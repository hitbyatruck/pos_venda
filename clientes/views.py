from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
import logging
from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse
import xlsxwriter
from io import BytesIO
import datetime
import csv
import json
import unicodedata

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

def normalize_text(text):
    """
    Normalize text by removing accents and converting to lowercase
    """
    if not text:
        return ""
    # Normalize unicode characters (remove accents)
    normalized = unicodedata.normalize('NFKD', str(text))
    normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])
    # Convert to lowercase and strip extra spaces
    return normalized.lower().strip()

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
    return HttpResponse("TODO: Implement exportar_clientes")


@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def importar_clientes(request):
    return HttpResponse("TODO: Implement importar_clientes")


@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def listar_clientes(request):
    # Get filters from request
    search_query = request.GET.get('q', '')
    setor_id = request.GET.get('setor', '')
    order_by = request.GET.get('orderby', 'nome')
    
    # Initialize results dictionary to hold categorized results
    search_results = {
        'clientes': [],
        'equipamentos': [],
        'assistencias': [],
        'notas': [],
        'contactos': []
    }
    
    total_count = 0
    
    # Apply filters
    try:
        # Get base queryset - all clients
        clientes = Cliente.objects.all()
        
        if search_query:
            # Log search terms for debugging
            logger.info(f"Searching for: '{search_query}', normalized: '{normalize_text(search_query)}'")
            
            # Use our enhanced search utility
            all_results, total_count = AdvancedSearch.global_search(search_query)
            
            # Directly update search_results with all_results
            for key, value in all_results.items():
                search_results[key] = value
                
            # Get contacts specifically for this query
            from clientes.models import Contacto
            from django.db.models import Q
            
            normalized_query = normalize_text(search_query)
            matching_contacts = Contacto.objects.filter(
                Q(valor__icontains=normalized_query) |
                Q(nome_contacto__icontains=normalized_query) |
                Q(cargo__icontains=normalized_query)
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
            
            # Handle deleted contacts
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
    
    # Add these lines to find emails
    primary_email = None
    first_email = None
    
    for contact in cliente.contactos.all():
        if contact.tipo.nome == "Email":
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
    if request.method == 'POST':
        form = SetorForm(request.POST, instance=setor)
        if form.is_valid():
            form.save()
            return redirect('clientes:detalhes_setor', setor_id=setor.id)
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
def adicionar_equipamento_cliente(request, cliente_id):
    if request.method == 'POST':
        form = EquipamentoClienteForm(request.POST, cliente_id=cliente_id)    
        if form.is_valid():
            form.save()
            return redirect('clientes:cliente_equipamentos', cliente_id=cliente_id)
    else:
        form = EquipamentoClienteForm(cliente_id=cliente_id)
    return render(request, 'clientes/cliente_equipamentos.html', {'form': form})


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
    return HttpResponse("TODO: Implement equipamentos_por_cliente")


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
def detalhes_empresa(request, empresa_id):
    cliente = get_object_or_404(Cliente, id=empresa_id, tipo='empresa')
    
    # Find primary/first email and phone
    primary_email = None
    first_email = None
    
    contacts_count = cliente.contactos.count()
    associated_individuals = Cliente.objects.filter(empresa_associada=cliente, tipo='individual')
    
    # Get all contacts (both from company and from associated individuals)
    all_contacts = cliente.contactos.all()
    individual_contacts = []
    for individual in associated_individuals:
        individual_contacts.extend(individual.contactos.all())
    
    combined_contacts = (contacts_count > 0) or (len(individual_contacts) > 0)
    
    # Find emails
    for contact in all_contacts:
        if contact.tipo.nome == "Email":
            if contact.principal and not primary_email:
                primary_email = contact
            if not first_email:
                first_email = contact
    
    return render(request, 'clientes/detalhes_empresa.html', {
        'cliente': cliente,
        'primary_email': primary_email,
        'first_email': first_email,
        'contacts_count': contacts_count,
        'associated_individuals': associated_individuals,
        'all_contacts': all_contacts,
        'individual_contacts': individual_contacts,
        'combined_contacts': combined_contacts,
    })