from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.translation import gettext as _  # Add this import
from .models import EquipamentoFabricado, DocumentoEquipamento, CategoriaEquipamento, EquipamentoCliente
from .forms import EquipamentoFabricadoForm, CategoriaEquipamentoForm
from clientes.models import Cliente
from assistencia.models import PedidoAssistencia
from notas.models import Nota
from django.views.decorators.http import require_http_methods, require_POST
from django.core.exceptions import ValidationError, FieldError
from django.db.models import Q
from core.utils import group_required
from core.search import AdvancedSearch, normalize_text  # Import normalize_text
from django.urls import reverse
from django.contrib import messages
import unicodedata
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import os
print(f"Loading views.py from: {os.path.abspath(__file__)}")

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
    sort_by = request.GET.get('sort', 'nome')
    sort_dir = request.GET.get('sort_dir', 'asc')

    equipamentos = EquipamentoFabricado.objects.all()

    # Apply search filters if provided
    if search_query:
        # Always normalize the search query to remove accents
        normalized_query = normalize_text(search_query)

        # First try standard database search using direct query
        db_results = equipamentos.filter(
            Q(nome__icontains=search_query) |
            Q(referencia_interna__icontains=search_query) |
            Q(descricao__icontains=search_query)
        )

        # Then do a manual search to catch accent differences
        matching_ids = set()

        # Add results from standard DB query
        for eq in db_results:
            matching_ids.add(eq.id)

        # Get ALL items and manually filter them with normalized text
        if normalized_query:  # Only do this expensive operation if we have a query
            for eq in equipamentos:
                if (normalized_query in normalize_text(eq.nome) or
                    normalized_query in normalize_text(str(eq.referencia_interna or "")) or
                    normalized_query in normalize_text(str(eq.descricao or ""))):
                    matching_ids.add(eq.id)

        # Now filter the queryset to include only matches
        if matching_ids:
            equipamentos = equipamentos.filter(id__in=matching_ids)
        else:
            equipamentos = EquipamentoFabricado.objects.none()

    # Convert categoria_id to string to make template comparison easier
    if categoria_id:
        categoria_id = str(categoria_id)
        equipamentos = equipamentos.filter(categoria_id=categoria_id)

    # Apply sorting with direction
    if sort_dir == 'desc':
        sort_by = f"-{sort_by}"
    equipamentos = equipamentos.order_by(sort_by)

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

    # Let's modify our approach by not using complex template conditionals
    # Instead, create a dict of "selected" flags
    selected = {
        'nome': 'selected' if sort_by == 'nome' else '',
        'nome_reversed': 'selected' if sort_by == '-nome' else '',
        'data_lancamento': 'selected' if sort_by == 'data_lancamento' else '',
        'data_lancamento_reversed': 'selected' if sort_by == '-data_lancamento' else '',
    }

    context = {
        'equipamentos_fabricados': equipamentos,  # Changed from 'equipamentos' to match the template variable name
        'search_query': search_query,
        'normalized_query': normalize_text(search_query) if search_query else '',
        'categoria_selecionada': categoria_id,
        'sort_by': sort_by.replace('-', '') if sort_by.startswith('-') else sort_by,
        'sort_dir': 'desc' if sort_by.startswith('-') else 'asc',
        'categorias': categorias,
        'total_equipamentos': paginator.count,
        'active_tab': 'fabricados',
        'selected': selected,  # Add this to context
        'nav_active': 'fabricados'  # This is correct for mini_nav
    }

    # Change this line to use the new template
    return render(request, 'equipamentos/listar_fabricados.html', context)

@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def listar_equipamentos(request):
    """View to list all equipment (both manufactured and client equipment)"""
    # Get equipment data
    equipamentos_fabricados = EquipamentoFabricado.objects.all()
    equipamentos_cliente = EquipamentoCliente.objects.all()

    # Apply search filters if provided
    search_query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', 'nome')
    sort_dir = request.GET.get('sort_dir', 'asc')

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

    # Apply sorting to both sets of equipment
    if sort_dir == 'desc':
        equipamentos_fabricados = equipamentos_fabricados.order_by(f"-{sort_by}")
        # For client equipment, we need to adjust field names as needed
        client_sort_field = sort_by
        if sort_by in ['nome', 'referencia_interna', 'categoria__nome']:
            if sort_by == 'nome':
                client_sort_field = 'equipamento_fabricado__nome'
            elif sort_by == 'referencia_interna':
                client_sort_field = 'equipamento_fabricado__referencia_interna'
            elif sort_by == 'categoria__nome':
                client_sort_field = 'equipamento_fabricado__categoria__nome'
        equipamentos_cliente = equipamentos_cliente.order_by(f"-{client_sort_field}")
    else:
        equipamentos_fabricados = equipamentos_fabricados.order_by(sort_by)
        # Same adjustment for ascending sort
        client_sort_field = sort_by
        if sort_by in ['nome', 'referencia_interna', 'categoria__nome']:
            if sort_by == 'nome':
                client_sort_field = 'equipamento_fabricado__nome'
            elif sort_by == 'referencia_interna':
                client_sort_field = 'equipamento_fabricado__referencia_interna'
            elif sort_by == 'categoria__nome':
                client_sort_field = 'equipamento_fabricado__categoria__nome'
        equipamentos_cliente = equipamentos_cliente.order_by(client_sort_field)

    # Prepare context
    context = {
        'equipamentos_fabricados': equipamentos_fabricados,
        'equipamentos_cliente': equipamentos_cliente,
        'search_query': search_query,
        'active_tab': 'equipamentos',  # To highlight the correct tab in navigation
        'sort_by': sort_by.replace('-', '') if sort_by.startswith('-') else sort_by,
        'sort_dir': sort_dir,
        'nav_active': 'equipamentos'  # This is correct for mini_nav
    }

    return render(request, 'equipamentos/listar_equipamentos.html', context)

@login_required
@group_required(['Administradores', 'Técnicos'])
def adicionar_equipamento_fabricado(request):
    if request.method == 'POST':
        form = EquipamentoFabricadoForm(request.POST, request.FILES)
        if form.is_valid():
            equipamento = form.save()
            messages.success(request, _('Equipamento adicionado com sucesso!'))
            return redirect('equipamentos:detalhes_fabricado', equipamento_id=equipamento.id)
    else:
        form = EquipamentoFabricadoForm()

    # Here's the correction: use 'listar_fabricados' instead of 'listar_equipamentos_fabricados'
    breadcrumbs = [
        {'title': _('Equipamentos'), 'url': reverse('equipamentos:listar_fabricados')},
        {'title': _('Adicionar Equipamento'), 'url': None}
    ]

    return render(request, 'equipamentos/adicionar_equipamento_fabricado.html', {
        'form': form,
        'breadcrumbs': breadcrumbs,
        'nav_active': 'adicionar'  # Add this to match mini_nav
    })

@login_required
@group_required(['Administradores', 'Técnicos'])
def detalhes_equipamento(request, equipamento_id):
    equipamento = get_object_or_404(EquipamentoFabricado, id=equipamento_id)
    equipamentos_cliente = EquipamentoCliente.objects.filter(equipamento_fabricado=equipamento)
    assistencias = PedidoAssistencia.objects.filter(equipamento__in=equipamentos_cliente).order_by('-data_entrada')

    # Fetch documents related to this equipment
    documentos = DocumentoEquipamento.objects.filter(equipamento=equipamento)

    # Ajustar a consulta de notas
    try:
        notas = Nota.objects.filter(equipamento_fabricado=equipamento).order_by('-data_criacao')
    except FieldError:
        # Alternativa: se a relação for com o equipamento do cliente
        notas = Nota.objects.filter(equipamento__in=equipamentos_cliente).order_by('-data_criacao')

    # Updated breadcrumbs with correct URL name
    breadcrumbs = [
        {'title': _('Equipamentos'), 'url': reverse('equipamentos:listar_fabricados')},
        {'title': f"Equipamento {equipamento.id}", 'url': None}
    ]

    return render(request, 'equipamentos/detalhes_equipamento.html', {
        'equipamento': equipamento,
        'equipamentos_cliente': equipamentos_cliente,
        'assistencias': assistencias,
        'notas': notas,
        'documentos': documentos,  # Pass documents to the template
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
                # Fix: Change detalhes_equipamento to detalhes_fabricado
                return redirect('equipamentos:detalhes_fabricado', equipamento_id=equipamento.id)
            except ValidationError as e:
                # Adicionar erros de validação ao formulário
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
                messages.error(request, "Erro ao atualizar equipamento. Verifique os campos destacados.")
    else:
        form = EquipamentoFabricadoForm(instance=equipamento)

    # Update breadcrumbs here too
    breadcrumbs = [
        {'title': _('Equipamentos'), 'url': reverse('equipamentos:listar_fabricados')},
        {'title': equipamento.nome, 'url': reverse('equipamentos:detalhes_fabricado', args=[equipamento.id])},
        {'title': _('Editar'), 'url': None}
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
        return JsonResponse({
            'success': True,
            'documento_id': documento.id,
            'documento_url': documento.arquivo.url,
            'excluir_url': reverse('equipamentos:excluir_documento', args=[documento.id])
        })
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

@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def listar_categorias(request):
    """View to list all equipment categories with enhanced features"""
    # Get search query, sort, and filter parameters
    search_query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', 'nome')
    sort_dir = request.GET.get('sort_dir', 'asc')
    only_active = request.GET.get('only_active', 'true') == 'true'
    parent_id = request.GET.get('parent', '')

    # Start with all categories
    categorias = CategoriaEquipamento.objects.all()

    # Apply search filter if provided
    if search_query:
        categorias = categorias.filter(
            Q(nome__icontains=search_query) |
            Q(descricao__icontains=search_query)
        )

    # Filter by parent category - IMPROVED
    if parent_id:
        if parent_id == 'root':
            categorias = categorias.filter(pai__isnull=True)
        else:
            try:
                # First try direct filtering by ID (if it's numeric)
                categorias = categorias.filter(pai_id=parent_id)
            except Exception:
                # If that fails, try name-based lookup (more flexible)
                try:
                    pai = CategoriaEquipamento.objects.filter(nome__iexact=parent_id).first()
                    if pai:
                        categorias = categorias.filter(pai=pai)
                except Exception:
                    pass  # If all filter attempts fail, keep the original queryset

    # Annotate with equipment count for all categories
    from django.db.models import Count
    categorias = categorias.annotate(equipment_count=Count('equipamentofabricado'))

    # Apply sorting with direction
    if sort_by == 'nome':
        categorias = categorias.order_by(f"{'-' if sort_dir == 'desc' else ''}nome")
    elif sort_by == 'equipment_count':
        categorias = categorias.order_by(f"{'-' if sort_dir == 'desc' else ''}equipment_count")
    elif sort_by == 'nivel':
        # For level, we sort by parent name first then category name
        if sort_dir == 'desc':
            categorias = categorias.order_by('-pai__nome', '-nome')
        else:
            categorias = categorias.order_by('pai__nome', 'nome')

    # Get all categories for the parent filter dropdown
    all_categorias = CategoriaEquipamento.objects.all().order_by('nome')

    # PRE-CALCULATE ALL ATTRIBUTES FOR THE TEMPLATE
    # This eliminates the need for conditionals in the template

    # Parent filter options with selected state
    parent_options = [
        {'value': '', 'text': 'Todas as Categorias', 'selected': 'selected' if parent_id == '' else ''},
        {'value': 'root', 'text': 'Apenas Categorias Raiz', 'selected': 'selected' if parent_id == 'root' else ''}
    ]

    # Category options with selected state
    category_options = []
    for cat in all_categorias:
        category_options.append({
            'id': cat.id,
            'nome': cat.nome,
            'selected': 'selected' if str(cat.id) == parent_id else ''
        })

    # Checkbox state
    only_active_checked = 'checked' if only_active else ''

    return render(request, 'equipamentos/lista_categorias.html', {
        'categorias': categorias,
        'all_categorias': all_categorias,
        'search_query': search_query,
        'sort_by': sort_by,
        'sort_dir': sort_dir,
        'only_active': only_active,
        'parent_id': parent_id,
        'total_count': categorias.count(),
        # Pre-calculated elements
        'parent_options': parent_options,
        'category_options': category_options,
        'only_active_checked': only_active_checked,
        # Add view_title for breadcrumbs
        'view_title': 'Categorias',
        'nav_active': 'categorias'  # Add this to match mini_nav
    })

@login_required
@group_required(['Administradores', 'Comerciais'])
def adicionar_categoria(request):
    from .forms import CategoriaEquipamentoForm
    if request.method == "POST":
        form = CategoriaEquipamentoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('equipamentos:listar_categorias')
    else:
        form = CategoriaEquipamentoForm()
    return render(request, 'equipamentos/adicionar_categoria.html', {
        'form': form,
        'view_title': 'Adicionar Categoria'  # Added for breadcrumbs
    })

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

    # Buscar histórico de pedidos de assistência para este equipamento
    numero_serie = equipamento.numero_serie
    historico_pats = PedidoAssistencia.objects.filter(
        Q(equipamento=equipamento) |
        Q(numero_serie_equipamento=numero_serie)
    ).order_by('-data_criacao').distinct()

    # Buscar histórico de mudanças no objeto (usando simple_history)
    historico_mudancas = equipamento.history.all()

    # Buscar histórico de transferências
    historico_transferencias = equipamento.transfer_history.all()

    # Buscar notas relacionadas a este equipamento
    try:
        notas = Nota.objects.filter(equipamento=equipamento).order_by('-data_criacao')
    except Exception:
        notas = []

    # Configurar breadcrumbs
    breadcrumbs = [
        {'title': 'Equipamentos', 'url': reverse('equipamentos:listar_cliente')},
        {'title': f'{equipamento.equipamento_fabricado.nome}',
         'url': reverse('equipamentos:detalhes_cliente', args=[equipamento.id])},
        {'title': f'Histórico (S/N: {equipamento.numero_serie})'}
    ]

    context = {
        'equipamento': equipamento,
        'historico_pats': historico_pats,
        'historico_mudancas': historico_mudancas,
        'historico_transferencias': historico_transferencias,
        'notas': notas,
        'breadcrumbs': breadcrumbs,
        'active_tab': active_tab
    }

    return render(request, 'equipamentos/historico_equipamento.html', context)

@login_required
def transferir_equipamento(request, equipamento_id):
    """Transfere um equipamento de um cliente para outro, mantendo o histórico"""
    equipamento = get_object_or_404(EquipamentoCliente, id=equipamento_id)
    pats_abertas = PedidoAssistencia.objects.filter(
        equipamento=equipamento,
        estado__in=['aberto', 'em_andamento', 'em_diagnostico', 'em_curso']
    )
    if request.method == 'POST':
        novo_cliente_id = request.POST.get('novo_cliente_id')
        data_transferencia = request.POST.get('data_transferencia')
        motivo = request.POST.get('motivo', '')
        fechar_pats = request.POST.get('fechar_pats') == 'on'

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
    equipamento_fabricado_id = request.GET.get('equipamento_fabricado')
    cliente = None
    equipamento_fabricado = None

    if cliente_id:
        cliente = get_object_or_404(Cliente, id=cliente_id)
    if equipamento_fabricado_id:
        equipamento_fabricado = get_object_or_404(EquipamentoFabricado, id=equipamento_fabricado_id)

    if request.method == 'POST':
        # Process form data - improved debugging
        post_equipamento_id = request.POST.get('equipamento_fabricado')
        post_cliente_id = request.POST.get('cliente_id')
        numero_serie = request.POST.get('numero_serie')
        data_instalacao = request.POST.get('data_instalacao')
        observacoes = request.POST.get('observacoes')

        # Use the ID that was provided either in POST data or from GET parameters
        equipamento_fabricado_id = post_equipamento_id or equipamento_fabricado_id
        cliente_id = post_cliente_id or cliente_id

        # Validation with explicit error messages
        if not equipamento_fabricado_id:
            messages.error(request, "Por favor selecione um modelo de equipamento.")
            return render(request, 'equipamentos/adicionar_equipamento_cliente.html', {
                'equipamentos_fabricados': EquipamentoFabricado.objects.all().order_by('nome'),
                'equipamento_fabricado_preselected': equipamento_fabricado,
                'cliente': cliente,
                'clientes': None if cliente else Cliente.objects.all().order_by('nome'),
                'next': request.GET.get('next', '')
            })
        if not cliente_id:
            messages.error(request, "Por favor selecione um cliente.")
            return render(request, 'equipamentos/adicionar_equipamento_cliente.html', {
                'equipamentos_fabricados': EquipamentoFabricado.objects.all().order_by('nome'),
                'equipamento_fabricado_preselected': equipamento_fabricado,
                'cliente': cliente,
                'clientes': None if cliente else Cliente.objects.all().order_by('nome'),
                'next': request.GET.get('next', '')
            })
        if not numero_serie:
            messages.error(request, "Por favor informe o número de série.")
            return render(request, 'equipamentos/adicionar_equipamento_cliente.html', {
                'equipamentos_fabricados': EquipamentoFabricado.objects.all().order_by('nome'),
                'equipamento_fabricado_preselected': equipamento_fabricado,
                'cliente': cliente,
                'clientes': None if cliente else Cliente.objects.all().order_by('nome'),
                'next': request.GET.get('next', '')
            })

        try:
            # Create new client equipment - FIX: only set fields that exist in the model
            equipamento_fabricado = get_object_or_404(EquipamentoFabricado, id=equipamento_fabricado_id)
            cliente = get_object_or_404(Cliente, id=cliente_id)

            # First create with required fields only
            equipamento = EquipamentoCliente.objects.create(
                equipamento_fabricado=equipamento_fabricado,
                cliente=cliente,
                numero_serie=numero_serie
            )

            # Then try to set optional fields if they exist on the model
            try:
                if data_instalacao:
                    equipamento.data_instalacao = data_instalacao
                if observacoes:
                    equipamento.observacoes = observacoes
                equipamento.save()
            except Exception as field_error:
                # If setting optional fields fails, just log the error but continue
                print(f"WARNING: Could not set optional fields: {str(field_error)}")

            messages.success(request, f"Equipamento '{equipamento_fabricado.nome}' adicionado ao cliente '{cliente.nome}' com sucesso!")

            # Redirect based on source
            if 'next' in request.GET and request.GET.get('next'):
                return redirect(request.GET.get('next'))
            elif equipamento_fabricado_id and not post_cliente_id:
                # If came from equipment page, go back to equipment details
                return redirect('equipamentos:detalhes_fabricado', equipamento_id=equipamento_fabricado.id)
            elif cliente_id and not post_equipamento_id:
                # If came from client page, go back to client details
                return redirect('clientes:detalhes_cliente', cliente_id=cliente.id)
            else:
                # Default: redirect to equipment list
                return redirect('equipamentos:listar_cliente')

        except Exception as e:
            messages.error(request, f"Erro ao adicionar equipamento: {str(e)}")
            # Print the error for debugging
            import traceback
            print(f"ERROR: {str(e)}")
            print(traceback.format_exc())

    # Get all manufactured equipment for the form - make sure we use the correct field name
    equipamentos_fabricados = EquipamentoFabricado.objects.all().order_by('nome')

    # Get all clients for the form if no client was specified
    clientes = None
    if not cliente:
        clientes = Cliente.objects.all().order_by('nome')

    context = {
        'equipamentos_fabricados': equipamentos_fabricados,
        'equipamento_fabricado_preselected': equipamento_fabricado,
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

    # Update this line to use categoria_id instead of the categoria object
    equipamentos = EquipamentoFabricado.objects.filter(categoria_id=categoria.id)

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
        'view_title': 'Editar Categoria'  # Added for breadcrumbs
    })

# Fix the excluir_categoria view to properly handle POST requests
@login_required
@group_required(['Administradores', 'Técnicos'])
def excluir_categoria(request, categoria_id):
    """View to delete category"""
    categoria = get_object_or_404(CategoriaEquipamento, id=categoria_id)

    # Get equipment count for user feedback
    equipamentos_count = EquipamentoFabricado.objects.filter(categoria_id=categoria.id).count()

    # Handle POST request for deletion
    if request.method == 'POST':
        try:
            nome_categoria = categoria.nome
            categoria.delete()
            if equipamentos_count > 0 and equipamentos_count < 10:  # Make sure this is "and" not "e"
                messages.success(request, f"Categoria '{nome_categoria}' excluída com sucesso! {equipamentos_count} equipamento(s) foram desassociados da categoria.")
            else:
                messages.success(request, f"Categoria '{nome_categoria}' excluída com sucesso!")
            # Make sure to redirect to the category listing
            return redirect('equipamentos:listar_categorias')
        except Exception as e:
            messages.error(request, f"Erro ao excluir categoria: {str(e)}")
            return redirect('equipamentos:detalhes_categoria', categoria_id=categoria_id)

    # For GET requests, show the confirmation page
    return render(request, 'equipamentos/excluir_categoria.html', {
        'categoria': categoria,
        'equipamentos_count': equipamentos_count,
    })

@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def exportar_equipamentos_fabricados(request):
    """Export manufactured equipment to various formats (Excel, CSV, PDF)"""
    formato = request.GET.get('formato', 'excel')

    # In a real implementation, this would generate the requested file format
    # For now, we'll just return a placeholder message
    response = HttpResponse(f"Exportação de equipamentos em formato {formato} (função a ser implementada)")

    # In a real implementation, headers would be set based on the file type
    # response['Content-Disposition'] = f'attachment; filename="equipamentos_fabricados.{formato}"'

    return response

@login_required
def api_equipamentos_cliente(request, cliente_id):
    """
    API endpoint to get equipment for a specific client.
    Used for AJAX requests to dynamically load client equipment.
    """
    try:
        # Debug log
        print(f"API request received for client ID: {cliente_id}")

        # Validate client_id is a positive integer
        try:
            cliente_id = int(cliente_id)
            if cliente_id <= 0:
                return JsonResponse({'error': 'Invalid client ID'}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Client ID must be an integer'}, status=400)

        # Get the client
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return JsonResponse({'error': f'Client with ID {cliente_id} not found'}, status=404)

        # Get client's equipment
        equipamentos = EquipamentoCliente.objects.filter(cliente=cliente)
        print(f"Found {equipamentos.count()} equipments for client {cliente_id}")

        # Format data for response
        equipamentos_data = []
        for eq in equipamentos:
            try:
                equipamentos_data.append({
                    'id': eq.id,
                    'nome': str(eq.equipamento_fabricado.nome) if hasattr(eq.equipamento_fabricado, 'nome') else 'Unknown',
                    'numero_serie': eq.numero_serie or '',
                    'modelo': str(eq.equipamento_fabricado) if eq.equipamento_fabricado else 'Unknown',
                })
            except Exception as item_error:
                print(f"Error processing equipment {eq.id}: {str(item_error)}")
                # Skip this item but continue with others
                continue

        return JsonResponse(equipamentos_data, safe=False)

    except Exception as e:
        import traceback
        print(f"Error in api_equipamentos_cliente: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)

@login_required
def api_equipamento_by_serial(request, numero_serie):
    """
    API endpoint to find equipment by serial number.
    Returns equipment details and its client if found.
    """
    try:
        # Debug log
        print(f"API request received for serial number: {numero_serie}")

        if not numero_serie or len(numero_serie.strip()) == 0:
            return JsonResponse({'error': 'Serial number cannot be empty'}, status=400)

        # Search for equipment with this serial number
        equipamento = EquipamentoCliente.objects.filter(numero_serie__iexact=numero_serie.strip()).first()

        if equipamento:
            # Return equipment and client details
            return JsonResponse({
                'found': True,
                'equipamento_id': equipamento.id,
                'equipamento_nome': str(equipamento.equipamento_fabricado.nome) if hasattr(equipamento.equipamento_fabricado, 'nome') else 'Unknown',
                'cliente_id': equipamento.cliente.id,
                'cliente_nome': str(equipamento.cliente.nome) if hasattr(equipamento.cliente, 'nome') else 'Unknown',
            })
        else:
            # Not found but still a valid response
            return JsonResponse({'found': False})

    except Exception as e:
        import traceback
        print(f"Error in api_equipamento_by_serial: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)

@login_required
@group_required(['Administradores', 'Comerciais', 'Gestores de Clientes'])
def listar_equipamentos_cliente(request):
    """View to list client equipment with search functionality"""
    # Get search query if provided
    search_query = request.GET.get('q', '')
    cliente_id = request.GET.get('cliente', '')
    sort_by = request.GET.get('sort', 'cliente__nome')
    sort_dir = request.GET.get('sort_dir', 'asc')

    # Start with all equipment
    equipamentos = EquipamentoCliente.objects.select_related('cliente', 'equipamento_fabricado').all()

    # Apply search filters
    if search_query:
        normalized_query = normalize_text(search_query)

        # Standard database search
        db_results = equipamentos.filter(
            Q(numero_serie__icontains=search_query) |
            Q(cliente__nome__icontains=search_query) |
            Q(equipamento_fabricado__nome__icontains=search_query)
        )

        # Manual search for accent insensitivity
        matching_ids = set()

        # Add results from standard DB query
        for eq in db_results:
            matching_ids.add(eq.id)

        # Get all items and manually filter them with normalized text
        if normalized_query:  # Only do this expensive operation if we have a query
            for eq in equipamentos:
                if (normalized_query in normalize_text(eq.numero_serie) or
                    normalized_query in normalize_text(eq.cliente.nome) or
                    normalized_query in normalize_text(eq.equipamento_fabricado.nome)):
                    matching_ids.add(eq.id)

        # Filter the queryset to include only matches
        if matching_ids:
            equipamentos = equipamentos.filter(id__in=matching_ids)
        else:
            equipamentos = EquipamentoCliente.objects.none()

    # Filter by client if specified
    if cliente_id:
        equipamentos = equipamentos.filter(cliente_id=cliente_id)

    # Apply sorting with direction
    if sort_dir == 'desc':
        sort_by = f"-{sort_by}"
    equipamentos = equipamentos.order_by(sort_by)

    # Add breadcrumbs
    breadcrumbs = [
        {'title': ('Equipamentos de Clientes'), 'url': None}
    ]

    # Pagination
    paginator = Paginator(equipamentos, 20)  # Show 20 items per page
    page = request.GET.get('pagina', 1)

    try:
        equipamentos = paginator.page(page)
    except PageNotAnInteger:
        equipamentos = paginator.page(1)
    except EmptyPage:
        equipamentos = paginator.page(paginator.num_pages)

    # Get all clients and precompute which one is selected
    all_clientes = Cliente.objects.all().order_by('nome')
    selected_clients = {str(c.id): "selected" if str(c.id) == cliente_id else "" for c in all_clientes}

    return render(request, 'equipamentos/listar_equipamentos_cliente.html', {
        'equipamentos': equipamentos,
        'search_query': search_query,
        'cliente_id': cliente_id,
        'breadcrumbs': breadcrumbs,
        'clientes': all_clientes,
        'selected_clients': selected_clients,  # Add this dictionary of precomputed selections
        'total_count': paginator.count,
        'sort_by': sort_by.replace('-', '') if sort_by.startswith('-') else sort_by,
        'sort_dir': 'desc' if sort_by.startswith('-') else 'asc',
    })

@require_POST
@login_required
@group_required(['Administradores', 'Técnicos'])
def bulk_categorias(request):
    """Handle bulk actions for categories via AJAX"""
    action = request.POST.get('action')

    # Debug information
    print(f"Bulk action requested: {action}")
    print(f"Request POST data: {request.POST}")

    # Handle multiple IDs from various possible formats
    selected_ids = []

    # Try to get from ids[] array format
    ids_array = request.POST.getlist('ids[]')
    if ids_array:
        selected_ids = ids_array
        print(f"Found IDs in array format: {selected_ids}")

    # If empty, try from comma-separated string
    if not selected_ids:
        ids_string = request.POST.get('ids', '')
        if ids_string:
            selected_ids = [id_str.strip() for id_str in ids_string.split(',') if id_str.strip()]
            print(f"Found IDs in string format: {selected_ids}")

    # Make sure all IDs are valid integers
    valid_ids = []
    for id_str in selected_ids:
        try:
            valid_ids.append(int(id_str))
        except (ValueError, TypeError):
            continue

    print(f"Valid IDs for processing: {valid_ids}")

    if not valid_ids:
        return JsonResponse({
            'success': False,
            'message': 'Nenhuma categoria válida selecionada.'
        })

    try:
        # Query for categories to delete
        selected_categories = CategoriaEquipamento.objects.filter(id__in=valid_ids)
        count = selected_categories.count()
        print(f"Found {count} categories to process")

        if count == 0:
            return JsonResponse({
                'success': False,
                'message': 'Nenhuma categoria encontrada com os IDs fornecidos.'
            })

        if action == 'delete':
            deleted_count = 0
            errors = []

            for categoria in selected_categories:
                try:
                    print(f"Attempting to delete category: {categoria.id} - {categoria.nome}")
                    categoria.delete()
                    deleted_count += 1
                except Exception as e:
                    errors.append(f"Erro ao excluir categoria {categoria.nome}: {str(e)}")
                    print(f"Error deleting category {categoria.id}: {str(e)}")

            result = {
                'success': deleted_count > 0,
                'message': f'{deleted_count} categoria(s) excluída(s) com sucesso!'
            }

            if errors:
                result['errors'] = errors
                if deleted_count == 0:
                    result['message'] = "Não foi possível excluir as categorias selecionadas."
                else:
                    result['message'] += f" ({len(errors)} categorias não puderam ser excluídas)"

            return JsonResponse(result)
        else:
            return JsonResponse({
                'success': False,
                'message': f'Ação "{action}" não é suportada.'
            })
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in bulk_categorias: {str(e)}")
        print(error_details)
        return JsonResponse({
            'success': False,
            'message': f'Erro ao processar solicitação: {str(e)}'
        })

@login_required
def debug_templates(request):
    """Debug view to list template locations"""
    from django.conf import settings
    templates = []

    # List all template directories
    for template_dir in settings.TEMPLATES[0]['DIRS']:
        if os.path.exists(template_dir):
            templates.append(f"Template directory exists: {template_dir}")
        else:
            templates.append(f"Template directory DOES NOT exist: {template_dir}")

    # Check for the specific template
    template_path = os.path.join(settings.BASE_DIR, 'equipamentos/templates/equipamentos/lista_categorias.html')
    if os.path.exists(template_path):
        templates.append(f"Template exists at: {template_path}")
    else:
        templates.append(f"Template DOES NOT exist at: {template_path}")

    # List modified date
    if os.path.exists(template_path):
        modified_time = os.path.getmtime(template_path)
        import datetime
        templates.append(f"Template last modified: {datetime.datetime.fromtimestamp(modified_time)}")

    return HttpResponse("<br>".join(templates))