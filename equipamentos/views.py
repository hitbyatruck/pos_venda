from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import EquipamentoFabricado, DocumentoEquipamento, CategoriaEquipamento
from .forms import EquipamentoFabricadoForm, CategoriaEquipamentoForm
from clientes.models import EquipamentoCliente, Cliente
from assistencia.models import PedidoAssistencia
from notas.models import Nota
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError, FieldError
from django.db.models import Q
from core.utils import group_required
from core.search import AdvancedSearch
from django.urls import reverse
from django.contrib import messages
import unicodedata
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

def normalize_text(text):
    if not text:
        return ""
    # Normalizar texto para remover acentos
    normalized = unicodedata.normalize('NFKD', str(text))
    normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])
    # Converter para minúsculas e remover espaços extras
    return normalized.lower().strip()

@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def listar_equipamentos_fabricados(request):
    search_query = request.GET.get('q', '')
    categoria_id = request.GET.get('categoria', '')
    
    equipamentos = EquipamentoFabricado.objects.all()
    
    # Apply search filters if provided
    if search_query:
        equipamentos = equipamentos.filter(
            Q(nome__icontains=search_query) |  # Changed from modelo to nome
            Q(referencia_interna__icontains=search_query) |
            Q(descricao__icontains=search_query)
        )
    
    if categoria_id:
        equipamentos = equipamentos.filter(categoria_id=categoria_id)
    
    # Get sorting parameter and fix default from 'modelo' to 'nome'
    order_by = request.GET.get('orderby', 'nome')  # Changed default from modelo to nome
    
    # Map frontend field names to database field names if needed
    field_mapping = {
        'modelo': 'nome',
        '-modelo': '-nome'
    }
    
    # If orderby is using the frontend field name, map it to the database field name
    actual_order_by = field_mapping.get(order_by, order_by)
    
    equipamentos = equipamentos.order_by(actual_order_by)
    
    # Pagination
    paginator = Paginator(equipamentos, 10)  # Show 10 items per page
    page = request.GET.get('pagina', 1)
    
    try:
        equipamentos = paginator.page(page)
    except PageNotAnInteger:
        equipamentos = paginator.page(1)
    except EmptyPage:
        equipamentos = paginator.page(paginator.num_pages)
    
    # Get all categories for filter dropdown
    categorias = CategoriaEquipamento.objects.all()
    
    context = {
        'equipamentos': equipamentos,
        'search_query': search_query,
        'categoria_selecionada': categoria_id,
        'orderby': order_by,  # Keep the original value for form display
        'categorias': categorias,
        'total_equipamentos': paginator.count,
        'active_tab': 'fabricados'
    }
    
    # Ensure we're using the correct template
    return render(request, 'equipamentos/lista_fab.html', context)

@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def listar_equipamentos(request):
    """View to list all equipment (both manufactured and client equipment)"""
    # Get equipment data
    equipamentos_fabricados = EquipamentoFabricado.objects.all()
    equipamentos_cliente = EquipamentoCliente.objects.all()
    
    # Apply search filters if provided
    search_query = request.GET.get('q', '')
    if search_query:
        equipamentos_fabricados = equipamentos_fabricados.filter(
            Q(nome__icontains=search_query) |  # Changed from modelo to nome
            Q(referencia_interna__icontains=search_query) |
            Q(descricao__icontains=search_query)
        )
        
        equipamentos_cliente = equipamentos_cliente.filter(
            Q(numero_serie__icontains=search_query) |
            Q(cliente__nome__icontains=search_query) |
            Q(equipamento_fabricado__nome__icontains=search_query)  # Changed from modelo to nome
        )
    
    # Prepare context
    context = {
        'equipamentos_fabricados': equipamentos_fabricados,
        'equipamentos_cliente': equipamentos_cliente,
        'search_query': search_query,
        'active_tab': 'equipamentos',  # To highlight the correct tab in navigation
    }
    
    return render(request, 'equipamentos/listar_equipamentos.html', context)

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

@login_required
def index(request):
    """Main index view for equipamentos app - redirects to the equipments list"""
    return redirect('equipamentos:listar_fabricados')

@login_required
def historico_equipamento_cliente(request, equipamento_id):
    """
    View para mostrar o histórico completo de um equipamento de cliente.
    Inclui detalhes do equipamento, histórico de propriedade e reparações.
    """
    equipamento = get_object_or_404(EquipamentoCliente, id=equipamento_id)
    
    # Determinar a aba ativa a partir da query string
    active_tab = request.GET.get('tab', 'detalhes')
    
    # Processar formulário de notas
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        conteudo = request.POST.get('conteudo')
        
        if titulo and conteudo:  # Fixed: changed && to and (Python syntax)
            try:
                # Criar nova nota associada ao equipamento
                Nota.objects.create(
                    titulo=titulo,
                    conteudo=conteudo,
                    equipamento=equipamento
                )
                # Redirecionar para a aba de notas após adicionar uma nova
                return redirect(f"{reverse('equipamentos:historico_equipamento_cliente', args=[equipamento.id])}?tab=notas")
            except Exception as e:
                print(f"Erro ao salvar nota: {str(e)}")
                messages.error(request, f"Erro ao salvar nota: {str(e)}")
    
    # Buscar histórico de pedidos de assistência para este equipamento
    numero_serie = equipamento.numero_serie
    historico_pats = PedidoAssistencia.objects.filter(
        Q(equipamento=equipamento) | 
        Q(numero_serie_equipamento=numero_serie)
    ).order_by('-data_criacao').distinct()
    
    # Buscar histórico de mudanças no objeto (requer django-simple-history)
    try:
        historico_mudancas = equipamento.history.all()
    except AttributeError:
        # Caso simple_history não esteja configurado para este modelo
        historico_mudancas = []
    
    # Buscar notas relacionadas a este equipamento
    try:
        notas = Nota.objects.filter(equipamento=equipamento).order_by('-data_criacao')
    except Exception as e:
        print(f"Erro ao buscar notas: {str(e)}")
        notas = []
    
    # Configurar breadcrumbs
    breadcrumbs = [
        {'title': 'Equipamentos', 'url': reverse('equipamentos:listar_equipamentos_cliente')},
        {'title': f'{equipamento.equipamento_fabricado.nome}', 
        'url': reverse('equipamentos:detalhes_equipamento', args=[equipamento.equipamento_fabricado.id])},
        {'title': f'Histórico (S/N: {equipamento.numero_serie})'}
    ]
    
    # Configurar abas de navegação específicas para o histórico
    nav_tabs = [
        {'id': 'detalhes', 'name': 'Detalhes', 'icon': 'bi-info-circle'},
        {'id': 'assistencia', 'name': 'Assistência Técnica', 'icon': 'bi-tools', 
         'badge': historico_pats.count() if historico_pats else 0},
        {'id': 'alteracoes', 'name': 'Mudanças', 'icon': 'bi-clock-history',
         'badge': historico_mudancas.count() if historico_mudancas else 0},
        {'id': 'notas', 'name': 'Notas', 'icon': 'bi-journal-text', 
         'badge': notas.count() if notas else 0}
    ]
    
    return render(request, 'equipamentos/historico_equipamento.html', {
        'equipamento': equipamento,
        'historico_pats': historico_pats,
        'historico_mudancas': historico_mudancas,
        'notas': notas,
        'breadcrumbs': breadcrumbs,
        'nav_tabs': nav_tabs,
        'active_tab': active_tab
    })

@login_required
def transferir_equipamento(request, equipamento_id):
    """Transfere um equipamento de um cliente para outro, mantendo o histórico"""
    equipamento = get_object_or_404(EquipamentoCliente, id=equipamento_id)
    
    pats_abertas = PedidoAssistencia.objects.filter(
    equipamento=equipamento,
    estado__in=['aberto', 'em_andamento', 'em_diagnostico', 'em_curso']
    )

    novo_cliente_id = request.POST.get('novo_cliente_id')
    data_transferencia = request.POST.get('data_transferencia')
    motivo = request.POST.get('motivo', '')
    fechar_pats = request.POST.get('fechar_pats') == 'on'

    if request.method == 'POST':
        novo_cliente_id = request.POST.get('novo_cliente_id')
        data_transferencia = request.POST.get('data_transferencia')
        motivo = request.POST.get('motivo', '')
        
        # Validar entradas
        if not novo_cliente_id or not data_transferencia:
            messages.error(request, "Por favor preencha todos os campos obrigatórios.")
            return redirect('equipamentos:transferir_equipamento', equipamento_id=equipamento_id)
            
        try:
            # Buscar o novo cliente
            novo_cliente = Cliente.objects.get(id=novo_cliente_id)
            
            # Registrar a transferência no histórico
            cliente_anterior = equipamento.cliente
            
            # Processar PATs abertas se solicitado
            if fechar_pats and pats_abertas.exists():
                for pat in pats_abertas:
                    pat.estado = 'concluido'
                    pat.data_conclusao = timezone.now()
                    pat.observacoes_tecnico = f"{pat.observacoes_tecnico or ''}\n\nPAT fechada automaticamente devido à transferência do equipamento para {novo_cliente.nome}."
                    pat.save()

            # Adicionar detalhes da transferência como comentário para o histórico
            equipamento._change_reason = f"Transferido de {cliente_anterior.nome} para {novo_cliente.nome}. Motivo: {motivo}"
            
            # Atualizar o equipamento com o novo cliente
            equipamento.cliente = novo_cliente
            equipamento.save()

            # Atualizar PATs existentes para refletir o novo cliente
            PedidoAssistencia.objects.filter(equipamento=equipamento).update(
                cliente=novo_cliente
)
            
            messages.success(request, f"Equipamento transferido com sucesso de {cliente_anterior.nome} para {novo_cliente.nome}.")
            return redirect('equipamentos:historico_equipamento_cliente', equipamento_id=equipamento_id)
            
        except Cliente.DoesNotExist:
            messages.error(request, "Cliente não encontrado.")
            return redirect('equipamentos:transferir_equipamento', equipamento_id=equipamento_id)
        except Exception as e:
            messages.error(request, f"Erro ao transferir equipamento: {str(e)}")
            return redirect('equipamentos:transferir_equipamento', equipamento_id=equipamento_id)
    
    # Configurar breadcrumbs
    breadcrumbs = [
        {'title': 'Equipamentos', 'url': reverse('equipamentos:listar_equipamentos_cliente')},
        {'title': f'Histórico: {equipamento.numero_serie}', 
         'url': reverse('equipamentos:historico_equipamento_cliente', args=[equipamento.id])},
        {'title': 'Transferir Equipamento'}
    ]
    
    # Renderizar formulário de transferência
    clientes = Cliente.objects.all().order_by('nome')
    return render(request, 'equipamentos/transferir_equipamento.html', {
        'equipamento': equipamento,
        'clientes': clientes,
        'breadcrumbs': breadcrumbs,
        'pats_abertas': pats_abertas
    })

@login_required
@group_required(['Administradores', 'Técnicos'])
def detalhes_equipamento_fabricado(request, equipamento_id):
    """View for manufactured equipment details - redirects to the generic equipment detail view"""
    return detalhes_equipamento(request, equipamento_id)

@login_required
@group_required(['Administradores', 'Técnicos'])
def adicionar_equipamento_cliente(request):
    """View to add equipment to a client"""
    cliente_id = request.GET.get('cliente')
    cliente = None
    
    if cliente_id:
        cliente = get_object_or_404(Cliente, id=cliente_id)
    
    if request.method == 'POST':
        # Process form data
        equipamento_fabricado_id = request.POST.get('equipamento_fabricado')
        numero_serie = request.POST.get('numero_serie')
        data_instalacao = request.POST.get('data_instalacao')
        observacoes = request.POST.get('observacoes')
        
        # Validation
        if not equipamento_fabricado_id or not numero_serie or not cliente_id:
            messages.error(request, "Por favor preencha todos os campos obrigatórios.")
        else:
            try:
                # Create new client equipment
                equipamento_fabricado = get_object_or_404(EquipamentoFabricado, id=equipamento_fabricado_id)
                cliente = get_object_or_404(Cliente, id=cliente_id)
                
                equipamento = EquipamentoCliente.objects.create(
                    equipamento_fabricado=equipamento_fabricado,
                    cliente=cliente,
                    numero_serie=numero_serie,
                    data_instalacao=data_instalacao,
                    observacoes=observacoes
                )
                
                messages.success(request, "Equipamento adicionado ao cliente com sucesso!")
                if 'next' in request.GET:
                    return redirect(request.GET.get('next'))
                return redirect('equipamentos:detalhes_cliente', equipamento_id=equipamento.id)
            except Exception as e:
                messages.error(request, f"Erro ao adicionar equipamento: {str(e)}")
    
    # Get all manufactured equipment for the form
    equipamentos_fabricados = EquipamentoFabricado.objects.all().order_by('modelo')
    
    # Get all clients for the form if no client was specified
    clientes = None
    if not cliente:
        clientes = Cliente.objects.all().order_by('nome')
    
    context = {
        'equipamentos_fabricados': equipamentos_fabricados,
        'cliente': cliente,
        'clientes': clientes,
        'next': request.GET.get('next', '')
    }
    
    return render(request, 'equipamentos/adicionar_equipamento_cliente.html', context)

@login_required
@group_required(['Administradores', 'Técnicos'])
def detalhes_equipamento_cliente(request, equipamento_id):
    """View for client equipment details"""
    equipamento = get_object_or_404(EquipamentoCliente, id=equipamento_id)
    
    # Fetch associated service requests
    assistencias = PedidoAssistencia.objects.filter(equipamento=equipamento).order_by('-data_entrada')
    
    # Fetch associated notes
    try:
        notas = Nota.objects.filter(equipamento=equipamento).order_by('-data_criacao')
    except Exception:
        notas = []
    
    # Breadcrumbs
    breadcrumbs = [
        {'title': 'Equipamentos', 'url': reverse('equipamentos:listar_equipamentos')},
        {'title': 'Equipamento de Cliente', 'url': None},
    ]
    
    return render(request, 'equipamentos/detalhes_equipamento_cliente.html', {
        'equipamento': equipamento,
        'assistencias': assistencias,
        'notas': notas,
        'breadcrumbs': breadcrumbs,
    })

@login_required
@group_required(['Administradores', 'Técnicos'])
def editar_equipamento_cliente(request, equipamento_id):
    """View to edit client equipment"""
    equipamento = get_object_or_404(EquipamentoCliente, id=equipamento_id)
    
    if request.method == 'POST':
        # Process form data
        numero_serie = request.POST.get('numero_serie')
        data_instalacao = request.POST.get('data_instalacao')
        observacoes = request.POST.get('observacoes')
        
        # Validation
        if not numero_serie:
            messages.error(request, "O número de série é obrigatório.")
        else:
            try:
                # Update client equipment
                equipamento.numero_serie = numero_serie
                equipamento.data_instalacao = data_instalacao
                equipamento.observacoes = observacoes
                equipamento.save()
                
                messages.success(request, "Equipamento atualizado com sucesso!")
                return redirect('equipamentos:detalhes_cliente', equipamento_id=equipamento.id)
            except Exception as e:
                messages.error(request, f"Erro ao atualizar equipamento: {str(e)}")
    
    # Breadcrumbs
    breadcrumbs = [
        {'title': 'Equipamentos', 'url': reverse('equipamentos:listar_equipamentos')},
        {'title': f'Equipamento: {equipamento.equipamento_fabricado.modelo}', 
         'url': reverse('equipamentos:detalhes_cliente', args=[equipamento.id])},
        {'title': 'Editar', 'url': None},
    ]
    
    return render(request, 'equipamentos/editar_equipamento_cliente.html', {
        'equipamento': equipamento,
        'breadcrumbs': breadcrumbs,
    })

@login_required
@group_required(['Administradores', 'Técnicos'])
def excluir_equipamento_cliente(request, equipamento_id):
    """View to delete client equipment"""
    equipamento = get_object_or_404(EquipamentoCliente, id=equipamento_id)
    
    if request.method == 'POST':
        try:
            cliente_id = equipamento.cliente.id
            equipamento.delete()
            messages.success(request, "Equipamento removido com sucesso!")
            
            # Redirect to client equipment page if came from there
            if 'from_client' in request.GET:
                return redirect('clientes:cliente_equipamentos', cliente_id=cliente_id)
            return redirect('equipamentos:listar_cliente')
        except Exception as e:
            messages.error(request, f"Erro ao excluir equipamento: {str(e)}")
            return redirect('equipamentos:detalhes_cliente', equipamento_id=equipamento_id)
    
    return render(request, 'equipamentos/excluir_equipamento_cliente.html', {
        'equipamento': equipamento,
    })

@login_required
@group_required(['Administradores', 'Técnicos'])
def detalhes_categoria(request, categoria_id):
    """View for category details"""
    categoria = get_object_or_404(CategoriaEquipamento, id=categoria_id)
    equipamentos = EquipamentoFabricado.objects.filter(categoria=categoria)
    
    return render(request, 'equipamentos/detalhes_categoria.html', {
        'categoria': categoria,
        'equipamentos': equipamentos,
    })

@login_required
@group_required(['Administradores', 'Técnicos'])
def editar_categoria(request, categoria_id):
    """View to edit category"""
    categoria = get_object_or_404(CategoriaEquipamento, id=categoria_id)
    
    if request.method == 'POST':
        form = CategoriaEquipamentoForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoria atualizada com sucesso!")
            return redirect('equipamentos:detalhes_categoria', categoria_id=categoria.id)
    else:
        form = CategoriaEquipamentoForm(instance=categoria)
    
    return render(request, 'equipamentos/editar_categoria.html', {
        'form': form,
        'categoria': categoria,
    })

@login_required
@group_required(['Administradores', 'Técnicos'])
def excluir_categoria(request, categoria_id):
    """View to delete category"""
    categoria = get_object_or_404(CategoriaEquipamento, id=categoria_id)
    
    if request.method == 'POST':
        try:
            categoria.delete()
            messages.success(request, "Categoria excluída com sucesso!")
            return redirect('equipamentos:listar_categorias')
        except Exception as e:
            messages.error(request, f"Erro ao excluir categoria: {str(e)}")
            return redirect('equipamentos:detalhes_categoria', categoria_id=categoria_id)
    
    return render(request, 'equipamentos/excluir_categoria.html', {
        'categoria': categoria,
    })