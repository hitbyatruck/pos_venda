from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.http import require_POST
from .models import PedidoAssistencia, ItemPat, HistoricoPAT
from .forms import PedidoAssistenciaForm, EditItemPatFormSet, PedidoAssistenciaFormSet, PatForm, PatItemFormSet
from clientes.models import Cliente
import logging
import re
import datetime
import unicodedata
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from core.utils import group_required
from core.search import AdvancedSearch
from django.urls import reverse

@login_required
@group_required(['Administradores', 'Técnicos'])
def criar_pat(request):
    """Cria um novo Pedido de Assistência Técnica (PAT)"""
    if request.method == "POST":
        form = PedidoAssistenciaForm(request.POST)
        formset = PedidoAssistenciaFormSet(request.POST)
        
        # Se o formulário principal for válido
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Criar instância temporária para validação
                    pat = form.save(commit=False)
                    
                    # Executar validação adicional (verifica número PAT único)
                    pat.full_clean()
                    
                    # Salvar o PAT
                    pat.save()
                    
                    # Processar o formset
                    valid_forms = []
                    has_errors = False
                    
                    # Processar cada formulário no formset
                    for item_form in formset:
                        # Verificar se é um formulário vazio
                        if not item_form.has_changed():
                            continue
                            
                        data = item_form.cleaned_data if hasattr(item_form, 'cleaned_data') else {}
                        
                        # Verificar se o form está marcado para exclusão
                        if data.get('DELETE', False):
                            continue
                            
                        # Verificar se o form está vazio (todos os campos principais vazios)
                        is_empty = not data.get('tipo') and not data.get('referencia', '').strip() and not data.get('designacao', '').strip()
                        
                        if is_empty:
                            # Formulário vazio, ignorar
                            continue
                            
                        # Se chegou aqui, temos um formulário com dados
                        if item_form.is_valid():
                            valid_forms.append(item_form)
                        else:
                            has_errors = True
                    
                    # Se não houver erros, salvar os formulários válidos
                    if not has_errors:
                        for item_form in valid_forms:
                            item = item_form.save(commit=False)
                            item.pat = pat
                            item.save()
                            
                        messages.success(request, "PAT criada com sucesso.")
                        return redirect('assistencia:listar_pats')
                    else:
                        messages.error(request, "Por favor, corrija os erros nos itens.")
                        
            except ValidationError as e:
                # Capturar erros do modelo (como número PAT duplicado)
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
                        
            except Exception as e:
                messages.error(request, f"Erro ao criar PAT: {str(e)}")
        else:
            # Formulário principal inválido
            messages.error(request, "Por favor, corrija os erros no formulário.")
    else:
        # GET request
        form = PedidoAssistenciaForm()
        formset = PedidoAssistenciaFormSet()

    return render(request, 'assistencia/criar_pat.html', {
        'form': form, 
        'formset': formset
    })

@login_required
@group_required(['Administradores', 'Técnicos'])
def listar_pats(request):
    # Configuração da ordenação
    ordenar_por = request.GET.get('ordenar_por', 'data_entrada')
    direcao = request.GET.get('direcao', 'desc')
    ordem = '-' + ordenar_por if direcao == 'desc' else ordenar_por
    
    # Parâmetros de pesquisa
    estado = request.GET.get('estado', 'aberto')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    
    # Inicializar a consulta base
    queryset = PedidoAssistencia.objects.all().select_related(
        'cliente', 
        'equipamento', 
        'equipamento__equipamento_fabricado'
    ).prefetch_related('itens')
    
    # Aplicar filtro de estado - Apenas filtrar se não for 'todos'
    if estado and estado != 'todos':
        queryset = queryset.filter(estado=estado)
        
    # Inicializar o serviço de pesquisa
    search_service = AdvancedSearch(
        request=request,
        model_class=PedidoAssistencia,
        fields_to_search=['pat_number', 'relatorio']
    )
    
    # Executar a pesquisa normalizada com campos relacionados
    pats = search_service.search(queryset)
    
    # Filtro por período de data
    if data_inicio:
        try:
            data_inicio_obj = datetime.datetime.strptime(data_inicio, '%Y-%m-%d').date()
            pats = pats.filter(data_entrada__gte=data_inicio_obj)
        except (ValueError, TypeError):
            messages.warning(request, "Formato de data inválido para data inicial.")
    
    if data_fim:
        try:
            data_fim_obj = datetime.datetime.strptime(data_fim, '%Y-%m-%d').date()
            pats = pats.filter(data_entrada__lte=data_fim_obj)
        except (ValueError, TypeError):
            messages.warning(request, "Formato de data inválido para data final.")
    
    # Ordenação
    pats = pats.order_by(ordem)
    
    # Paginação
    paginator = Paginator(pats, 20)  # 20 PATs por página
    page = request.GET.get('page', 1)
    
    try:
        pats = paginator.page(page)
    except PageNotAnInteger:
        pats = paginator.page(1)
    except EmptyPage:
        pats = paginator.page(paginator.num_pages)
    
    # HTML para os filtros avançados
    filter_html = """
    <!-- Campo de pesquisa geral -->
    <div class="col-md-6">
      <label for="q" class="form-label">Pesquisar</label>
      <input type="text" class="form-control" id="q" name="q" value="{q}" 
        placeholder="PAT, cliente, equipamento, número de série...">
    </div>

    <!-- Filtros específicos -->
    <div class="col-md-3">
      <label for="data_inicio" class="form-label">Data Início</label>
      <input type="date" class="form-control" id="data_inicio" name="data_inicio" value="{data_inicio}">
    </div>
    
    <div class="col-md-3">
      <label for="data_fim" class="form-label">Data Fim</label>
      <input type="date" class="form-control" id="data_fim" name="data_fim" value="{data_fim}">
    </div>
    """.format(
        q=request.GET.get('q', ''),
        data_inicio=request.GET.get('data_inicio', ''),
        data_fim=request.GET.get('data_fim', ''),
    )
    
    # Contexto
    context = {
        'pats': pats,
        'direcao': 'asc' if direcao == 'desc' else 'desc',  # Inverte para próximo clique
        'ordenar_por': ordenar_por,
        'estado_atual': estado,
        'query': search_service.query,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'status_choices': PedidoAssistencia.ESTADO_CHOICES,
        'filter_html': filter_html,
        'breadcrumbs': [
            {'title': 'Assistência', 'url': None}
        ]
    }
    
    return render(request, 'assistencia/listar_pats.html', context)

@login_required
@group_required(['Administradores', 'Técnicos'])
def detalhes_pat(request, pat_id):
    pat = get_object_or_404(PedidoAssistencia, id=pat_id)
    historico = HistoricoPAT.objects.filter(pat=pat).order_by('-data_registo')
    
    # Adicione breadcrumbs
    breadcrumbs = [
        {'title': ('Assistências'), 'url': reverse('assistencia:listar_pats')},
        {'title': f'PAT #{pat.pat_number}', 'url': None}
    ]
    
    return render(request, 'assistencia/detalhes_pat.html', {
        'pat': pat,
        'historico': historico,
        'breadcrumbs': breadcrumbs  # Adicione esta linha
    })

@login_required
@group_required(['Administradores', 'Técnicos'])
def editar_pat(request, pat_id):
    pat = get_object_or_404(PedidoAssistencia, id=pat_id)
    
    if request.method == 'POST':
        form = PatForm(request.POST, instance=pat)
        # Use EditItemPatFormSet aqui!
        formset = EditItemPatFormSet(request.POST, instance=pat)
        
        # DEBUG: Vamos ver o que está acontecendo
        print("========================= DEBUG =========================")
        print(f"Form is valid: {form.is_valid()}")
        print(f"Formset is valid: {formset.is_valid()}")

        print("RAW POST DATA para DELETE:")
        for key, value in request.POST.items():
            if 'DELETE' in key:
                print(f"{key}: {value}")

        # Tentar uma abordagem mais direta para encontrar items excluídos
        print("==== TENTANDO ENCONTRAR ITENS PARA EXCLUIR DE FORMA ALTERNATIVA ====")

        for key, value in request.POST.items():
            if key.endswith('-DELETE') and value in ('on', 'true', '1', 'checked'):
                try:
                    prefix = key.split('-DELETE')[0]
                    id_field = f"{prefix}-id"
                    if id_field in request.POST:
                        item_id = request.POST[id_field]
                        print(f"ITEM PARA EXCLUSÃO: ID={item_id}")
                        
                        # Excluir diretamente pelo ID
                        try:
                            item = ItemPat.objects.get(id=item_id)
                            print(f"EXCLUINDO ITEM com ID {item_id}")
                            item.delete()
                            print(f"Item excluído com sucesso!")
                        except Exception as e:
                            print(f"Erro ao excluir item: {str(e)}")
                except Exception as e:
                    print(f"Erro ao processar exclusão: {str(e)}")

        # Inicializar a lista forms_to_delete AQUI! (linha já existente)
        forms_to_delete = []

        # Inicializar a lista forms_to_delete AQUI!
        forms_to_delete = []
        
        # Processar os formulários para encontrar os marcados para exclusão
        for item_form in formset:
            if not hasattr(item_form, 'cleaned_data'):
                continue
                
            data = item_form.cleaned_data
            item_id = data.get('id', 'Nova linha')
            is_deleted = data.get('DELETE', False)
            
            print(f"Item ID: {item_id}, Marcado para exclusão: {is_deleted}")
            
            # Verificar se está marcado para exclusão
            if is_deleted:
                if data.get('id'):  # Se tem ID, é um registro existente
                    print(f">>> EFETIVAMENTE MARCADO PARA EXCLUSÃO: {item_form.instance.pk}")
                    forms_to_delete.append(item_form)
                    continue

        if form.is_valid():
            try:
                with transaction.atomic():
                    # Obter instância para validação
                    pat_instance = form.save(commit=False)
                    
                    # Validar instância incluindo unicidade do número PAT
                    pat_instance.full_clean()
                    
                    # Salvar
                    pat_instance.save()
                    
                    # IMPORTANTE: Primeiro excluir explicitamente os marcados para exclusão
                    print(f"Formulários para excluir: {len(forms_to_delete)}")
                    for item_form in forms_to_delete:
                        if item_form.instance.pk:
                            print(f"Excluindo item: {item_form.instance.pk}")
                            item_form.instance.delete()
                    
                    # Depois processar os formulários válidos
                    valid_forms = []
                    has_errors = False
                    
                    # Processar formulários existentes, IGNORANDO os já marcados para exclusão
                    for item_form in formset:
                        if not hasattr(item_form, 'cleaned_data'):
                            continue
                            
                        data = item_form.cleaned_data
                        
                        # Pular formulários já marcados para exclusão
                        if data.get('DELETE', False):
                            continue
                            
                        # Verificar se está vazio
                        is_empty = not data.get('tipo') and not data.get('referencia', '').strip() and not data.get('designacao', '').strip()
                        
                        if is_empty:
                            continue
                            
                        # Chegou aqui, temos um form com dados
                        if item_form.is_valid():
                            valid_forms.append(item_form)
                        else:
                            has_errors = True
                    
                    # Se não houver erros, salvar os formulários válidos
                    if not has_errors:
                        # Salvar os válidos
                        for item_form in valid_forms:
                            item = item_form.save(commit=False)
                            item.pat = pat_instance
                            item.save()
                            
                        messages.success(request, 'PAT atualizada com sucesso.')
                        return redirect('assistencia:detalhes_pat', pat_id=pat.id)
                    else:
                        messages.error(request, "Por favor, corrija os erros nos itens.")
                        
            except ValidationError as e:
                # Capturar erros do modelo
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
                        
            except Exception as e:
                messages.error(request, f"Erro ao atualizar PAT: {str(e)}")
    else:
        # GET request
        form = PatForm(instance=pat)
        formset = EditItemPatFormSet(instance=pat)
    
    return render(request, 'assistencia/editar_pat.html', {
        'form': form,
        'formset': formset,
        'pat': pat,
        'pat_id': pat.id
    })

logger = logging.getLogger(__name__)


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
def equipamentos_por_cliente(request):
    """Retorna os equipamentos associados ao cliente selecionado"""
    cliente_id = request.GET.get("cliente_id")
    
    if not cliente_id:
        return JsonResponse({
            "success": False,
            "message": "ID do cliente não fornecido."
        }, status=400)

    try:
        cliente = get_object_or_404(Cliente, id=cliente_id)
        equipamentos = cliente.equipamentos.select_related('equipamento_fabricado').all()
        
        equipamentos_data = [{
            "id": eq.id,
            "nome": eq.equipamento_fabricado.nome,
            "numero_serie": eq.numero_serie
        } for eq in equipamentos]

        return JsonResponse({
            "success": True,
            "equipamentos": equipamentos_data
        })
    except Cliente.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Cliente não encontrado."
        }, status=404)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": f"Erro ao buscar equipamentos: {str(e)}"
        }, status=500)
    
@login_required
@group_required(['Administradores', 'Técnicos'])
@require_POST
def excluir_item_pat(request, item_id):
    """API endpoint para excluir um item de PAT via AJAX"""
    try:
        item = get_object_or_404(ItemPat, id=item_id)
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