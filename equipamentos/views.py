from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import EquipamentoFabricado, DocumentoEquipamento, CategoriaEquipamento
from .forms import EquipamentoFabricadoForm, CategoriaEquipamentoForm
from clientes.models import EquipamentoCliente
from assistencia.models import PedidoAssistencia
from notas.models import Nota
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError, FieldError
from django.db.models import Q
from core.utils import group_required
from django.urls import reverse
from django.contrib import messages
import unicodedata

def normalize_text(text):
    if not text:
        return ""
    # Normalizar texto para remover acentos
    normalized = unicodedata.normalize('NFKD', str(text))
    normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])
    # Converter para minúsculas e remover espaços extras
    return normalized.lower().strip()

@login_required
@group_required(['Administradores', 'Técnicos'])
def listar_equipamentos_fabricados(request):
    # Parâmetros de busca e filtro
    q = request.GET.get('q', '')
    categoria_id = request.GET.get('categoria', '')
    normalized_query = ""
    
    # Query base com pré-carregamento de relacionamentos
    equipamentos = EquipamentoFabricado.objects.all().select_related('categoria')
    
    # Filtro por categoria
    if categoria_id:
        try:
            categoria_id = int(categoria_id)
            equipamentos = equipamentos.filter(categoria_id=categoria_id)
        except (ValueError, TypeError):
            pass
    
    # Busca por texto
    if q:
        normalized_query = normalize_text(q)
        search_terms = normalized_query.split()
        
        matched_results = set()
        first_iteration = True
        
        for term in search_terms:
            results = list(equipamentos)
            matching_ids = []
            
            for eq in results:
                fields_to_check = [
                    eq.nome or '',
                    eq.referencia_interna or '',
                    eq.descricao or '',
                    eq.especificacoes or '',
                    eq.categoria.nome if eq.categoria else ''
                ]
                
                combined_text = normalize_text(' '.join([str(field) for field in fields_to_check if field]))
                
                if term in combined_text:
                    matching_ids.append(eq.id)
            
            term_results = set(matching_ids)
            
            if first_iteration:
                matched_results = term_results
                first_iteration = False
            else:
                matched_results &= term_results
        
        if matched_results:
            equipamentos = equipamentos.filter(id__in=matched_results)
        else:
            equipamentos = EquipamentoFabricado.objects.none()
    
    # Ordenação padrão
    equipamentos = equipamentos.order_by('nome')
    
    # Categorias para o filtro dropdown
    categorias = CategoriaEquipamento.objects.all()
    
    breadcrumbs = [
        {'title': ('Equipamentos'), 'url': None}
    ]
    
    return render(request, 'equipamentos/listar_equipamentos_fabricados.html', {
        'equipamentos': equipamentos,
        'categorias': categorias,
        'query': q,
        'categoria_selecionada': categoria_id,
        'breadcrumbs': breadcrumbs
    })


@login_required
@group_required(['Administradores', 'Técnicos'])
def adicionar_equipamento_fabricado(request):
    if request.method == 'POST':
        form = EquipamentoFabricadoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Criar objeto mas não salvar no banco ainda
                equipamento = form.save(commit=False)
                # Executar validações personalizadas
                equipamento.full_clean()
                # Salvar o objeto validado
                equipamento.save()
                # Tratar os documentos anexados
                for arquivo in request.FILES.getlist('documentos'):
                    DocumentoEquipamento.objects.create(equipamento=equipamento, arquivo=arquivo)
                
                messages.success(request, "Equipamento adicionado com sucesso!")
                return redirect('equipamentos:listar_equipamentos_fabricados')
            except ValidationError as e:
                # Adicionar erros de validação ao formulário
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
                messages.error(request, "Erro ao adicionar equipamento. Verifique os campos destacados.")
    else:
        form = EquipamentoFabricadoForm()
    
    # Adicione breadcrumbs
    breadcrumbs = [
        {'title': ('Equipamentos'), 'url': reverse('equipamentos:listar_equipamentos_fabricados')},
        {'title': ('Adicionar Equipamento'), 'url': None}
    ]
    
    return render(request, 'equipamentos/adicionar_equipamento_fabricado.html', {
        'form': form,
        'breadcrumbs': breadcrumbs
    })

@login_required
@group_required(['Administradores', 'Técnicos'])
def detalhes_equipamento(request, equipamento_id):
    equipamento = get_object_or_404(EquipamentoFabricado, id=equipamento_id)
    equipamentos_cliente = EquipamentoCliente.objects.filter(equipamento_fabricado=equipamento)
    assistencias = PedidoAssistencia.objects.filter(equipamento__in=equipamentos_cliente).order_by('-data_entrada')
    # Ajustar a consulta de notas
    try:
        notas = Nota.objects.filter(equipamento_fabricado=equipamento).order_by('-data_criacao')
    except FieldError:
        # Alternativa: se a relação for com o equipamento do cliente
        notas = Nota.objects.filter(equipamento__in=equipamentos_cliente).order_by('-data_criacao')
    
    # Adicione breadcrumbs
    breadcrumbs = [
        {'title': ('Equipamentos'), 'url': reverse('equipamentos:listar_equipamentos_fabricados')},
        {'title': f"Equipamento {equipamento.id}", 'url': None}
    ]
    
    return render(request, 'equipamentos/detalhes_equipamento.html', {
        'equipamento': equipamento,
        'equipamentos_cliente': equipamentos_cliente,
        'assistencias': assistencias,
        'notas': notas,
        'breadcrumbs': breadcrumbs
    })

@login_required
@group_required(['Administradores', 'Técnicos'])
def editar_equipamento_fabricado(request, equipamento_id):
    equipamento = get_object_or_404(EquipamentoFabricado, pk=equipamento_id)
    documentos = DocumentoEquipamento.objects.filter(equipamento=equipamento)
    
    if request.method == 'POST':
        form = EquipamentoFabricadoForm(request.POST, request.FILES, instance=equipamento)
        if form.is_valid():
            try:
                # Criar objeto mas não salvar no banco ainda
                equipamento = form.save(commit=False)
                # Executar validações personalizadas
                equipamento.full_clean()
                # Salvar o objeto validado
                equipamento.save()
                # Tratar os documentos anexados
                for arquivo in request.FILES.getlist('documentos'):
                    DocumentoEquipamento.objects.create(equipamento=equipamento, arquivo=arquivo)
                
                messages.success(request, "Equipamento atualizado com sucesso!")
                return redirect('equipamentos:detalhes_equipamento', equipamento_id=equipamento.id)
            except ValidationError as e:
                # Adicionar erros de validação ao formulário
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
                messages.error(request, "Erro ao atualizar equipamento. Verifique os campos destacados.")
    else:
        form = EquipamentoFabricadoForm(instance=equipamento)
    
    # Adicione breadcrumbs
    breadcrumbs = [
        {'title': ('Equipamentos'), 'url': reverse('equipamentos:listar_equipamentos_fabricados')},
        {'title': equipamento.nome, 'url': reverse('equipamentos:detalhes_equipamento', args=[equipamento.id])},
        {'title': ('Editar'), 'url': None}
    ]
    
    return render(request, 'equipamentos/editar_equipamento_fabricado.html', {
        'form': form,
        'documentos': documentos,
        'equipamento': equipamento,
        'breadcrumbs': breadcrumbs
    })

@login_required
@group_required(['Administradores', 'Técnicos'])
@require_http_methods(["DELETE"])
def excluir_equipamento_fabricado(request, pk):
    try:
        equipamento = get_object_or_404(EquipamentoFabricado, pk=pk)
        force = request.GET.get('force') == 'true'
        
        try:
            equipamento.delete(force=force)
            return JsonResponse({'status': 'success'})
        except ValidationError as e:
            # Get the first message without list formatting
            message = str(e.message) if hasattr(e, 'message') else str(e.messages[0])
            return JsonResponse({
                'status': 'warning',
                'message': message,
                'requireForce': True
            })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@login_required
@group_required(['Administradores', 'Técnicos'])   
@csrf_exempt
def upload_documento_equipamento(request, equipamento_id):
    equipamento = get_object_or_404(EquipamentoFabricado, id=equipamento_id)
    if request.method == 'POST' and request.FILES.get('arquivo'):
        documento = DocumentoEquipamento.objects.create(
            equipamento=equipamento,
            arquivo=request.FILES['arquivo']
        )
        return JsonResponse({'success': True, 'documento_id': documento.id, 'documento_url': documento.arquivo.url})
    return JsonResponse({'success': False})

@login_required
@group_required(['Administradores', 'Técnicos'])
@csrf_exempt
def excluir_documento(request, documento_id):
    documento = get_object_or_404(DocumentoEquipamento, id=documento_id)
    if request.method == 'POST':
        documento.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

def listar_equipamentos_cliente(request):
    equipamentos = EquipamentoCliente.objects.all()
    
    # Adicione breadcrumbs
    breadcrumbs = [
        {'title': ('Equipamentos de Clientes'), 'url': None}
    ]
    
    return render(request, 'equipamentos/listar_equipamentos_cliente.html', {
        'equipamentos': equipamentos,
        'breadcrumbs': breadcrumbs
    })

def listar_categorias(request):
    categorias = CategoriaEquipamento.objects.all()
    return render(request, 'equipamentos/lista_categorias.html', {'categorias': categorias})

def adicionar_categoria(request):
    from .forms import CategoriaEquipamentoForm
    if request.method == "POST":
        form = CategoriaEquipamentoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('equipamentos:listar_categorias')
    else:
        form = CategoriaEquipamentoForm()
    return render(request, 'equipamentos/adicionar_categoria.html', {'form': form})
