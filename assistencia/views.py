from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext as _
from django.db import transaction
from django.db.models import Q
from django.views.decorators.http import require_POST, require_http_methods
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.utils import timezone
from datetime import datetime
import logging
import traceback
import json

from .models import PedidoAssistencia, ItemPAT, HistoricoPAT
from .forms import PatForm, PatItemFormSet, EditItemPatFormSet
from clientes.models import Cliente
from equipamentos.models import EquipamentoCliente
from core.utils import group_required
from core.search import AdvancedSearch

# Configure logger
logger = logging.getLogger(__name__)

@login_required
@group_required(['Administradores', 'Técnicos'])
def criar_pat(request):
    """Cria um novo Pedido de Assistência Técnica (PAT)"""
    initial_data = {}

    # Get initial values from query params
    cliente_id = request.GET.get('cliente')
    equipamento_id = request.GET.get('equipamento')

    if cliente_id:
        try:
            cliente = Cliente.objects.get(id=cliente_id)
            initial_data['cliente'] = cliente
        except Cliente.DoesNotExist:
            pass

    if equipamento_id:
        try:
            equipamento = EquipamentoCliente.objects.get(id=equipamento_id)
            initial_data['equipamento'] = equipamento
        except EquipamentoCliente.DoesNotExist:
            pass

    if request.method == 'POST':
        # Print form data for debugging
        print("POST data:", request.POST)

        form = PatForm(request.POST, initial=initial_data)
        # Use 'items' prefix consistently
        itemformset = PatItemFormSet(request.POST, prefix='items')

        # Print form and formset validation status
        if not form.is_valid():
            print("Form errors:", form.errors)
        if not itemformset.is_valid():
            print("Formset errors:", itemformset.errors)

        if form.is_valid() and itemformset.is_valid():
            try:
                with transaction.atomic():
                    pat = form.save()

                    # Set PAT reference for all items and save them
                    instances = itemformset.save(commit=False)
                    for instance in instances:
                        instance.pat = pat
                        instance.save()

                    # Make sure to handle formset's deleted objects
                    for obj in itemformset.deleted_objects:
                        obj.delete()

                    messages.success(request, _('PAT criada com sucesso!'))
                    return redirect('assistencia:detalhes_pat', pat_id=pat.id)
            except Exception as e:
                # Log the exception for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error creating PAT: {str(e)}")
                messages.error(request, _('Erro ao criar PAT: {}').format(str(e)))
        else:
            # Add more informative error messages
            if not form.is_valid():
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")

            if not itemformset.is_valid():
                for i, form_errors in enumerate(itemformset.errors):
                    for field, errors in form_errors.items():
                        for error in errors:
                            messages.error(request, f"Item {i+1}, {field}: {error}")

            messages.error(request, _('Por favor corrija os erros no formulário.'))
    else:
        form = PatForm(initial=initial_data)
        itemformset = PatItemFormSet(prefix='items')

    # Always pass equipment_id to the template if it exists
    context = {
        'form': form,
        'itemformset': itemformset,  # Make sure to use 'itemformset' consistently
        'equipment_id': equipamento_id,
        'cliente_id': cliente_id
    }

    return render(request, 'assistencia/criar_pat.html', context)

@login_required
@group_required(['Administradores', 'Técnicos'])
def editar_pat(request, pat_id):
    """Edita um Pedido de Assistência Técnica (PAT)"""
    pat = get_object_or_404(PedidoAssistencia, id=pat_id)

    if request.method == 'POST':
        form = PatForm(request.POST, instance=pat)
        # Use prefix to ensure we capture the right form fields
        itemformset = PatItemFormSet(request.POST, instance=pat, prefix='items')

        if form.is_valid() and itemformset.is_valid():
            try:
                with transaction.atomic():
                    pat = form.save()

                    # Save the formset without commit first
                    instances = itemformset.save(commit=False)

                    # Process all form instances
                    for instance in instances:
                        instance.pat = pat
                        instance.save()

                    # Process any deleted forms
                    for obj in itemformset.deleted_objects:
                        obj.delete()

                    messages.success(request, _('PAT atualizada com sucesso!'))
                    return redirect('assistencia:detalhes_pat', pat_id=pat.id)
            except Exception as e:
                # Log the exception
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error updating PAT: {str(e)}")
                messages.error(request, _('Erro ao atualizar PAT: {}').format(str(e)))
        else:
            # Debug: Print form errors
            print("Form errors:", form.errors)
            print("Formset errors:", itemformset.errors)

            for form_errors in itemformset.errors:
                for field, error in form_errors.items():
                    messages.error(request, f"{field}: {error}")

            messages.error(request, _('Por favor corrija os erros no formulário.'))
    else:
        form = PatForm(instance=pat)
        # Use consistent prefix
        itemformset = PatItemFormSet(instance=pat, prefix='items')

    return render(request, 'assistencia/editar_pat.html', {
        'form': form,
        'pat': pat,
        'itemformset': itemformset
    })

@login_required
@group_required(['Administradores', 'Técnicos'])
def equipamentos_por_cliente(request):
    """Retorna os equipamentos associados ao cliente selecionado"""
    # Get client ID parameter
    cliente_id = request.GET.get("cliente_id")
    logger.info(f"Equipment request for client ID: {cliente_id}")

    if not cliente_id:
        logger.warning("No client ID provided")
        return JsonResponse({
            "success": False,
            "message": "ID do cliente não fornecido."
        }, status=400)

    try:
        from clientes.models import Cliente
        from equipamentos.models import EquipamentoCliente

        # Validate client exists
        cliente = Cliente.objects.get(id=cliente_id)

        # Get equipment with efficient querying
        equipamentos = EquipamentoCliente.objects.filter(
            cliente=cliente
        ).select_related('equipamento_fabricado')

        logger.info(f"Found {equipamentos.count()} equipment items for client {cliente_id}")

        equipamentos_data = []
        for eq in equipamentos:
            # Skip equipment with missing fabrication info
            if not eq.equipamento_fabricado:
                logger.warning(f"Equipment {eq.id} has no fabrication data")
                continue

            # Add equipment to the response list with all required fields
            equipamentos_data.append({
                "id": eq.id,
                "nome": eq.equipamento_fabricado.nome,
                "numero_serie": eq.numero_serie
            })

        logger.info(f"Returning {len(equipamentos_data)} equipment items")
        return JsonResponse({
            "success": True,
            "equipamentos": equipamentos_data
        })

    except Cliente.DoesNotExist:
        logger.warning(f"Client with ID {cliente_id} not found")
        return JsonResponse({
            "success": False,
            "message": "Cliente não encontrado."
        }, status=404)

    except Exception as e:
        logger.error(f"Error fetching equipment: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            "success": False,
            "message": f"Erro ao buscar equipamentos: {str(e)}"
        }, status=500)

@login_required
@group_required(['Administradores', 'Técnicos', 'Gestores de Clientes'])
def listar_pats(request):
    """Lista os pedidos de assistência técnica"""
    # Get query parameters
    search_query = request.GET.get('q', '')
    estado_filter = request.GET.get('estado', '')
    cliente_id = request.GET.get('cliente', '')
    sort_by = request.GET.get('sort', '')
    sort_dir = request.GET.get('sort_dir', 'asc')

    # Start with all PATs - this will be filtered
    pats = PedidoAssistencia.objects.all()

    # Get all PATs before filtering - for accurate count badges
    all_pats = PedidoAssistencia.objects.all()

    # Apply search filter if provided
    if search_query:
        # Use Q objects for complex OR queries
        pats = pats.filter(
            Q(pat_number__icontains=search_query) |
            Q(cliente__nome__icontains=search_query) |
            Q(numero_serie_equipamento__icontains=search_query) |
            Q(equipamento__numero_serie__icontains=search_query) |
            Q(descricao_problema__icontains=search_query)
        )

    # Apply cliente filter if provided
    if cliente_id:
        pats = pats.filter(cliente_id=cliente_id)

    # Get counts for each status - USING ALL_PATS for accurate counts
    estado_counts = {
        'todas': all_pats.count(),
        'aberto': all_pats.filter(estado='aberto').count(),
        'em_diagnostico': all_pats.filter(estado='em_diagnostico').count(),
        'em_andamento': all_pats.filter(estado='em_andamento').count(),
        'aguardando_peca': all_pats.filter(estado='aguardando_peca').count(),
        'aguardando_cliente': all_pats.filter(estado='aguardando_cliente').count(),
        'concluido': all_pats.filter(estado='concluido').count(),
    }

    # Apply estado filter AFTER counting
    if estado_filter and estado_filter != 'todas':
        pats = pats.filter(estado=estado_filter)

    # Apply sorting
    if sort_by:
        # Add negative sign for descending order
        if sort_dir == 'desc':
            sort_by = f"-{sort_by}"
        pats = pats.order_by(sort_by)
    else:
        # Default sorting: newest first
        pats = pats.order_by('-data_entrada')

    # Pass data to template
    context = {
        'pats': pats,
        'search_query': search_query,
        'estado_filter': estado_filter if estado_filter else 'todas',  # Default to 'todas' if empty
        'cliente_id': cliente_id,
        'estado_counts': estado_counts,
        'sort_by': sort_by.replace('-', '') if sort_by and sort_by.startswith('-') else sort_by,
        'sort_dir': 'desc' if sort_by and sort_by.startswith('-') else 'asc',
        'all_states': dict(PedidoAssistencia.STATUS_CHOICES),  # Fixed: Changed ESTADO_CHOICES to STATUS_CHOICES
        'active_tab': 'pats',
        'nav_active': 'pats',
    }

    return render(request, 'assistencia/listar_pats.html', context)

@login_required
@group_required(['Administradores', 'Técnicos'])
def detalhes_pat(request, pat_id):
    pat = get_object_or_404(PedidoAssistencia, id=pat_id)
    pat_items = pat.itens.all() if hasattr(pat, 'itens') else []
    total_valor = pat.total_valor if hasattr(pat, 'total_valor') else 0

    # Get active tab from URL or default to 'detalhes'
    active_tab = request.GET.get('tab', 'detalhes')

    # Get history with detailed changes - using a helper function for cleaner code
    history_data = prepare_history_data(pat)

    context = {
        'pat': pat,
        'pat_items': pat_items,
        'total_valor': total_valor,
        'active_tab': active_tab,
        'history_data': history_data,
    }
    return render(request, 'assistencia/detalhes_pat.html', context)

def prepare_history_data(pat):
    """
    Prepare detailed history data with actual changes between versions
    """
    history_items = list(pat.history.all())
    history_data = []

    for i, current in enumerate(history_items):
        # Store basic information for each history item
        item_data = {
            'history_item': current,
            'changes': [],
            'previous': None,
            'changed_fields': []
        }

        # Skip the first history item in reverse order (latest), as there's no previous version to compare
        if i < len(history_items) - 1:
            prev = history_items[i + 1]  # Previous version in history
            item_data['previous'] = prev
            changed_fields = []

            # Compare all fields to identify changes
            for field in pat._meta.fields:
                field_name = field.name
                if field_name not in ['id', 'history_id', 'history_date', 'history_change_reason', 'history_type']:
                    old_value = getattr(prev, field_name)
                    new_value = getattr(current, field_name)

                    # If values differ, add to changes list
                    if old_value != new_value:
                        # Format the values for display
                        old_display = format_field_value(pat, field_name, old_value)
                        new_display = format_field_value(pat, field_name, new_value)

                        # Get human-readable field name
                        field_verbose = field.verbose_name if hasattr(field, 'verbose_name') else field_name.replace('_', ' ').title()

                        # Add to changes list
                        item_data['changes'].append({
                            'field': field_name,
                            'field_verbose': field_verbose,
                            'old': old_value,
                            'new': new_value,
                            'old_display': old_display,
                            'new_display': new_display
                        })
                        changed_fields.append(field_name)

            item_data['changed_fields'] = changed_fields

        history_data.append(item_data)

    return history_data

def format_field_value(obj, field_name, value):
    """Format field values for human-readable display"""
    # Handle dates
    if field_name.endswith('_date') or field_name in ['data_entrada', 'data_conclusao', 'data_criacao']:
        if value:
            return value.strftime('%d/%m/%Y') if hasattr(value, 'strftime') else str(value)
        return '(sem data)'

    # Handle choice fields
    if field_name == 'estado' and hasattr(obj, 'get_estado_display'):
        try:
            # Create a temporary instance with the value to get the display
            temp_obj = type(obj)()
            setattr(temp_obj, field_name, value)
            return temp_obj.get_estado_display()
        except:
            return str(value)

    # Handle foreign keys
    if field_name in ['cliente', 'equipamento', 'tecnico']:
        if value and hasattr(value, 'nome'):
            return value.nome
        elif value and hasattr(value, 'username'):
            return value.username
        elif value and hasattr(value, 'id'):
            return f"ID: {value.id}"

    # Default
    return str(value) if value is not None else '(vazio)'

@login_required
@group_required(['Administradores'])
@require_POST
def excluir_pat(request, pat_id):
    """Delete a PAT and return JSON response"""
    logger.info(f"Attempting to delete PAT {pat_id}")

    try:
        with transaction.atomic():
            pat = get_object_or_404(PedidoAssistencia, id=pat_id)

            # Store info before deletion for logging
            pat_number = pat.pat_number

            # Check for related items and delete
            pat.itens.all().delete()
            pat.delete()

            logger.info(f"PAT {pat_number} successfully deleted")
            return JsonResponse({
                "success": True,
                "message": f"PAT {pat_number} excluída com sucesso"
            })

    except PedidoAssistencia.DoesNotExist:
        logger.warning(f"Attempted to delete non-existent PAT {pat_id}")
        return JsonResponse({
            "success": False,
            "message": "PAT não encontrada"
        }, status=404)

    except Exception as e:
        logger.error(f"Failed to delete PAT {pat_id}: {str(e)}", exc_info=True)
        return JsonResponse({
            "success": False,
            "message": "Erro ao excluir PAT. Por favor, tente novamente."
        }, status=500)

@login_required
@group_required(['Administradores', 'Técnicos'])
@require_POST
def excluir_item_pat(request, item_id):
    """API endpoint para excluir um item de PAT via AJAX"""
    try:
        item = get_object_or_404(ItemPAT, id=item_id)
        pat_id = item.pat.id  # Guarde o ID do PAT antes de excluir o item

        # Verifique permissões se necessário

        # Exclua o item
        item.delete()

        return JsonResponse({
            'success': True,
            'message': 'Item excluído com sucesso'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@group_required(['Administradores', 'Técnicos'])
@require_POST
def mudar_status_pat(request, pat_id):
    """Change PAT status via AJAX request"""
    try:
        data = json.loads(request.body)
        new_status = data.get('new_status')
        note = data.get('note', '')

        pat = get_object_or_404(PedidoAssistencia, id=pat_id)
        old_status = pat.estado

        # Check if status is valid
        valid_statuses = dict(PedidoAssistencia.ESTADO_CHOICES).keys()
        if new_status not in valid_statuses:
            return JsonResponse({'success': False, 'message': 'Status inválido'})

        # Update status with history tracking
        pat.estado = new_status

        # Add note as change reason
        if note:
            pat._change_reason = note
        else:
            pat._change_reason = f"Status alterado de {pat.get_estado_display(old_status)} para {pat.get_estado_display()}"

        # Handle completion date if status is completed
        if new_status == 'concluido' and not pat.data_conclusao:
            pat.data_conclusao = timezone.now()
        elif new_status != 'concluido' and pat.data_conclusao:
            pat.data_conclusao = None

        pat.save()

        return JsonResponse({'success': True})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

# Add this new view to the assistencia/views.py file

@login_required
@group_required(['Administradores', 'Técnicos'])
def historico_pat(request, pat_id):
    """View to show complete PAT history"""
    pat = get_object_or_404(PedidoAssistencia, id=pat_id)

    # Get PAT history changes
    pat_history = pat.history.all()

    # Get status history records
    status_history = pat.status_history.all()

    # Get associated notes, if any
    try:
        from notas.models import Nota
        notas = Nota.objects.filter(pat=pat).order_by('-data_criacao')
    except:
        notas = []

    context = {
        'pat': pat,
        'pat_history': pat_history,
        'status_history': status_history,
        'notas': notas,
        'active_tab': 'historico'
    }

    return render(request, 'assistencia/historico_pat.html', context)