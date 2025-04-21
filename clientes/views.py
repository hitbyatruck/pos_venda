from django.shortcuts import render, get_object_or_404, redirect
import logging
from django.db import transaction
from django.db.models import Q, QuerySet
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse, JsonResponse  # Keep as is for proper imports
import xlsxwriter
from io import BytesIO
import datetime
import csv
import json
import unicodedata
from typing import Dict, Any, List, Optional, Union, cast, TypeVar, Type, TYPE_CHECKING

# Configure logger
logger = logging.getLogger(__name__)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST, require_http_methods
from .models import Cliente, Contacto, TipoContacto, Setor, CategoriaCliente
from .forms import ClienteForm, ContactoForm, SetorForm, TipoContactoForm
from equipamentos.models import EquipamentoFabricado, EquipamentoCliente
from assistencia.models import PedidoAssistencia
from notas.models import Nota
from core.utils import group_required
from core.search import AdvancedSearch, normalize_text
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from .utils import check_permissions
from equipamentos.forms import EquipamentoClienteForm
from django.forms.models import inlineformset_factory
from django.core.exceptions import FieldError

T = TypeVar('T')  # Define a generic type variable

# Helper function to safely add dynamic attributes to models
def add_dynamic_attribute(obj: Any, attr_name: str, value: Any) -> None:
    """Safely add a dynamic attribute to an object for type checking."""
    setattr(obj, attr_name, value)

# Add missing helper functions for type checking
def with_contactos(obj: Any) -> Any:
    """Mark an object as having contactos attribute for type checking."""
    return obj  # Just returns the object, used for type hints

def with_id(obj: Any) -> Any:
    """Mark an object as having id attribute for type checking."""
    return obj  # Just returns the object, used for type hints

@login_required
@check_permissions
def dashboard(request):
    hoje = timezone.now()
    ha_90_dias = hoje - timedelta(days=90)
    total_clientes = Cliente.objects.count()
    valor_contratos_ativos = 4000.00  # Exemplo
    total_contratos_ativos = 10       # Exemplo
    taxa_engagement = 75              # Exemplo

    context = {
        'valor_contratos_ativos': valor_contratos_ativos,
        'total_contratos_ativos': total_contratos_ativos,
        'taxa_engagement': taxa_engagement,
        'total_clientes': total_clientes,
        'active_tab': 'dashboard',
    }
    return render(request, 'clientes/dashboard_clientes.html', context)


@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def exportar_clientes(request):
    # Fix HttpResponse content type by using bytes
    return HttpResponse(b"TODO: Implement exportar_clientes")


@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def importar_clientes(request):
    # Fix HttpResponse content type by using bytes
    return HttpResponse(b"TODO: Implement importar_clientes")


@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def listar_clientes(request):
    # Get filters from request
    search_query = request.GET.get('q', '')
    setor_id = request.GET.get('setor', '')
    order_by = request.GET.get('orderby', 'nome')

    # Initialize results dictionary to hold categorized results
    search_results: Dict[str, Any] = {
        'clientes': [],
        'equipamentos': [],
        'assistencias': [],
        'notas': [],
        'contactos': []
    }

    total_count = 0

    # Apply filters
    try:
        # Get base queryset - all clients with prefetched contacts to improve performance
        clientes = Cliente.objects.prefetch_related('contactos', 'contactos__tipo').all()

        if search_query:
            # Log search terms for debugging
            logger.info(f"Searching for: '{search_query}', normalized: '{normalize_text(search_query)}'")

            # Use our enhanced search utility with the aliased name
            all_results, total_count = AdvancedSearch.global_search(search_query)

            # Directly update search_results with all_results
            for key, value in all_results.items():
                search_results[key] = value

            # Get contacts specifically for this query
            from clientes.models import Contacto
            from django.db.models import Q

            normalized_query = normalize_text(search_query)
            matching_contacts = Contacto.objects.filter(
                # Use Q() | Q() syntax instead of direct | operator
                Q(valor__icontains=normalized_query) |
                Q(nome_contacto__icontains=normalized_query) |
                Q(cargo__icontains=normalized_query)  # type: ignore
            )

            # Update the contacts in search_results
            search_results['contactos'] = matching_contacts

            # Update the clients queryset to use the search results
            clientes = search_results['clientes']

            # If we're doing a search, use the unified search template
            if search_query:
                context = {
                    'search_query': search_query,
                    'results': search_results,
                    'total_count': total_count,
                    'normalized_query': normalize_text(search_query),
                }
                return render(request, 'search/results.html', context)

        # Apply setor filter if provided
        if setor_id:
            try:
                clientes = clientes.filter(setor_id=setor_id)
                search_results['clientes'] = clientes
            except FieldError:
                logger.warning("Setor field does not exist yet. Migrations may need to be applied.")

        # Apply ordering
        clientes = clientes.order_by(order_by)
        search_results['clientes'] = clientes

    except Exception as e:
        logger.error(f"Error querying clients: {str(e)}")
        clientes = []
        messages.error(request, f"Erro ao carregar clientes: {str(e)}")

    # Pre-process contacts for efficiency - find primary emails and phones
    for cliente in clientes:
        cliente_with_contactos = with_contactos(cliente)  # Use type adapter
        # Store contact data in a dict for later access
        contact_data: Dict[str, Any] = {
            'primary_email': None,
            'primary_phone': None,
            'first_email': None,
            'first_phone': None
        }

        # First look for principal contacts
        for contact in cliente_with_contactos.contactos.all():  # type: ignore
            if not contact.tipo:
                continue

            if contact.tipo.nome == "Email" and contact.principal and not contact_data['primary_email']:
                contact_data['primary_email'] = contact
            elif contact.tipo.nome in ["Telefone", "Móvel", "Telemóvel", "Celular"] and contact.principal and not contact_data['primary_phone']:
                contact_data['primary_phone'] = contact

        # Then look for first contacts if no principal was found
        for contact in cliente_with_contactos.contactos.all():  # type: ignore
            if not contact.tipo:
                continue

            if contact.tipo.nome == "Email" and not contact_data['first_email']:
                contact_data['first_email'] = contact
            elif contact.tipo.nome in ["Telefone", "Móvel", "Telemóvel", "Celular"] and not contact_data['first_phone']:
                contact_data['first_phone'] = contact

        # Use helper to add attributes safely
        if not hasattr(cliente, '_contacts_processed'):
            # Store a flag to prevent processing multiple times
            setattr(cliente, '_contacts_processed', True)
            # Store contact references as attributes
            setattr(cliente, 'primary_email', contact_data['primary_email'])
            setattr(cliente, 'primary_phone', contact_data['primary_phone'])
            setattr(cliente, 'first_email', contact_data['first_email'])
            setattr(cliente, 'first_phone', contact_data['first_phone'])

    # Pagination
    paginator = Paginator(clientes, 20)
    page = request.GET.get('pagina', 1)

    try:
        clientes_paginated = paginator.page(page)
    except PageNotAnInteger:
        clientes_paginated = paginator.page(1)
    except EmptyPage:
        clientes_paginated = paginator.page(paginator.num_pages)

    # Get setores and categories for filters
    try:
        setores = Setor.objects.all()
    except:
        setores = []

    try:
        categorias = CategoriaCliente.objects.all()
    except:
        categorias = []

    context = {
        'clientes': clientes_paginated,
        'page_obj': clientes_paginated,
        'paginator': paginator,
        'search_query': search_query,
        'setor_id': setor_id,
        'order_by': order_by,
        'setores': setores,
        'categorias': categorias,
        'total_clientes': paginator.count if clientes else 0,
        'search_results': search_results,
        'is_search_result': bool(search_query),
        'active_tab': 'all',
        'normalized_query': normalize_text(search_query) if search_query else '',
        'total_count': total_count
    }
    return render(request, 'clientes/listar_clientes.html', context)

@login_required
@group_required(['Administradores', 'Comerciais'])
def adicionar_cliente(request):
    """View for adding a new client"""
    # Create a formset for contacts
    ContactoFormSet = inlineformset_factory(
        Cliente,
        Contacto,
        form=ContactoForm,
        extra=1,
        can_delete=True
    )

    if request.method == 'POST':
        form = ClienteForm(request.POST, request.FILES)
        formset = ContactoFormSet(request.POST, prefix='contactos')

        if form.is_valid() and formset.is_valid():
            # Save the client first
            cliente = form.save()

            # Then save the contacts with the client reference
            contactos = formset.save(commit=False)
            for contacto in contactos:
                contacto.cliente = cliente
                contacto.save()

            # Handle deleted contacts:
            for obj in formset.deleted_objects:
                obj.delete()

            messages.success(request, _("Cliente adicionado com sucesso!"))
            return redirect('clientes:detalhes_cliente', cliente_id=cliente.id)
    else:
        form = ClienteForm()
        formset = ContactoFormSet(prefix='contactos')

    context = {
        'form': form,
        'formset': formset,
        'title': _('Adicionar Cliente'),
        'tipos_contacto': TipoContacto.objects.filter(ativo=True),
    }
    return render(request, 'clientes/criar_cliente.html', context)

@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def detalhes_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    cliente_with_contactos = with_contactos(cliente)  # Use type adapter
    # Add these lines to find emails
    primary_email = None
    first_email = None

    for contact in cliente_with_contactos.contactos.all():  # type: ignore
        # Add null check before accessing tipo.nome
        if contact.tipo is not None and contact.tipo.nome == "Email":
            if contact.principal and not primary_email:
                primary_email = contact
            if not first_email:
                first_email = contact

    return render(request, 'clientes/detalhes_cliente.html', {
        'cliente': cliente,
        'primary_email': primary_email,
        'first_email': first_email,
    })

@login_required
@group_required(['Administradores', 'Comerciais'])
def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    # Create a formset for contacts
    ContactoFormSet = inlineformset_factory(
        Cliente,
        Contacto,
        form=ContactoForm,
        extra=1,
        can_delete=True
    )

    if request.method == 'POST':
        form = ClienteForm(request.POST, request.FILES, instance=cliente)
        formset = ContactoFormSet(request.POST, request.FILES, prefix='contactos', instance=cliente)

        if form.is_valid() and formset.is_valid():
            # Save the client first
            cliente = form.save()

            # Then save the contacts with the client reference
            contactos = formset.save(commit=False)
            for contacto in contactos:
                contacto.cliente = cliente
                contacto.save()

            # Handle deleted contacts
            for obj in formset.deleted_objects:
                obj.delete()

            messages.success(request, _("Cliente atualizado com sucesso!"))
            return redirect('clientes:detalhes_cliente', cliente_id=cliente.id)
        else:
            # If there are errors, log them for debugging
            if not form.is_valid():
                logger.error(f"Form errors: {form.errors}")
            if not formset.is_valid():
                logger.error(f"Formset errors: {formset.errors}")
            messages.error(request, _("Erro ao atualizar cliente. Verifique os campos destacados."))
    else:
        form = ClienteForm(instance=cliente)
        formset = ContactoFormSet(prefix='contactos', instance=cliente)

    context = {
        'form': form,
        'formset': formset,
        'cliente': cliente,
        'title': _('Editar Cliente'),
        'is_edit': True,
        'tipos_contacto': TipoContacto.objects.filter(ativo=True),
    }
    return render(request, 'clientes/criar_cliente.html', context)

@login_required
@group_required(['Administradores', 'Comerciais'])
def excluir_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cliente.delete()
        return JsonResponse({'success': True, 'redirect_url': reverse('clientes:listar_clientes')})
    if request.method == 'POST':
        cliente.delete()
        return redirect('clientes:listar_clientes')
    return render(request, 'clientes/excluir_cliente.html', {'cliente': cliente})

@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def listar_setores(request):
    setores = Setor.objects.all()
    return render(request, 'clientes/listar_setores.html', {'setores': setores, 'active_tab': 'configuracoes'})

@login_required
@group_required(['Administradores', 'Comerciais'])
def adicionar_setor(request):
    if request.method == 'POST':
        form = SetorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('clientes:listar_setores')
    else:
        form = SetorForm()
    return render(request, 'clientes/form_setor.html', {'form': form})

@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def detalhes_setor(request, setor_id):
    setor = get_object_or_404(Setor, id=setor_id)
    return render(request, 'clientes/detalhes_setor.html', {'setor': setor})

@login_required
@group_required(['Administradores', 'Comerciais'])
def editar_setor(request, setor_id):
    setor = get_object_or_404(Setor, id=setor_id)
    setor_with_id = with_id(setor)  # Use type adapter
    if request.method == 'POST':
        form = SetorForm(request.POST, instance=setor)
        if form.is_valid():
            form.save()
            return redirect('clientes:detalhes_setor', setor_id=setor_with_id.id)  # type: ignore
    else:
        form = SetorForm(instance=setor)
    return render(request, 'clientes/form_setor.html', {'form': form, 'setor': setor})

@login_required
@group_required(['Administradores', 'Comerciais'])
def excluir_setor(request, setor_id):
    setor = get_object_or_404(Setor, id=setor_id)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        setor.delete()
        return JsonResponse({'success': True})
    if request.method == 'POST':
        setor.delete()
        return redirect('clientes:listar_setores')
    return render(request, 'clientes/listar_setores.html')

@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def listar_tipos_contacto(request):
    tipos_contacto = TipoContacto.objects.all()
    total_tipos_contacto = tipos_contacto.count()

    # Handle search query if present
    search_query = request.GET.get('q', '')
    if search_query:
        tipos_contacto = tipos_contacto.filter(nome__icontains=search_query)

    # Pagination
    paginator = Paginator(tipos_contacto, 10)  # Show 10 tipos per page
    page = request.GET.get('pagina', 1)

    try:
        tipos_contacto = paginator.page(page)
    except PageNotAnInteger:
        tipos_contacto = paginator.page(1)
    except EmptyPage:
        tipos_contacto = paginator.page(paginator.num_pages)

    context = {
        'tipos_contacto': tipos_contacto,
        'total_tipos_contacto': total_tipos_contacto,
        'search_query': search_query,
        'active_tab': 'configuracoes'
    }

    return render(request, 'clientes/listar_tipos_contacto.html', context)

@login_required
@group_required(['Administradores', 'Comerciais'])
def adicionar_tipo_contacto(request):
    if request.method == 'POST':
        form = TipoContactoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('clientes:listar_tipos_contacto')
    else:
        form = TipoContactoForm()
    return render(request, 'clientes/form_tipo_contacto.html', {'form': form, 'is_new': True})

@login_required
@group_required(['Administradores', 'Comerciais'])
def editar_tipo_contacto(request, tipo_id):
    tipo = get_object_or_404(TipoContacto, id=tipo_id)
    if request.method == 'POST':
        form = TipoContactoForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            return redirect('clientes:listar_tipos_contacto')
    else:
        form = TipoContactoForm(instance=tipo)
    return render(request, 'clientes/form_tipo_contacto.html', {'form': form, 'tipo_contacto': tipo, 'is_new': False})

@login_required
@group_required(['Administradores', 'Comerciais'])
def excluir_tipo_contacto(request, tipo_id):
    tipo = get_object_or_404(TipoContacto, id=tipo_id)
    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        # Check if there are related contacts
        contactos_relacionados = Contacto.objects.filter(tipo=tipo).count()
        force_delete = request.POST.get('force', 'false').lower() == 'true'

        if contactos_relacionados > 0 and not force_delete:
            # If there are related contacts and force is not set, return warning
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'has_dependencies': True,
                    'message': _('Este tipo possui {} contactos associados. Tem certeza que deseja excluí-lo?').format(contactos_relacionados)
                })

        try:
            tipo.delete()
            if is_ajax:
                return JsonResponse({'success': True})
            messages.success(request, _('Tipo de contacto excluído com sucesso!'))
            return redirect('clientes:listar_tipos_contacto')
        except Exception as e:
            logger.error(f"Error deleting contact type: {e}")
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': _('Erro ao excluir tipo de contacto: {}').format(str(e))
                })
            messages.error(request, _('Erro ao excluir tipo de contacto: {}').format(str(e)))
            return redirect('clientes:listar_tipos_contacto')

    # Not a POST request
    if is_ajax:
        return JsonResponse({'success': False, 'message': _('Método não permitido')}, status=405)
    return render(request, 'clientes/excluir_tipo_contacto.html', {'tipo': tipo})

@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def detalhes_tipo_contacto(request, tipo_id):
    tipo = get_object_or_404(TipoContacto, id=tipo_id)
    contactos = Contacto.objects.filter(tipo=tipo)

    context = {
        'tipo': tipo,
        'contactos': contactos,
        'total_contactos': contactos.count(),
    }

    return render(request, 'clientes/detalhes_tipo_contacto.html', context)

@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def cliente_contactos(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    contactos = Contacto.objects.filter(cliente=cliente)

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Handle AJAX form submission for adding/editing contacts
        contacto_id = request.POST.get('contacto_id')
        if contacto_id and contacto_id.isdigit():
            # Editing existing contact
            contacto = get_object_or_404(Contacto, id=contacto_id, cliente=cliente)
            form = ContactoForm(request.POST, instance=contacto)
        else:
            # Adding new contact
            form = ContactoForm(request.POST)

        if form.is_valid():
            contacto = form.save(commit=False)
            contacto.cliente = cliente
            contacto.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})

    # Get all tipos_contacto for the form
    tipos_contacto = TipoContacto.objects.filter(ativo=True)

    context = {
        'cliente': cliente,
        'contactos': contactos,
        'tipos_contacto': tipos_contacto,
    }
    return render(request, 'clientes/cliente_contactos.html', context)

@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def cliente_equipamentos(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    return render(request, 'clientes/cliente_equipamentos.html', {'cliente': cliente})

@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def cliente_assistencias(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    return render(request, 'clientes/cliente_assistencias.html', {'cliente': cliente})

@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def cliente_notas(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    return render(request, 'clientes/cliente_notas.html', {'cliente': cliente})

@login_required
@group_required(['Administradores', 'Comerciais'])
def adicionar_equipamento_cliente(request, cliente_id: int):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == 'POST':
        form = EquipamentoClienteForm(request.POST)
        if form.is_valid():
            equipamento = form.save(commit=False)
            equipamento.cliente = cliente
            equipamento.save()
            return redirect('clientes:cliente_equipamentos', cliente_id=cliente_id)
    else:
        form = EquipamentoClienteForm(initial={'cliente': cliente_id})
    return render(request, 'clientes/cliente_equipamentos.html', {'form': form, 'cliente': cliente})

@login_required
@group_required(['Administradores', 'Comerciais'])
def desassociar_equipamento(request, equipamento_cliente_id):
    eq = get_object_or_404(EquipamentoCliente, id=equipamento_cliente_id)
    cliente_id = eq.cliente.id
    eq.delete()
    return redirect('clientes:cliente_equipamentos', cliente_id=cliente_id)

@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def equipamentos_por_cliente(request):
    # Fix HttpResponse content type by using bytes
    return HttpResponse(b"TODO: Implement equipamentos_por_cliente")

@login_required
@group_required(['Administradores', 'Comerciais'])
def excluir_contacto(request):
    """Delete a contact via AJAX request"""
    if request.method != 'POST' or not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'message': _('Método não permitido')}, status=405)

    try:
        # Try to get data from JSON body or from POST data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            # If not valid JSON, use POST data
            data = request.POST

        contacto_id = data.get('contacto_id')
        cliente_id = data.get('cliente_id')

        if not contacto_id or not cliente_id:
            return JsonResponse({
                'success': False,
                'message': _('Dados incompletos')
            }, status=400)

        cliente = get_object_or_404(Cliente, id=cliente_id)
        contacto = get_object_or_404(Contacto, id=contacto_id, cliente=cliente)
        contacto.delete()
        return JsonResponse({'success': True})
    except Contacto.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': _('Contacto não encontrado')
        }, status=404)
    except Exception as e:
        logger.error(f"Error deleting contact: {e}")
        return JsonResponse({
            'success': False,
            'message': _('Erro ao excluir contacto: {}').format(str(e))
        }, status=500)

@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def busca_unificada(request):
    """
    Redirect to the main search functionality
    """
    search_query = request.GET.get('q', '')
    if (search_query):
        return redirect(f'/search/?q={search_query}')
    return redirect('search_global')

@login_required
def index(request):
    return redirect('clientes:dashboard')

@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def listar_contactos(request):
    """View to list all contacts across all clients in a contact book format"""

    # Get filters from request
    search_query = request.GET.get('q', '')
    tipo_id = request.GET.get('tipo', '')
    order_by = request.GET.get('orderby', 'nome_contacto')

    # Get base queryset - all contacts with their related client and contact type
    contactos = Contacto.objects.select_related('cliente', 'tipo').all()

    # Apply search filter provided - use separate filters instead of Q objects
    if search_query:
        normalized_query = normalize_text(search_query)

        # Create a separate queryset for each filter condition and then combine results
        # This avoids the problematic Q() | operator entirely
        nome_results = Contacto.objects.filter(nome_contacto__icontains=search_query)
        valor_results = Contacto.objects.filter(valor__icontains=search_query)
        cargo_results = Contacto.objects.filter(cargo__icontains=search_query)
        cliente_results = Contacto.objects.filter(cliente__nome__icontains=search_query)

        # Combine the querysets using distinct() to remove duplicates
        contactos = nome_results.union(valor_results, cargo_results, cliente_results)

    # Apply contact type filter if provided
    if tipo_id:
        contactos = contactos.filter(tipo_id=tipo_id)

    # Apply ordering
    if order_by.startswith('-'):
        contactos = contactos.order_by(order_by)
    else:
        contactos = contactos.order_by(order_by)

    # Get all contact types for the filter dropdown
    tipos_contacto = TipoContacto.objects.filter(ativo=True)

    # Pagination
    paginator = Paginator(contactos, 20)
    page = request.GET.get('pagina', 1)

    try:
        contactos_paginated = paginator.page(page)
    except PageNotAnInteger:
        contactos_paginated = paginator.page(1)
    except EmptyPage:
        contactos_paginated = paginator.page(paginator.num_pages)

    # Get selected contact type name if tipo_id is provided
    tipo_nome = None
    if tipo_id:
        try:
            tipo = TipoContacto.objects.get(id=tipo_id)
            tipo_nome = tipo.nome
        except TipoContacto.DoesNotExist:
            pass

    # Group contacts by name - safely convert for manipulation
    contactos_list = list(contactos_paginated.object_list)
    # Process the list if needed
    # Then update context to use this list instead of modifying the paginator directly

    context = {
        'contactos': contactos_paginated,
        'contactos_list': contactos_list,  # Add the processed list to context
        'page_obj': contactos_paginated,
        'paginator': paginator,
        'search_query': search_query,
        'tipo_id': tipo_id,
        'tipo_nome': tipo_nome,  # Add this to context
        'tipos_contacto': tipos_contacto,
        'order_by': order_by,
        'total_contactos': paginator.count if contactos else 0,
        'active_tab': 'contactos',  # Highlight the Contactos tab in the navigation
    }

    return render(request, 'clientes/listar_contactos.html', context)

if TYPE_CHECKING:
    # These type hints are only used by the type checker and not during runtime

    # Django model manager type
    class DjangoManager:
        def all(self): ...
        def filter(self, *args, **kwargs): ...
        def get(self, *args, **kwargs): ...
        def count(self): ...
        def create(self, **kwargs): ...
        def update(self, **kwargs): ...
        def delete(self): ...

    # Add Django model type definitions
    class DjangoModelType:
        objects: DjangoManager
        DoesNotExist: Type[Exception]

    # Apply Django type to our models
    Cliente.__class__ = DjangoModelType  # type: ignore
    Contacto.__class__ = DjangoModelType  # type: ignore
    TipoContacto.__class__ = DjangoModelType  # type: ignore
    Setor.__class__ = DjangoModelType  # type: ignore
    CategoriaCliente.__class__ = DjangoModelType  # type: ignore
    EquipamentoCliente.__class__ = DjangoModelType  # type: ignore

# Add type ignore directives to the most common pattern
def _suppress_django_warnings() -> None:
    """This function is never called, it just contains type-ignore directives."""
    Cliente.objects  # type: ignore
    Contacto.objects  # type: ignore
    TipoContacto.objects  # type: ignore
    Setor.objects  # type: ignore
    CategoriaCliente.objects  # type: ignore
    Contacto.DoesNotExist  # type: ignore
    TipoContacto.DoesNotExist  # type: ignore
    # Add more as needed