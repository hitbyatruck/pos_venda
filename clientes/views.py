from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from .models import Cliente, Contacto
from equipamentos.models import EquipamentoFabricado
from assistencia.models import PedidoAssistencia  # PAT em vez de OrdemAssistencia
from equipamentos.models import EquipamentoCliente  # Add this line to import EquipamentoCliente
from notas.models import Nota
from core.utils import group_required
from .forms import ClienteForm, EquipamentoClienteForm  # Add this line to import ClienteForm and EquipamentoClienteForm

# LISTAGEM DE FUNÇÕES DE CLIENTES
@login_required
@group_required(['Administradores', 'Comerciais'])
def adicionar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, _('Cliente criado com sucesso.'))
            return redirect('clientes:detalhes_cliente', cliente_id=cliente.id)
    else:
        form = ClienteForm()
    
    # Adicione breadcrumbs
    breadcrumbs = [
        {'title': _('Clientes'), 'url': reverse('clientes:listar_clientes')},
        {'title': _('Adicionar Cliente'), 'url': None}
    ]
    
    return render(request, 'clientes/form_cliente.html', {
        'form': form,
        'titulo': _('Adicionar Cliente'),
        'breadcrumbs': breadcrumbs  # Adicione esta linha
    })

@login_required
@group_required(['Administradores', 'Técnicos', 'Comerciais'])
def listar_clientes(request):
    query = request.GET.get('q', '')
    clientes = Cliente.objects.all()
    
    if query:
        clientes = clientes.filter(
            Q(nome__icontains=query) | 
            Q(codigo__icontains=query) |
            Q(email__icontains=query) |
            Q(telefone__icontains=query)
        )
    
    clientes = clientes.order_by('nome')
    
    # Adicione breadcrumbs
    breadcrumbs = [
        {'title': _('Clientes'), 'url': None}
    ]
    
    return render(request, 'clientes/listar_clientes.html', {
        'clientes': clientes,
        'query': query,
        'breadcrumbs': breadcrumbs  # Adicione esta linha
    })

@login_required
@group_required(['Administradores', 'Técnicos', 'Comerciais'])
def detalhes_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    contactos = Contacto.objects.filter(cliente=cliente)
    equipamentos = EquipamentoFabricado.objects.filter(cliente=cliente)
    assistencias = PedidoAssistencia.objects.filter(cliente=cliente).order_by('-data_criacao')
    notas = Nota.objects.filter(cliente=cliente).order_by('-data_criacao')
    
    # Adicione breadcrumbs
    breadcrumbs = [
        {'title': _('Clientes'), 'url': reverse('clientes:listar_clientes')},
        {'title': cliente.nome, 'url': None}
    ]
    
    return render(request, 'clientes/detalhes_cliente.html', {
        'cliente': cliente,
        'contactos': contactos,
        'equipamentos': equipamentos,
        'assistencias': assistencias,
        'notas': notas,
        'breadcrumbs': breadcrumbs  # Adicione esta linha
    })

@login_required
@group_required(['Administradores', 'Comerciais'])
def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, _('Cliente atualizado com sucesso.'))
            return redirect('clientes:detalhes_cliente', cliente_id=cliente.id)
    else:
        form = ClienteForm(instance=cliente)
    
    # Adicione breadcrumbs
    breadcrumbs = [
        {'title': _('Clientes'), 'url': reverse('clientes:listar_clientes')},
        {'title': cliente.nome, 'url': reverse('clientes:detalhes_cliente', args=[cliente.id])},
        {'title': _('Editar'), 'url': None}
    ]
    
    return render(request, 'clientes/form_cliente.html', {
        'form': form,
        'cliente': cliente,
        'titulo': _('Editar Cliente'),
        'breadcrumbs': breadcrumbs  # Adicione esta linha
    })

@login_required
@group_required(['Administradores', 'Gestores de Clientes'])
@require_POST
def excluir_cliente(request, cliente_id):
    """Handle client deletion with dependency checking"""
    try:
        force = request.POST.get('force') == 'true'
        cliente = get_object_or_404(Cliente, id=cliente_id)
        
        # Check for dependencies
        has_equipamentos = hasattr(cliente, 'equipamentos') and cliente.equipamentos.exists()
        has_pats = hasattr(cliente, 'pedidos_assistencia') and cliente.pedidos_assistencia.exists()
        
        if not force and (has_equipamentos or has_pats):
            # Count dependencies
            num_equipamentos = cliente.equipamentos.count() if has_equipamentos else 0
            num_pats = cliente.pedidos_assistencia.count() if has_pats else 0
            
            # Create warning message
            warnings = []
            if num_equipamentos > 0:
                warnings.append(f"{num_equipamentos} equipamento(s)")
            if num_pats > 0:
                warnings.append(f"{num_pats} PAT(s)")
                
            message = f"Este cliente possui {' e '.join(warnings)} associados. A exclusão removerá todos estes registros. Deseja continuar?"
            
            logger.warning(f"Attempted to delete client {cliente_id} with dependencies")
            return JsonResponse({
                "success": False,
                "has_dependencies": True,
                "message": message
            })
        
        with transaction.atomic():
            # If force=true or no dependencies, proceed with deletion
            cliente.delete()
            logger.info(f"Client {cliente_id} deleted successfully")
            return JsonResponse({
                "success": True,
                "message": "Cliente excluído com sucesso."
            })
            
    except Exception as e:
        logger.error(f"Error deleting client {cliente_id}: {str(e)}", exc_info=True)
        return JsonResponse({
            "success": False,
            "message": f"Erro ao excluir cliente: {str(e)}"
        }, status=500)

@login_required
@group_required(['Administradores', 'Técnicos', 'Gestores de Clientes'])
def adicionar_equipamento_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    if request.method == "POST":
        form = EquipamentoClienteForm(request.POST)
        if form.is_valid():
            equipamento_cliente = form.save(commit=False)
            equipamento_cliente.cliente = cliente
            equipamento_cliente.save()
            return redirect('detalhes_cliente', cliente_id=cliente.id)  # Redireciona para detalhes do cliente
    else:
        form = EquipamentoClienteForm()
    
    return render(request, 'clientes/adicionar_equipamento_cliente.html', {'equipamento_form': form, 'cliente': cliente})

@login_required
@group_required(['Administradores', 'Técnicos', 'Gestores de Clientes', 'Visualizadores'])
def equipamentos_por_cliente(request):
    cliente_id = request.GET.get("cliente_id")
    if not cliente_id:
        return JsonResponse({"error": "cliente_id não fornecido."}, status=400)
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return JsonResponse({"error": "Cliente não encontrado."}, status=404)
    
    equipamentos = cliente.equipamentos.all()
    equipamentos_data = []
    for eq in equipamentos:
        equipamentos_data.append({
            "id": eq.id,
            "nome": eq.equipamento_fabricado.nome,
            "numero_serie": eq.numero_serie,
        })
    return JsonResponse({"equipamentos": equipamentos_data})

@login_required
@group_required(['Administradores', 'Técnicos'])
def desassociar_equipamento(request, equipamento_cliente_id):
    equipamento = get_object_or_404(EquipamentoCliente, id=equipamento_cliente_id)
    cliente_id = equipamento.cliente.id
    equipamento.delete()
    return redirect('detalhes_cliente', cliente_id=cliente_id)

@login_required
@group_required(['Administradores', 'Técnicos', 'Gestores de Clientes'])
@require_http_methods(["DELETE"])
def desassociar_equipamento_cliente(request, equipamento_id):
    try:
        equipamento_cliente = get_object_or_404(EquipamentoCliente, id=equipamento_id)
        pats = PedidoAssistencia.objects.filter(equipamento=equipamento_cliente)
        
        if pats.exists():
            if request.GET.get('force') == 'true':
                # Store PAT IDs before deletion
                pat_ids = list(pats.values_list('id', flat=True))
                # Delete PATs and then the association
                pats.delete()
                equipamento_cliente.delete()
                return JsonResponse({
                    'status': 'success',
                    'removedPats': pat_ids
                })
            else:
                return JsonResponse({
                    'status': 'warning',
                    'message': f'Este equipamento possui {pats.count()} PAT(s) associado(s). '
                              'A desassociação removerá todos os PATs relacionados. '
                              'Esta ação é irreversível.',
                    'requireForce': True
                })
        else:
            equipamento_cliente.delete()
            return JsonResponse({
                'status': 'success',
                'removedPats': []
            })
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)