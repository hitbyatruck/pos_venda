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

# Configure logger
logger = logging.getLogger(__name__)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST, require_http_methods
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from .models import Contacto, Empresa, Cliente, Setor, Individual, TipoContacto
from .forms import ContactoForm, EmpresaForm, EquipamentoClienteForm, SetorForm, IndividualForm, ContactoFormSet, ClienteForm, TipoContactoForm
from equipamentos.models import EquipamentoFabricado, EquipamentoCliente
from assistencia.models import PedidoAssistencia
from notas.models import Nota
from core.utils import group_required
from core.search import AdvancedSearch
from django.urls import reverse_lazy
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from .models import InteracaoCliente, TarefaCliente
from .utils import check_permissions


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
    clientes = Cliente.objects.all()
    
    # Get main contacts for email/telefone display
    for cliente in clientes:
        if not cliente.email or not cliente.telefone:
            # Look for primary email and phone contacts
            cliente_contacts = cliente.contactos.all()
            
            # Try to find a primary email
            if not cliente.email:
                email_contact = cliente_contacts.filter(
                    tipo__nome__icontains='email', 
                    principal=True
                ).first() or cliente_contacts.filter(
                    tipo__nome__icontains='email'
                ).first()
                
                if email_contact:
                    cliente.email = email_contact.valor
            
            # Try to find a primary phone
            if not cliente.telefone:
                phone_contact = cliente_contacts.filter(
                    Q(tipo__nome__icontains='telefone') | Q(tipo__nome__icontains='celular'),
                    principal=True
                ).first() or cliente_contacts.filter(
                    Q(tipo__nome__icontains='telefone') | Q(tipo__nome__icontains='celular')
                ).first()
                
                if phone_contact:
                    cliente.telefone = phone_contact.valor
    
    return render(request, 'clientes/listar_clientes.html', {'clientes': clientes, 'active_tab': 'all'})


@login_required
@group_required(['Administradores', 'Comerciais'])
def adicionar_cliente(request):
    # Exemplo: só redireciona para escolha de tipo
    return render(request, 'clientes/adicionar_cliente.html')


@login_required
@group_required(['Administradores', 'Comerciais'])
def adicionar_empresa(request):
    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES)
        formset = ContactoFormSet(request.POST, instance=form.instance)
        
        if form.is_valid() and formset.is_valid():
            empresa = form.save()
            formset.instance = empresa
            formset.save()
            messages.success(request, _('Empresa adicionada com sucesso!'))
            return redirect('clientes:detalhes_cliente', cliente_id=empresa.id)
    else:
        form = EmpresaForm()
        formset = ContactoFormSet(instance=form.instance)
    
    context = {
        'form': form,
        'formset': formset,
        'tipos_contacto': TipoContacto.objects.filter(ativo=True),
    }
    return render(request, 'clientes/form_empresa.html', context)


@login_required
@group_required(['Administradores', 'Comerciais'])
def adicionar_individual(request):
    if request.method == 'POST':
        form = IndividualForm(request.POST, request.FILES)
        formset = ContactoFormSet(request.POST, instance=form.instance)
        
        if form.is_valid() and formset.is_valid():
            individual = form.save()
            formset.instance = individual
            formset.save()
            messages.success(request, _('Cliente individual adicionado com sucesso!'))
            return redirect('clientes:detalhes_cliente', cliente_id=individual.id)
    else:
        form = IndividualForm()
        formset = ContactoFormSet(instance=form.instance)
    
    context = {
        'form': form,
        'formset': formset,
        'tipos_contacto': TipoContacto.objects.filter(ativo=True),
    }
    return render(request, 'clientes/form_individual.html', context)


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
    
    # Get specific instance based on client type
    if cliente.is_empresa:
        cliente_especifico = get_object_or_404(Empresa, id=cliente_id)
    else:
        cliente_especifico = get_object_or_404(Individual, id=cliente_id)
    
    if request.method == 'POST':
        if cliente.is_empresa:
            form = EmpresaForm(request.POST, request.FILES, instance=cliente_especifico)
        else:
            form = IndividualForm(request.POST, request.FILES, instance=cliente_especifico)
        
        formset = ContactoFormSet(request.POST, instance=cliente)
        
        if form.is_valid() and formset.is_valid():
            cliente = form.save()
            formset.save()
            messages.success(request, _('Cliente atualizado com sucesso!'))
            return redirect('clientes:detalhes_cliente', cliente_id=cliente.id)
    else:
        # Use the specific instance to ensure all fields are populated
        if cliente.is_empresa:
            form = EmpresaForm(instance=cliente_especifico)
        else:
            form = IndividualForm(instance=cliente_especifico)
        
        formset = ContactoFormSet(instance=cliente)
    
    template = 'clientes/form_empresa.html' if cliente.is_empresa else 'clientes/form_individual.html'
    context = {
        'form': form,
        'formset': formset,
        'cliente': cliente,
        'tipos_contacto': TipoContacto.objects.filter(ativo=True),
    }
    return render(request, template, context)


@login_required
@group_required(['Administradores', 'Comerciais'])
def excluir_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Exemplo simplificado
        cliente.delete()
        return JsonResponse({'success': True, 'redirect_url': reverse('clientes:listar_clientes')})
    if request.method == 'POST':
        cliente.delete()
        return redirect('clientes:listar_clientes')
    return render(request, 'clientes/excluir_cliente.html', {'cliente': cliente})


@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def listar_empresas(request):
    empresas = Empresa.objects.all()
    
    # Get main contacts for email/telefone display
    for cliente in empresas:
        if not cliente.email or not cliente.telefone:
            # Look for primary email and phone contacts
            cliente_contacts = cliente.contactos.all()
            
            # Try to find a primary email
            if not cliente.email:
                email_contact = cliente_contacts.filter(
                    tipo__nome__icontains='email', 
                    principal=True
                ).first() or cliente_contacts.filter(
                    tipo__nome__icontains='email'
                ).first()
                
                if email_contact:
                    cliente.email = email_contact.valor
            
            # Try to find a primary phone
            if not cliente.telefone:
                phone_contact = cliente_contacts.filter(
                    Q(tipo__nome__icontains='telefone') | Q(tipo__nome__icontains='celular'),
                    principal=True
                ).first() or cliente_contacts.filter(
                    Q(tipo__nome__icontains='telefone') | Q(tipo__nome__icontains='celular')
                ).first()
                
                if phone_contact:
                    cliente.telefone = phone_contact.valor
    
    return render(request, 'clientes/listar_clientes.html', {'clientes': empresas, 'active_tab': 'empresas'})


@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def detalhes_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    
    # Find associated individuals
    associated_individuals = Individual.objects.filter(empresa_associada=empresa)
    
    # Initialize contact variables
    primary_email = None
    first_email = None
    primary_phone = None
    first_phone = None
    
    # Get all contacts (company + individuals)
    all_contacts = list(empresa.contactos.all())
    individual_contacts = []
    
    # Add contacts from associated individuals
    for individual in associated_individuals:
        individual_contacts.extend(individual.contactos.all())
    
    # Process company contacts first for primary info section
    for contact in empresa.contactos.all():
        contact_type = contact.tipo.nome.lower()
        
        # Find email contacts
        if "email" in contact_type:
            if contact.principal and not primary_email:
                primary_email = contact
            elif not first_email:
                first_email = contact
        
        # Find phone contacts
        if "telefone" in contact_type or "celular" in contact_type:
            if contact.principal and not primary_phone:
                primary_phone = contact
            elif not first_phone:
                first_phone = contact
    
    # If no primary contacts found in company contacts, check individual contacts
    if not primary_email or not first_email or not primary_phone or not first_phone:
        for contact in individual_contacts:
            contact_type = contact.tipo.nome.lower()
            
            # Find email contacts from individuals
            if "email" in contact_type:
                if contact.principal and not primary_email:
                    primary_email = contact
                elif not first_email:
                    first_email = contact
            
            # Find phone contacts from individuals
            if "telefone" in contact_type or "celular" in contact_type:
                if contact.principal and not primary_phone:
                    primary_phone = contact
                elif not first_phone:
                    first_phone = contact
    
    return render(request, 'clientes/detalhes_empresa.html', {
        'cliente': empresa,
        'associated_individuals': associated_individuals,
        'primary_email': primary_email,
        'first_email': first_email,
        'primary_phone': primary_phone,
        'first_phone': first_phone,
        'all_contacts': all_contacts,
        'individual_contacts': individual_contacts,
        'combined_contacts': all_contacts + individual_contacts,
    })


@login_required
@group_required(['Administradores', 'Comerciais'])
def editar_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            form.save()
            return redirect('clientes:detalhes_empresa', empresa_id=empresa.id)
    else:
        form = EmpresaForm(instance=empresa)
    return render(request, 'clientes/form_empresa.html', {'form': form, 'cliente': empresa})


@login_required
@group_required(['Administradores', 'Comerciais'])
def excluir_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    if request.method == 'POST':
        empresa.delete()
        return redirect('clientes:listar_empresas')
    return render(request, 'clientes/excluir_cliente.html', {'cliente': empresa})


@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def listar_individuais(request):
    individuais = Individual.objects.all()
    
    # Get main contacts for email/telefone display
    for cliente in individuais:
        if not cliente.email or not cliente.telefone:
            # Look for primary email and phone contacts
            cliente_contacts = cliente.contactos.all()
            
            # Try to find a primary email
            if not cliente.email:
                email_contact = cliente_contacts.filter(
                    tipo__nome__icontains='email', 
                    principal=True
                ).first() or cliente_contacts.filter(
                    tipo__nome__icontains='email'
                ).first()
                
                if email_contact:
                    cliente.email = email_contact.valor
            
            # Try to find a primary phone
            if not cliente.telefone:
                phone_contact = cliente_contacts.filter(
                    Q(tipo__nome__icontains='telefone') | Q(tipo__nome__icontains='celular'),
                    principal=True
                ).first() or cliente_contacts.filter(
                    Q(tipo__nome__icontains='telefone') | Q(tipo__nome__icontains='celular')
                ).first()
                
                if phone_contact:
                    cliente.telefone = phone_contact.valor
    
    return render(request, 'clientes/listar_clientes.html', {'clientes': individuais, 'active_tab': 'individuais'})


@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def listar_setores(request):
    setores = Setor.objects.all()
    return render(request, 'clientes/listar_setores.html', {'setores': setores, 'active_tab': 'setores'})


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
    if request.is_ajax():
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
        'search_query': search_query
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
    if request.method != 'POST' or request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'success': False, 'message': _('Método não permitido')}, status=405)
    
    try:
        data = json.loads(request.body)
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
def busca_unificada(request):
    return HttpResponse("TODO: Implement busca_unificada")


@login_required
def index(request):
    return redirect('clientes:dashboard')