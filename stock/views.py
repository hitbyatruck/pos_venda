from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.urls import reverse
from datetime import datetime, timedelta
import csv
import io
import json
import os
import pandas as pd
from io import BytesIO



from .models import (
    Peca, CategoriaPeca, Fornecedor, FornecedorPeca,
    EncomendaPeca, ItemEncomenda, MovimentacaoStock, HistoricoPrecoFornecedor
)

# Importar forms (serão definidos em forms.py)
from .forms import (
    PecaForm, CategoriaForm, FornecedorForm, FornecedorPecaForm,
    EncomendaPecaForm, ItemEncomendaForm, MovimentacaoStockForm
)

# Utilidades e decoradores
from core.utils import group_required

# Pacotes externos para importação/exportação
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# ===========================================
# DASHBOARD E PÁGINAS PRINCIPAIS
# ===========================================

@login_required
def dashboard_stock(request):
    """
    Dashboard principal do módulo de stock
    """
    # Estatísticas rápidas
    total_pecas = Peca.objects.count()
    pecas_sem_stock = Peca.objects.filter(stock_atual=0).count()
    
    # Peças com baixo stock (abaixo do mínimo, mas não zero)
    pecas_baixo_stock = Peca.objects.filter(
        stock_atual__lt=models.F('stock_minimo'),
        stock_atual__gt=0
    ).count()
    
    # Lista de peças com baixo stock para exibir na tabela
    pecas_baixo_stock_lista = Peca.objects.filter(
        stock_atual__lt=models.F('stock_minimo'),
        stock_atual__gt=0
    ).order_by('stock_atual')[:5]
    
    # Movimentações recentes
    movimentacoes_recentes = MovimentacaoStock.objects.all().select_related(
        'peca', 'utilizador'
    ).order_by('-data_movimentacao')[:5]
    
    # Encomendas pendentes (lista para iterar no template)
    # Aqui está o problema - era apenas um contador, mas precisamos da lista completa
    encomendas_pendentes_lista = EncomendaPeca.objects.filter(
        status__in=['pendente', 'encomendada', 'parcial']
    ).select_related('fornecedor').order_by('data_encomenda')[:5]
    
    # Contador de encomendas pendentes
    total_encomendas_pendentes = EncomendaPeca.objects.filter(
        status__in=['pendente', 'encomendada', 'parcial']
    ).count()
    
    # Peças mais utilizadas (últimos 30 dias)
    data_limite = timezone.now() - timezone.timedelta(days=30)
    pecas_populares = MovimentacaoStock.objects.filter(
        tipo='saida',
        data_movimentacao__gte=data_limite
    ).values('peca').annotate(
        total_saidas=models.Sum('quantidade')
    ).order_by('-total_saidas')[:5]
    
    # Enriquecer os dados de peças populares
    for item in pecas_populares:
        item['peca'] = Peca.objects.get(id=item['peca'])
    
    return render(request, 'stock/dashboard_stock.html', {
        'total_pecas': total_pecas,
        'pecas_sem_stock': pecas_sem_stock,
        'pecas_baixo_stock': pecas_baixo_stock,
        'pecas_baixo_stock_lista': pecas_baixo_stock_lista,
        'movimentacoes_recentes': movimentacoes_recentes,
        'encomendas_pendentes': encomendas_pendentes_lista,  # Agora é uma lista, não um contador
        'total_encomendas_pendentes': total_encomendas_pendentes,
        'pecas_populares': pecas_populares,
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def configuracoes_stock(request):
    """
    Página de configurações para o módulo de stock
    """
    # Carregar configurações atuais (se existirem)
    # Exemplo: configs = ConfiguracoesStock.objects.first()
    
    if request.method == 'POST':
        # Processar formulário de configurações
        # Exemplo: form = ConfiguracoesStockForm(request.POST, instance=configs)
        # if form.is_valid():
        #     form.save()
        #     messages.success(request, _('Configurações guardadas com sucesso.'))
        
        # Por enquanto, apenas mostrar mensagem
        messages.success(request, _('Configurações atualizadas com sucesso.'))
        return redirect('stock/dashboard_stock')
    else:
        # Criar formulário com configurações atuais
        # Exemplo: form = ConfiguracoesStockForm(instance=configs)
        form = None  # Temporário até criar o formulário real
    
    return render(request, 'stock/configuracoes_stock.html', {
        'form': form,
    })

# ===========================================
# GESTÃO DE PEÇAS
# ===========================================

@login_required
def listar_pecas(request):
    """
    Lista todas as peças com filtros e paginação
    """
    # Parâmetros de filtro
    categoria_id = request.GET.get('categoria', '')
    stock_status = request.GET.get('stock', '')
    searchterm = request.GET.get('q', '').strip()
    ordem = request.GET.get('ordem', 'codigo')
    
    # Query base
    pecas = Peca.objects.all()
    
    # Aplicar filtros
    if categoria_id and categoria_id.isdigit():
        pecas = pecas.filter(categoria_id=categoria_id)
    
    if stock_status:
        if stock_status == 'baixo':
            pecas = pecas.filter(stock_atual__lt=models.F('stock_minimo'))
        elif stock_status == 'zerado':
            pecas = pecas.filter(stock_atual=0)
        elif stock_status == 'ok':
            pecas = pecas.filter(
                stock_atual__gte=models.F('stock_minimo')
            )
    
    if searchterm:
        pecas = pecas.filter(
            models.Q(codigo__icontains=searchterm) | 
            models.Q(nome__icontains=searchterm) | 
            models.Q(descricao__icontains=searchterm)
        )
    
    # Ordenação
    if ordem.startswith('-'):
        pecas = pecas.order_by(ordem)
    else:
        pecas = pecas.order_by(ordem)
    
    # Paginação
    paginator = Paginator(pecas, 25)  # 25 peças por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Categorias para o filtro
    categorias = CategoriaPeca.objects.all().order_by('nome')
    
    return render(request, 'stock/listar_pecas.html', {
        'page_obj': page_obj,
        'categorias': categorias,
        'filtros': {
            'categoria': categoria_id,
            'stock': stock_status,
            'q': searchterm,
            'ordem': ordem
        },
        'total_resultados': paginator.count
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def pecas_baixo_stock(request):
    """
    Exibe a lista de peças com stock abaixo do nível mínimo
    """
    # Encontrar peças com stock abaixo do mínimo
    pecas_baixo_stock = Peca.objects.filter(
        stock_atual__lt=models.F('stock_minimo')
    ).order_by('stock_atual')
    
    # Encontrar peças com stock zero
    pecas_esgotadas = Peca.objects.filter(stock_atual=0).order_by('codigo')
    
    # Encontrar peças abaixo do nível ideal, mas acima do mínimo
    pecas_atencao = Peca.objects.filter(
        stock_atual__gte=models.F('stock_minimo'),
        stock_atual__lt=models.F('stock_ideal')
    ).order_by('stock_atual')
    
    return render(request, 'stock/pecas_baixo_stock.html', {
        'pecas_baixo_stock': pecas_baixo_stock,
        'pecas_esgotadas': pecas_esgotadas,
        'pecas_atencao': pecas_atencao,
        'total_baixo_stock': pecas_baixo_stock.count(),
        'total_esgotadas': pecas_esgotadas.count(),
        'total_atencao': pecas_atencao.count(),
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def adicionar_peca(request):
    if request.method == 'POST':
        form = PecaForm(request.POST)
        if form.is_valid():
            peca = form.save()
            messages.success(request, _('Peça adicionada com sucesso.'))
            return redirect('stock:detalhes_peca', peca_id=peca.id)
        else:
            # Depuração - imprimir erros no console
            print("ERROS DO FORMULÁRIO:", form.errors)
            messages.error(request, _('Corrija os erros abaixo.'))
    else:
        form = PecaForm()
    
    return render(request, 'stock/form_peca.html', {
        'form': form,
        'title': _('Adicionar Peça'),
        'is_new': True,
    })

@login_required
def detalhes_peca(request, peca_id):
    """
    Exibe os detalhes de uma peça específica
    """
    peca = get_object_or_404(Peca, id=peca_id)
    
    # Fornecedores desta peça
    fornecedores_peca = FornecedorPeca.objects.filter(
        peca=peca
    ).select_related('fornecedor').order_by('-fornecedor_preferencial', 'preco_unitario')
    
    # Movimentações recentes
    movimentacoes = MovimentacaoStock.objects.filter(
        peca=peca
    ).order_by('-data_movimentacao')[:15]
    
    # Equipamentos compatíveis
    equipamentos_compativeis = peca.compativel_com.all()
    
    # Encomendas pendentes
    itens_encomenda = ItemEncomenda.objects.filter(
        peca=peca,
        encomenda__status__in=['pendente', 'encomendada', 'parcial']
    ).select_related('encomenda', 'encomenda__fornecedor')
    
    return render(request, 'stock/detalhes_peca.html', {
        'peca': peca,
        'fornecedores_peca': fornecedores_peca,
        'movimentacoes': movimentacoes,
        'equipamentos_compativeis': equipamentos_compativeis,
        'itens_encomenda': itens_encomenda,
        'tem_fornecedor_preferencial': fornecedores_peca.filter(fornecedor_preferencial=True).exists()
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def editar_peca(request, peca_id):
    """
    Edita uma peça existente
    """
    peca = get_object_or_404(Peca, id=peca_id)
    
    if request.method == 'POST':
        form = PecaForm(request.POST, request.FILES, instance=peca)
        if form.is_valid():
            peca = form.save()
            messages.success(request, _(f'Peça "{peca.codigo}" atualizada com sucesso.'))
            return redirect('stock/detalhes_peca', peca_id=peca.id)
    else:
        form = PecaForm(instance=peca)
    
    return render(request, 'stock/editar_peca.html', {
        'form': form,
        'peca': peca,
        'categorias': CategoriaPeca.objects.all()
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def excluir_peca(request, peca_id):
    """
    Exclui uma peça existente se não houver dependências
    """
    peca = get_object_or_404(Peca, id=peca_id)
    
    # Verificar se há movimentações para esta peça
    tem_movimentacoes = MovimentacaoStock.objects.filter(peca=peca).exists()
    
    # Verificar se há itens de encomenda para esta peça
    tem_encomendas = ItemEncomenda.objects.filter(peca=peca).exists()
    
    # Verificar se tem stock atual
    tem_stock = peca.stock_atual > 0
    
    if request.method == 'POST':
        if tem_movimentacoes or tem_encomendas or tem_stock:
            messages.error(request, _('Não é possível excluir esta peça porque existem registos dependentes.'))
        else:
            codigo = peca.codigo  # Guardar para mensagem
            peca.delete()
            messages.success(request, _(f'Peça "{codigo}" excluída com sucesso.'))
            return redirect('stock/listar_pecas')
    
    return render(request, 'stock/excluir_peca.html', {
        'peca': peca,
        'tem_movimentacoes': tem_movimentacoes,
        'tem_encomendas': tem_encomendas,
        'tem_stock': tem_stock
    })

@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def registar_entrada(request):
    """
    Regista uma entrada de stock para uma peça específica
    """
    peca_id = request.GET.get('peca')
    
    initial = {}
    if peca_id:
        try:
            peca = Peca.objects.get(id=peca_id)
            initial['peca'] = peca
            initial['tipo'] = 'entrada'
        except Peca.DoesNotExist:
            messages.error(request, _('Peça não encontrada.'))
            return redirect('stock:listar_pecas')
    
    if request.method == 'POST':
        form = MovimentacaoStockForm(request.POST)
        if form.is_valid():
            movimentacao = form.save(commit=False)
            movimentacao.utilizador = request.user
            movimentacao.tipo = 'entrada'
            
            # Atualizar stock da peça
            peca = movimentacao.peca
            peca.stock_atual += movimentacao.quantidade
            peca.save()
            
            movimentacao.save()
            
            messages.success(request, _('Entrada de stock registada com sucesso.'))
            return redirect('stock:detalhes_peca', peca_id=peca.id)
    else:
        form = MovimentacaoStockForm(initial=initial)
    
    return render(request, 'stock/form_movimentacao.html', {
        'form': form,
        'title': _('Registar Entrada de Stock'),
        'tipo': 'entrada',
    })

@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def registar_saida(request):
    """
    Regista uma saída de stock para uma peça específica
    """
    peca_id = request.GET.get('peca')
    
    initial = {}
    if peca_id:
        try:
            peca = Peca.objects.get(id=peca_id)
            initial['peca'] = peca
            initial['tipo'] = 'saida'
        except Peca.DoesNotExist:
            messages.error(request, _('Peça não encontrada.'))
            return redirect('stock:listar_pecas')
    
    if request.method == 'POST':
        form = MovimentacaoStockForm(request.POST)
        if form.is_valid():
            movimentacao = form.save(commit=False)
            movimentacao.utilizador = request.user
            movimentacao.tipo = 'saida'
            
            # Verificar se há stock suficiente
            peca = movimentacao.peca
            if peca.stock_atual < movimentacao.quantidade:
                messages.error(request, _('Stock insuficiente. Existem apenas %(stock)s unidades disponíveis.') % {'stock': peca.stock_atual})
                return render(request, 'stock/form_movimentacao.html', {'form': form, 'title': _('Registar Saída de Stock'), 'tipo': 'saida'})
            
            # Atualizar stock da peça
            peca.stock_atual -= movimentacao.quantidade
            peca.save()
            
            movimentacao.save()
            
            messages.success(request, _('Saída de stock registada com sucesso.'))
            return redirect('stock:detalhes_peca', peca_id=peca.id)
    else:
        form = MovimentacaoStockForm(initial=initial)
    
    return render(request, 'stock/form_movimentacao.html', {
        'form': form,
        'title': _('Registar Saída de Stock'),
        'tipo': 'saida',
    })


# ===========================================
# GESTÃO DE CATEGORIAS
# ===========================================

@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def listar_categorias(request):
    """
    Lista todas as categorias de peças
    """
    # Obter todas as categorias
    categorias = CategoriaPeca.objects.all().order_by('nome')
    
    # Contar peças em cada categoria
    for categoria in categorias:
        categoria.total_pecas = Peca.objects.filter(categoria=categoria).count()
    
    return render(request, 'stock/listar_categorias.html', {
        'categorias': categorias,
        'total_categorias': categorias.count()
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def adicionar_categoria(request):
    """
    Adiciona uma nova categoria de peças
    """
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, _(f'Categoria "{categoria.nome}" adicionada com sucesso.'))
            
            # Redirecionar dependendo de onde veio
            next_url = request.POST.get('next', '')
            if next_url:
                return redirect(next_url)
            return redirect('stock/listar_categorias')
    else:
        form = CategoriaForm()
    
    return render(request, 'stock/adicionar_categoria.html', {
        'form': form,
        'next': request.GET.get('next', '')
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def editar_categoria(request, categoria_id):
    """
    Edita uma categoria existente
    """
    categoria = get_object_or_404(CategoriaPeca, id=categoria_id)
    
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, _(f'Categoria "{categoria.nome}" atualizada com sucesso.'))
            return redirect('stock/listar_categorias')
    else:
        form = CategoriaForm(instance=categoria)
    
    return render(request, 'stock/editar_categoria.html', {
        'form': form,
        'categoria': categoria
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def excluir_categoria(request, categoria_id):
    """
    Exclui uma categoria existente se não houver peças associadas
    """
    categoria = get_object_or_404(CategoriaPeca, id=categoria_id)
    
    # Verificar se há peças nesta categoria
    tem_pecas = Peca.objects.filter(categoria=categoria).exists()
    
    if request.method == 'POST':
        if tem_pecas:
            messages.error(request, _('Não é possível excluir esta categoria porque existem peças associadas.'))
        else:
            nome = categoria.nome  # Guardar para mensagem
            categoria.delete()
            messages.success(request, _(f'Categoria "{nome}" excluída com sucesso.'))
            return redirect('stock/listar_categorias')
    
    return render(request, 'stock/excluir_categoria.html', {
        'categoria': categoria,
        'tem_pecas': tem_pecas
    })


# ===========================================
# GESTÃO DE FORNECEDORES
# ===========================================

@login_required
def listar_fornecedores(request):
    """
    Lista todos os fornecedores com filtros e paginação
    """
    # Parâmetros de filtro
    searchterm = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    
    # Query base
    fornecedores = Fornecedor.objects.all()
    
    # Aplicar filtros
    if searchterm:
        fornecedores = fornecedores.filter(
            models.Q(nome__icontains=searchterm) | 
            models.Q(contacto__icontains=searchterm) | 
            models.Q(email__icontains=searchterm) | 
            models.Q(telefone__icontains=searchterm)
        )
    
    if status:
        if status == 'ativo':
            fornecedores = fornecedores.filter(ativo=True)
        elif status == 'inativo':
            fornecedores = fornecedores.filter(ativo=False)
    
    # Ordenação
    fornecedores = fornecedores.order_by('nome')
    
    # Paginação
    paginator = Paginator(fornecedores, 25)  # 25 fornecedores por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'stock/listar_fornecedores.html', {
        'page_obj': page_obj,
        'filtros': {
            'q': searchterm,
            'status': status
        },
        'total_resultados': paginator.count
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def adicionar_fornecedor(request):
    """
    Adiciona um novo fornecedor ao sistema
    """
    if request.method == 'POST':
        form = FornecedorForm(request.POST)
        if form.is_valid():
            fornecedor = form.save()
            messages.success(request, _(f'Fornecedor "{fornecedor.nome}" adicionado com sucesso.'))
            
            # Redirecionar dependendo de onde veio
            next_url = request.POST.get('next', '')
            if next_url:
                return redirect(next_url)
            return redirect('stock/detalhes_fornecedor', fornecedor_id=fornecedor.id)
    else:
        form = FornecedorForm()
    
    return render(request, 'stock/adicionar_fornecedor.html', {
        'form': form,
        'next': request.GET.get('next', '')
    })


@login_required
def detalhes_fornecedor(request, fornecedor_id):
    """
    Exibe os detalhes de um fornecedor específico
    """
    fornecedor = get_object_or_404(Fornecedor, id=fornecedor_id)
    
    # Peças fornecidas
    pecas_fornecidas = FornecedorPeca.objects.filter(
        fornecedor=fornecedor
    ).select_related('peca', 'peca__categoria').order_by('peca__codigo')
    
    # Encomendas para este fornecedor
    encomendas = EncomendaPeca.objects.filter(
        fornecedor=fornecedor
    ).order_by('-data_encomenda')[:10]
    
    return render(request, 'stock/detalhes_fornecedor.html', {
        'fornecedor': fornecedor,
        'pecas_fornecidas': pecas_fornecidas,
        'encomendas': encomendas,
        'total_pecas': pecas_fornecidas.count(),
        'total_encomendas': encomendas.count()
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def editar_fornecedor(request, fornecedor_id):
    """
    Edita um fornecedor existente
    """
    fornecedor = get_object_or_404(Fornecedor, id=fornecedor_id)
    
    if request.method == 'POST':
        form = FornecedorForm(request.POST, instance=fornecedor)
        if form.is_valid():
            fornecedor = form.save()
            messages.success(request, _(f'Fornecedor "{fornecedor.nome}" atualizado com sucesso.'))
            return redirect('stock/detalhes_fornecedor', fornecedor_id=fornecedor.id)
    else:
        form = FornecedorForm(instance=fornecedor)
    
    return render(request, 'stock/editar_fornecedor.html', {
        'form': form,
        'fornecedor': fornecedor
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def excluir_fornecedor(request, fornecedor_id):
    """
    Exclui um fornecedor existente se não houver dependências
    """
    fornecedor = get_object_or_404(Fornecedor, id=fornecedor_id)
    
    # Verificar se há peças associadas a este fornecedor
    tem_pecas = FornecedorPeca.objects.filter(fornecedor=fornecedor).exists()
    
    # Verificar se há encomendas para este fornecedor
    tem_encomendas = EncomendaPeca.objects.filter(fornecedor=fornecedor).exists()
    
    if request.method == 'POST':
        if tem_pecas or tem_encomendas:
            messages.error(request, _('Não é possível excluir este fornecedor porque existem registos dependentes.'))
        else:
            nome = fornecedor.nome  # Guardar para mensagem
            fornecedor.delete()
            messages.success(request, _(f'Fornecedor "{nome}" excluído com sucesso.'))
            return redirect('stock/listar_fornecedores')
    
    return render(request, 'stock/excluir_fornecedor.html', {
        'fornecedor': fornecedor,
        'tem_pecas': tem_pecas,
        'tem_encomendas': tem_encomendas
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def associar_peca_fornecedor(request, peca_id=None, fornecedor_id=None):
    """
    Associa uma peça a um fornecedor
    """
    # Definir contexto inicial baseado nos parâmetros
    contexto = {}
    
    if peca_id:
        peca = get_object_or_404(Peca, id=peca_id)
        contexto['peca'] = peca
    
    if fornecedor_id:
        fornecedor = get_object_or_404(Fornecedor, id=fornecedor_id)
        contexto['fornecedor'] = fornecedor
    
    # Verificar se a associação já existe
    if peca_id and fornecedor_id:
        associacao_existente = FornecedorPeca.objects.filter(
            peca_id=peca_id, fornecedor_id=fornecedor_id
        ).first()
        
        if associacao_existente:
            return redirect('stock/editar_associacao_peca_fornecedor', associacao_id=associacao_existente.id)
    
    if request.method == 'POST':
        form = FornecedorPecaForm(request.POST)
        
        # Predefinir peça ou fornecedor se fornecidos
        if not form.has_field('peca') and peca_id:
            form.instance.peca_id = peca_id
        
        if not form.has_field('fornecedor') and fornecedor_id:
            form.instance.fornecedor_id = fornecedor_id
        
        if form.is_valid():
            associacao = form.save()
            
            # Registar histórico de preço inicial
            if associacao.preco_unitario:
                HistoricoPrecoFornecedor.objects.create(
                    fornecedor_peca=associacao,
                    preco_unitario=associacao.preco_unitario,
                    utilizador=request.user
                )
            
            messages.success(request, _('Associação criada com sucesso.'))
            
            # Redirecionar com base no contexto
            if peca_id:
                return redirect('stock/detalhes_peca', peca_id=peca_id)
            elif fornecedor_id:
                return redirect('stock/detalhes_fornecedor', fornecedor_id=fornecedor_id)
            else:
                return redirect('stock/listar_pecas')
    else:
        # Se temos peça ou fornecedor, pré-preencher o formulário
        dados_iniciais = {}
        
        if peca_id:
            dados_iniciais['peca'] = peca_id
        
        if fornecedor_id:
            dados_iniciais['fornecedor'] = fornecedor_id
        
        form = FornecedorPecaForm(initial=dados_iniciais)
        
        # Esconder campos pré-preenchidos
        if peca_id:
            form.fields.pop('peca', None)
        
        if fornecedor_id:
            form.fields.pop('fornecedor', None)
    
    contexto['form'] = form
    return render(request, 'stock/associar_peca_fornecedor.html', contexto)


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def editar_associacao_peca_fornecedor(request, associacao_id):
    """
    Edita uma associação existente entre peça e fornecedor
    """
    associacao = get_object_or_404(FornecedorPeca, id=associacao_id)
    
    if request.method == 'POST':
        form = FornecedorPecaForm(request.POST, instance=associacao)
        if form.is_valid():
            # Verificar se o preço foi alterado para registar histórico
            preco_anterior = associacao.preco_unitario
            
            associacao = form.save()
            
            # Se o preço foi alterado, registar histórico
            if preco_anterior != associacao.preco_unitario:
                HistoricoPrecoFornecedor.objects.create(
                    fornecedor_peca=associacao,
                    preco_unitario=associacao.preco_unitario,
                    utilizador=request.user
                )
                
                messages.info(request, _('Histórico de preço atualizado.'))
            
            messages.success(request, _('Associação atualizada com sucesso.'))
            
            # Redirecionar para a página da peça
            return redirect('stock/detalhes_peca', peca_id=associacao.peca.id)
    else:
        form = FornecedorPecaForm(instance=associacao)
    
    return render(request, 'stock/editar_associacao_peca_fornecedor.html', {
        'form': form,
        'associacao': associacao
    })


@login_required
def historico_precos_peca(request, peca_id):
    """
    Exibe o histórico de preços de uma peça para todos os fornecedores
    """
    peca = get_object_or_404(Peca, id=peca_id)
    
    # Obter todas as associações desta peça com fornecedores
    associacoes = FornecedorPeca.objects.filter(
        peca=peca
    ).select_related('fornecedor')
    
    historicos = {}
    
    # Para cada associação, obter o histórico de preços
    for assoc in associacoes:
        historicos[assoc.id] = {
            'fornecedor': assoc.fornecedor,
            'preco_atual': assoc.preco_unitario,
            'registos': HistoricoPrecoFornecedor.objects.filter(
                fornecedor_peca=assoc
            ).select_related('utilizador').order_by('-data_alteracao')
        }
    
    return render(request, 'stock/historico_precos_peca.html', {
        'peca': peca,
        'historicos': historicos
    })

@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def receber_encomenda(request, encomenda_id):
    """
    Regista o recebimento de itens de uma encomenda
    """
    encomenda = get_object_or_404(EncomendaPeca, id=encomenda_id)
    
    # Obter itens ainda não recebidos completamente
    itens_pendentes = ItemEncomenda.objects.filter(
        encomenda=encomenda,
        quantidade_recebida__lt=models.F('quantidade')
    ).select_related('peca')
    
    if not itens_pendentes.exists():
        messages.info(request, _('Todos os itens desta encomenda já foram recebidos.'))
        return redirect('stock/detalhes_encomenda', encomenda_id=encomenda.id)
    
    if request.method == 'POST':
        # Processar recebimentos
        itens_atualizados = 0
        data_recebimento = request.POST.get('data_recebimento')
        num_documento = request.POST.get('num_documento', '')
        observacao = request.POST.get('observacao', '')
        
        for item in itens_pendentes:
            qtd_recebida_str = request.POST.get(f'qtd_recebida_{item.id}', '0')
            
            try:
                qtd_recebida = int(qtd_recebida_str)
                
                # Validar quantidade
                if qtd_recebida <= 0:
                    continue  # Pular este item
                
                qtd_pendente = item.quantidade - item.quantidade_recebida
                
                if qtd_recebida > qtd_pendente:
                    messages.warning(request, _(
                        'Quantidade recebida para o item %(codigo)s foi ajustada '
                        'para o máximo pendente (%(pendente)s)'
                    ) % {
                        'codigo': item.peca.codigo,
                        'pendente': qtd_pendente
                    })
                    qtd_recebida = qtd_pendente
                
                # Atualizar quantidade recebida do item
                item.quantidade_recebida += qtd_recebida
                
                # Atualizar status do item
                if item.quantidade_recebida >= item.quantidade:
                    item.status = 'recebido'
                else:
                    item.status = 'parcial'
                
                # Guardar
                item.save()
                
                # Registar movimentação de stock
                MovimentacaoStock.objects.create(
                    peca=item.peca,
                    tipo='entrada',
                    motivo='compra',
                    quantidade=qtd_recebida,
                    preco_unitario=item.preco_unitario,
                    data_movimentacao=data_recebimento,
                    fornecedor=encomenda.fornecedor,
                    num_fatura=num_documento,
                    observacao=observacao,
                    utilizador=request.user
                )
                
                # Atualizar stock da peça
                item.peca.stock_atual += qtd_recebida
                item.peca.save()
                
                itens_atualizados += 1
            
            except ValueError:
                messages.error(request, _(
                    'Valor inválido para o item %(codigo)s'
                ) % {'codigo': item.peca.codigo})
        
        # Atualizar status da encomenda
        if itens_atualizados > 0:
            # Verificar se todos os itens foram recebidos
            itens_total = ItemEncomenda.objects.filter(encomenda=encomenda).count()
            itens_recebidos = ItemEncomenda.objects.filter(
                encomenda=encomenda, status='recebido'
            ).count()
            
            if itens_recebidos == itens_total:
                encomenda.status = 'concluida'
            else:
                encomenda.status = 'parcial'
            
            encomenda.save()
            
            messages.success(request, _(
                'Receção registada com sucesso para %(count)s itens.'
            ) % {'count': itens_atualizados})
        
        return redirect('stock/detalhes_encomenda', encomenda_id=encomenda.id)
    
    return render(request, 'stock/receber_encomenda.html', {
        'encomenda': encomenda,
        'itens_pendentes': itens_pendentes,
        'data_atual': timezone.now().date().strftime('%Y-%m-%d')
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def cancelar_encomenda(request, encomenda_id):
    """
    Cancela uma encomenda pendente
    """
    encomenda = get_object_or_404(EncomendaPeca, id=encomenda_id)
    
    # Verificar se a encomenda já foi recebida parcialmente
    itens_recebidos = ItemEncomenda.objects.filter(
        encomenda=encomenda, quantidade_recebida__gt=0
    ).exists()
    
    if request.method == 'POST':
        if itens_recebidos:
            messages.error(request, _(
                'Não é possível cancelar esta encomenda '
                'porque já existem itens recebidos.'
            ))
        else:
            encomenda.status = 'cancelada'
            encomenda.observacoes += '\n\n' + _('Cancelada em %(data)s por %(user)s') % {
                'data': timezone.now().strftime('%d/%m/%Y %H:%M'),
                'user': request.user.get_full_name() or request.user.username
            }
            encomenda.save()
            
            # Atualizar status dos itens
            ItemEncomenda.objects.filter(encomenda=encomenda).update(status='cancelado')
            
            messages.success(request, _(f'Encomenda "{encomenda.numero_pedido}" cancelada com sucesso.'))
        
        return redirect('stock/detalhes_encomenda', encomenda_id=encomenda.id)
    
    return render(request, 'stock/cancelar_encomenda.html', {
        'encomenda': encomenda,
        'itens_recebidos': itens_recebidos
    })


# ===========================================
# APIS E ENDPOINTS AUXILIARES
# ===========================================

@login_required
def api_filtrar_pecas(request):
    """
    API para filtrar peças por diversos critérios e retornar em JSON
    Usada para pesquisas dinâmicas em AJAX
    """
    resultados = []
    
    # Parâmetros de filtro
    query = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria')
    fornecedor_id = request.GET.get('fornecedor')
    stock_minimo = request.GET.get('stock_minimo') == 'true'
    stock_zero = request.GET.get('stock_zero') == 'true'
    limit = request.GET.get('limit', 20)
    
    try:
        limit = int(limit)
        if limit <= 0 or limit > 100:
            limit = 20  # Limitar para evitar sobrecarga
    except ValueError:
        limit = 20
    
    # Query base
    pecas = Peca.objects.all()
    
    # Aplicar filtros
    if categoria_id and categoria_id.isdigit():
        pecas = pecas.filter(categoria_id=categoria_id)
    
    if fornecedor_id and fornecedor_id.isdigit():
        pecas = pecas.filter(fornecedor_pecas__fornecedor_id=fornecedor_id)
    
    if stock_minimo:
        pecas = pecas.filter(stock_atual__lt=models.F('stock_minimo'), stock_atual__gt=0)
    
    if stock_zero:
        pecas = pecas.filter(stock_atual=0)
    
    if query:
        pecas = pecas.filter(
            models.Q(codigo__icontains=query) | 
            models.Q(nome__icontains=query) |
            models.Q(descricao__icontains=query)
        )
    
    # Ordenar e limitar resultados
    pecas = pecas.order_by('codigo')[:limit]
    
    # Formatar resultados
    for peca in pecas:
        # Obter fornecedor preferencial se houver
        fornecedor_preferencial = FornecedorPeca.objects.filter(
            peca=peca, 
            fornecedor_preferencial=True
        ).select_related('fornecedor').first()
        
        # Estrutura do resultado
        resultado = {
            'id': peca.id,
            'codigo': peca.codigo,
            'nome': peca.nome,
            'categoria': peca.categoria.nome if peca.categoria else None,
            'stock_atual': peca.stock_atual,
            'stock_minimo': peca.stock_minimo,
            'unidade': peca.unidade,
            'preco_venda': float(peca.preco_venda) if peca.preco_venda else None,
            'status_stock': 'ok' if peca.stock_atual >= peca.stock_minimo else (
                'baixo' if peca.stock_atual > 0 else 'esgotado'
            ),
            'url': request.build_absolute_uri(
                reverse('detalhes_peca', args=[peca.id])
            )
        }
        
        # Adicionar informações do fornecedor preferencial se existir
        if fornecedor_preferencial:
            resultado['fornecedor_preferencial'] = {
                'id': fornecedor_preferencial.fornecedor.id,
                'nome': fornecedor_preferencial.fornecedor.nome,
                'preco': float(fornecedor_preferencial.preco_unitario) if fornecedor_preferencial.preco_unitario else None
            }
        
        resultados.append(resultado)
    
    return JsonResponse({
        'success': True,
        'resultados': resultados,
        'total': len(resultados),
        'filtros': {
            'query': query,
            'categoria': categoria_id,
            'fornecedor': fornecedor_id,
            'stock_minimo': stock_minimo,
            'stock_zero': stock_zero
        }
    })


@login_required
def api_historico_precos_peca(request, peca_id):
    """
    API que retorna o histórico de preços de uma peça específica para todos os fornecedores
    Usado para gerar gráficos de evolução de preços
    """
    try:
        # Verificar se a peça existe
        peca = Peca.objects.get(id=peca_id)
        
        # Obter todas as associações de fornecedores para esta peça
        associacoes = FornecedorPeca.objects.filter(peca=peca).select_related('fornecedor')
        
        # Resultado a ser retornado
        dados = {
            'peca': {
                'id': peca.id,
                'codigo': peca.codigo,
                'nome': peca.nome
            },
            'fornecedores': [],
            'historico': {}
        }
        
        # Para cada fornecedor, obter o histórico de preços
        for associacao in associacoes:
            fornecedor_id = associacao.fornecedor.id
            fornecedor_nome = associacao.fornecedor.nome
            
            # Adicionar fornecedor à lista
            dados['fornecedores'].append({
                'id': fornecedor_id,
                'nome': fornecedor_nome,
                'preco_atual': float(associacao.preco_unitario) if associacao.preco_unitario else 0,
                'preferencial': associacao.fornecedor_preferencial
            })
            
            # Obter histórico de preços para este fornecedor
            historico = HistoricoPrecoFornecedor.objects.filter(
                fornecedor_peca=associacao
            ).order_by('data_alteracao')
            
            # Formatar histórico para este fornecedor
            dados_fornecedor = []
            for registo in historico:
                dados_fornecedor.append({
                    'data': registo.data_alteracao.strftime('%Y-%m-%d'),
                    'preco': float(registo.preco_unitario) if registo.preco_unitario else 0,
                    'utilizador': registo.utilizador.get_full_name() if registo.utilizador else 'Sistema'
                })
            
            # Adicionar histórico deste fornecedor ao resultado
            dados['historico'][fornecedor_id] = dados_fornecedor
        
        return JsonResponse({
            'success': True,
            'dados': dados
        })
        
    except Peca.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Peça não encontrada'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def api_pecas_modelo(request, modelo_id):
    """
    API que retorna todas as peças compatíveis com um determinado modelo de equipamento
    Usado para facilitar a seleção de peças em serviços de assistência técnica
    """
    try:
        # Obter peças associadas a este modelo
        # Assumindo que existe um relacionamento entre modelos e peças
        pecas = Peca.objects.filter(modelos_compativeis__id=modelo_id).order_by('codigo')
        
        # Formatar resultados
        resultados = []
        for peca in pecas:
            # Obter fornecedor preferencial se houver
            fornecedor_pref = FornecedorPeca.objects.filter(
                peca=peca, 
                fornecedor_preferencial=True
            ).select_related('fornecedor').first()
            
            resultado = {
                'id': peca.id,
                'codigo': peca.codigo,
                'nome': peca.nome,
                'categoria': peca.categoria.nome if peca.categoria else None,
                'stock_atual': peca.stock_atual,
                'unidade': peca.unidade,
                'preco_venda': float(peca.preco_venda) if peca.preco_venda else None,
                'disponivel': peca.stock_atual > 0,
                'url': request.build_absolute_uri(
                    reverse('detalhes_peca', args=[peca.id])
                )
            }
            
            # Adicionar informações do fornecedor preferencial
            if fornecedor_pref:
                resultado['fornecedor'] = {
                    'id': fornecedor_pref.fornecedor.id,
                    'nome': fornecedor_pref.fornecedor.nome,
                    'referencia': fornecedor_pref.referencia_fornecedor
                }
            
            resultados.append(resultado)
        
        return JsonResponse({
            'success': True,
            'modelo_id': modelo_id,
            'total_pecas': len(resultados),
            'pecas': resultados
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def api_filtrar_fornecedores(request):
    """
    API para filtrar fornecedores por diversos critérios e retornar em JSON
    Usada para pesquisas dinâmicas em AJAX
    """
    resultados = []
    
    # Parâmetros de filtro
    query = request.GET.get('q', '').strip()
    fornece_peca_id = request.GET.get('peca_id')
    ativo = request.GET.get('ativo') == 'true'
    limit = request.GET.get('limit', 20)
    
    try:
        limit = int(limit)
        if limit <= 0 or limit > 100:
            limit = 20  # Limitar para evitar sobrecarga
    except ValueError:
        limit = 20
    
    # Query base
    fornecedores = Fornecedor.objects.all()
    
    # Aplicar filtros
    if query:
        fornecedores = fornecedores.filter(
            models.Q(nome__icontains=query) | 
            models.Q(contacto__icontains=query) |
            models.Q(email__icontains=query) |
            models.Q(telefone__icontains=query)
        )
    
    # Filtrar fornecedores que fornecem uma determinada peça
    if fornece_peca_id and fornece_peca_id.isdigit():
        fornecedores = fornecedores.filter(
            fornecedor_pecas__peca_id=fornece_peca_id
        )
    
    # Filtrar apenas fornecedores ativos (se solicitado)
    if ativo:
        fornecedores = fornecedores.filter(ativo=True)
    
    # Remover duplicatas e ordenar
    fornecedores = fornecedores.distinct().order_by('nome')[:limit]
    
    # Formatar resultados
    for fornecedor in fornecedores:
        # Contar quantas peças este fornecedor fornece
        total_pecas = FornecedorPeca.objects.filter(fornecedor=fornecedor).count()
        
        # Estrutura do resultado
        resultado = {
            'id': fornecedor.id,
            'nome': fornecedor.nome,
            'contacto': fornecedor.contacto,
            'telefone': fornecedor.telefone,
            'email': fornecedor.email,
            'website': fornecedor.website,
            'total_pecas': total_pecas,
            'url': request.build_absolute_uri(
                reverse('detalhes_fornecedor', args=[fornecedor.id])
            )
        }
        
        # Se estiver filtrando por peça, adicionar detalhes da associação
        if fornece_peca_id and fornece_peca_id.isdigit():
            try:
                associacao = FornecedorPeca.objects.get(
                    fornecedor=fornecedor,
                    peca_id=fornece_peca_id
                )
                resultado['associacao'] = {
                    'id': associacao.id,
                    'preco': float(associacao.preco_unitario) if associacao.preco_unitario else None,
                    'referencia': associacao.referencia_fornecedor,
                    'tempo_entrega': associacao.tempo_entrega,
                    'preferencial': associacao.fornecedor_preferencial
                }
            except FornecedorPeca.DoesNotExist:
                pass
        
        resultados.append(resultado)
    
    return JsonResponse({
        'success': True,
        'resultados': resultados,
        'total': len(resultados),
        'filtros': {
            'query': query,
            'peca_id': fornece_peca_id,
            'ativo': ativo
        }
    })

def gerar_cod_peca_sequencial(prefixo='P'):
    """
    Gera um código de peça sequencial com um prefixo
    Formato: PXXXXX (onde X é um número)
    """
    # Obter o último código existente com este prefixo
    ultima_peca = Peca.objects.filter(
        codigo__startswith=prefixo
    ).order_by('-codigo').first()
    
    if ultima_peca:
        # Extrair o número do código
        try:
            numero = int(ultima_peca.codigo[len(prefixo):])
            novo_numero = numero + 1
        except ValueError:
            # Se o código não seguir o formato esperado, começar do 1
            novo_numero = 1
    else:
        # Se não houver nenhuma peça com este prefixo, começar do 1
        novo_numero = 1
    
    # Formatar o novo código (prefixo + número de 5 dígitos)
    return f"{prefixo}{novo_numero:05d}"

def obter_estatisticas_stock():
    """
    Obtém estatísticas globais do stock
    """
    # Total de peças
    total_pecas = Peca.objects.count()
    
    # Total de fornecedores
    total_fornecedores = Fornecedor.objects.count()
    
    # Valor total do stock (custo)
    valor_stock = Peca.objects.aggregate(
        valor_total=models.Sum(models.F('stock_atual') * models.F('preco_custo'))
    )['valor_total'] or 0
    
    # Valor potencial de vendas
    valor_vendas = Peca.objects.aggregate(
        valor_total=models.Sum(models.F('stock_atual') * models.F('preco_venda'))
    )['valor_total'] or 0
    
    # Peças com stock crítico
    pecas_baixo_stock = Peca.objects.filter(
        stock_atual__lt=models.F('stock_minimo')
    ).count()
    
    # Peças esgotadas
    pecas_esgotadas = Peca.objects.filter(stock_atual=0).count()
    
    # Movimentações recentes (últimos 30 dias)
    data_limite = timezone.now() - timedelta(days=30)
    movimentacoes_recentes = MovimentacaoStock.objects.filter(
        data_movimentacao__gte=data_limite
    ).count()
    
    # Encomendas pendentes
    encomendas_pendentes = EncomendaPeca.objects.filter(
        status__in=['pendente', 'encomendada', 'parcial']
    ).count()
    
    return {
        'total_pecas': total_pecas,
        'total_fornecedores': total_fornecedores,
        'valor_stock': valor_stock,
        'valor_vendas': valor_vendas,
        'pecas_baixo_stock': pecas_baixo_stock,
        'pecas_esgotadas': pecas_esgotadas,
        'movimentacoes_recentes': movimentacoes_recentes,
        'encomendas_pendentes': encomendas_pendentes
    }

@login_required
def listar_movimentacoes(request):
    """
    Lista todas as movimentações de stock com filtros e paginação
    """
    # Parâmetros de filtro
    tipo = request.GET.get('tipo', '')
    motivo = request.GET.get('motivo', '')
    peca_id = request.GET.get('peca', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    searchterm = request.GET.get('q', '').strip()
    
    # Query base
    movimentacoes = MovimentacaoStock.objects.all()
    
    # Aplicar filtros
    if tipo:
        movimentacoes = movimentacoes.filter(tipo=tipo)
    
    if motivo:
        movimentacoes = movimentacoes.filter(motivo=motivo)
    
    if peca_id and peca_id.isdigit():
        movimentacoes = movimentacoes.filter(peca_id=peca_id)
    
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            movimentacoes = movimentacoes.filter(data_movimentacao__gte=data_inicio_obj)
        except ValueError:
            pass
    
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            movimentacoes = movimentacoes.filter(data_movimentacao__lte=data_fim_obj)
        except ValueError:
            pass
    
    if searchterm:
        movimentacoes = movimentacoes.filter(
            models.Q(peca__codigo__icontains=searchterm) | 
            models.Q(peca__nome__icontains=searchterm) | 
            models.Q(observacao__icontains=searchterm)
        )
    
    # Ordenação
    movimentacoes = movimentacoes.select_related('peca', 'fornecedor').order_by('-data_movimentacao')
    
    # Paginação
    paginator = Paginator(movimentacoes, 50)  # 50 movimentações por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'stock/listar_movimentacoes.html', {
        'page_obj': page_obj,
        'filtros': {
            'tipo': tipo,
            'motivo': motivo,
            'peca': peca_id,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'q': searchterm
        },
        'total_resultados': paginator.count
    })

@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def adicionar_movimentacao(request):
    """
    Adiciona uma nova movimentação de stock (entrada ou saída)
    """
    if request.method == 'POST':
        form = MovimentacaoStockForm(request.POST)
        if form.is_valid():
            movimentacao = form.save(commit=False)
            movimentacao.utilizador = request.user
            
            # Atualizar stock da peça
            peca = movimentacao.peca
            if movimentacao.tipo == 'entrada':
                peca.stock_atual += movimentacao.quantidade
            else:  # saída
                # Verificar se há stock suficiente
                if peca.stock_atual < movimentacao.quantidade:
                    messages.error(request, _(
                        'Stock insuficiente. Existem apenas %(stock)s unidades disponíveis.'
                    ) % {'stock': peca.stock_atual})
                    return render(request, 'stock/adicionar_movimentacao.html', {'form': form})
                
                peca.stock_atual -= movimentacao.quantidade
            
            # Salvar alterações
            peca.save()
            movimentacao.save()
            
            messages.success(request, _(
                'Movimentação de %(tipo)s registada com sucesso. '
                'Stock atual da peça: %(stock)s'
            ) % {
                'tipo': _('entrada') if movimentacao.tipo == 'entrada' else _('saída'),
                'stock': peca.stock_atual
            })
            
            return redirect('stock/listar_movimentacoes')
    else:
        form = MovimentacaoStockForm(initial={'data_movimentacao': timezone.now()})
    
    return render(request, 'stock/adicionar_movimentacao.html', {'form': form})

@login_required
def detalhes_movimentacao(request, movimentacao_id):
    """
    Exibe os detalhes de uma movimentação específica
    """
    movimentacao = get_object_or_404(MovimentacaoStock, id=movimentacao_id)
    
    # Obter movimentações relacionadas (da mesma peça)
    movimentacoes_relacionadas = MovimentacaoStock.objects.filter(
        peca=movimentacao.peca
    ).exclude(
        id=movimentacao_id
    ).order_by('-data_movimentacao')[:10]  # Últimas 10 movimentações
    
    return render(request, 'stock/detalhes_movimentacao.html', {
        'movimentacao': movimentacao,
        'movimentacoes_relacionadas': movimentacoes_relacionadas
    })

@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def exportar_associacoes(request):
    """
    Exporta associações entre peças e fornecedores para um arquivo CSV ou Excel
    """
    if not PANDAS_AVAILABLE:
        messages.error(request, _('Bibliotecas necessárias para exportação não estão instaladas.'))
        return redirect('stock/importar_exportar')
    
    formato = request.GET.get('formato', 'excel')
    
    # Obter todas as associações
    associacoes = FornecedorPeca.objects.all().select_related('peca', 'fornecedor')
    
    # Criar DataFrame
    data = []
    for assoc in associacoes:
        row = {
            'codigo_peca': assoc.peca.codigo,
            'nome_peca': assoc.peca.nome,
            'nome_fornecedor': assoc.fornecedor.nome,
            'referencia_fornecedor': assoc.referencia_fornecedor,
            'preco_unitario': float(assoc.preco_unitario) if assoc.preco_unitario else 0,
            'tempo_entrega': assoc.tempo_entrega,
            'preferencial': assoc.fornecedor_preferencial,
            'notas': assoc.notas
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # Exportar nos formatos suportados
    if formato == 'excel':
        # Gerar Excel
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=associacoes_export.xlsx'
        
        with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Associações', index=False)
        
        return response
    
    elif formato == 'csv':
        # Gerar CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=associacoes_export.csv'
        
        df.to_csv(response, index=False, encoding='utf-8-sig')
        return response
    
    else:
        messages.error(request, _('Formato de exportação não suportado.'))
        return redirect('stock/importar_exportar')

def gerar_relatorio_movimentacoes(data_inicio, data_fim, formato='pdf'):
    """
    Gera um relatório de movimentações de stock num período específico
    """
    # Converter datas para objetos date
    try:
        data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
    except ValueError:
        return None, "Formato de data inválido"
    
    # Obter movimentações no período
    movimentacoes = MovimentacaoStock.objects.filter(
        data_movimentacao__gte=data_inicio_obj,
        data_movimentacao__lte=data_fim_obj
    ).select_related('peca', 'fornecedor', 'utilizador').order_by('data_movimentacao')
    
    if not movimentacoes.exists():
        return None, "Nenhuma movimentação encontrada no período especificado"
    
    # Estatísticas
    total_entradas = movimentacoes.filter(tipo='entrada').aggregate(
        total=models.Sum('quantidade'),
        valor=models.Sum(models.F('quantidade') * models.F('preco_unitario'))
    )
    
    total_saidas = movimentacoes.filter(tipo='saida').aggregate(
        total=models.Sum('quantidade'),
        valor=models.Sum(models.F('quantidade') * models.F('preco_unitario'))
    )
    
    # Dados para o relatório
    dados = {
        'movimentacoes': movimentacoes,
        'data_inicio': data_inicio_obj,
        'data_fim': data_fim_obj,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'data_geracao': timezone.now()
    }
    
    # Gerar relatório no formato solicitado
    if formato == 'pdf':
        # Código para gerar PDF
        # (Requer biblioteca específica como ReportLab ou WeasyPrint)
        return None, "Geração de PDF não implementada"
    
    elif formato == 'excel':
        # Criar DataFrame com os dados
        data = []
        for mov in movimentacoes:
            row = {
                'data': mov.data_movimentacao.strftime('%Y-%m-%d %H:%M'),
                'tipo': 'Entrada' if mov.tipo == 'entrada' else 'Saída',
                'motivo': mov.get_motivo_display(),
                'peca_codigo': mov.peca.codigo,
                'peca_nome': mov.peca.nome,
                'quantidade': mov.quantidade,
                'preco_unitario': float(mov.preco_unitario) if mov.preco_unitario else 0,
                'valor_total': float(mov.quantidade * mov.preco_unitario) if mov.preco_unitario else 0,
                'fornecedor': mov.fornecedor.nome if mov.fornecedor else '',
                'utilizador': mov.utilizador.get_full_name() if mov.utilizador else '',
                'observacao': mov.observacao or ''
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Gerar Excel em memória
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Movimentações', index=False)
            
            # Adicionar aba com resumo
            resumo_data = [
                {'Métrica': 'Total de Entradas (Quantidades)', 'Valor': total_entradas['total'] or 0},
                {'Métrica': 'Total de Entradas (Valor)', 'Valor': total_entradas['valor'] or 0},
                {'Métrica': 'Total de Saídas (Quantidades)', 'Valor': total_saidas['total'] or 0},
                {'Métrica': 'Total de Saídas (Valor)', 'Valor': total_saidas['valor'] or 0},
                {'Métrica': 'Período', 'Valor': f"{data_inicio} a {data_fim}"},
            ]
            pd.DataFrame(resumo_data).to_excel(writer, sheet_name='Resumo', index=False)
        
        output.seek(0)
        return output.getvalue(), f"relatorio_movimentacoes_{data_inicio}_{data_fim}.xlsx"
    
    elif formato == 'csv':
        # Criar CSV em memória
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        writer.writerow([
            'Data', 'Tipo', 'Motivo', 'Código Peça', 'Nome Peça', 'Quantidade',
            'Preço Unitário', 'Valor Total', 'Fornecedor', 'Utilizador', 'Observação'
        ])
        
        # Dados
        for mov in movimentacoes:
            writer.writerow([
                mov.data_movimentacao.strftime('%Y-%m-%d %H:%M'),
                'Entrada' if mov.tipo == 'entrada' else 'Saída',
                mov.get_motivo_display(),
                mov.peca.codigo,
                mov.peca.nome,
                mov.quantidade,
                float(mov.preco_unitario) if mov.preco_unitario else 0,
                float(mov.quantidade * mov.preco_unitario) if mov.preco_unitario else 0,
                mov.fornecedor.nome if mov.fornecedor else '',
                mov.utilizador.get_full_name() if mov.utilizador else '',
                mov.observacao or ''
            ])
        
        return output.getvalue(), f"relatorio_movimentacoes_{data_inicio}_{data_fim}.csv"
    
    else:
        return None, "Formato de relatório não suportado"


def gerar_etiquetas_pecas(pecas_ids, formato='pdf'):
    """
    Gera etiquetas para as peças selecionadas
    """
    # Obter peças
    pecas = Peca.objects.filter(id__in=pecas_ids)
    
    if not pecas.exists():
        return None, "Nenhuma peça selecionada"
    
    # Gerar etiquetas no formato solicitado
    if formato == 'pdf':
        # Código para gerar PDF de etiquetas
        # (Requer biblioteca específica como ReportLab ou WeasyPrint)
        return None, "Geração de PDF não implementada"
    
    elif formato == 'excel':
        # Criar template de etiquetas em Excel
        data = []
        for peca in pecas:
            row = {
                'codigo': peca.codigo,
                'nome': peca.nome,
                'categoria': peca.categoria.nome if peca.categoria else '',
                'localizacao': peca.localizacao,
                'codigo_barras': peca.codigo  # Seria melhor ter um campo específico para código de barras
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Gerar Excel em memória
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Etiquetas', index=False)
            
            # Configurar formatação para impressão de etiquetas
            worksheet = writer.sheets['Etiquetas']
            
            # Ajustar largura das colunas
            worksheet.set_column('A:A', 15)  # Código
            worksheet.set_column('B:B', 25)  # Nome
            worksheet.set_column('C:C', 15)  # Categoria
            worksheet.set_column('D:D', 15)  # Localização
            worksheet.set_column('E:E', 15)  # Código de barras
            
            # Configurar para impressão
            worksheet.set_paper(9)  # A4
            worksheet.fit_to_pages(1, 0)  # Ajustar para largura da página
        
        output.seek(0)
        return output.getvalue(), "etiquetas_pecas.xlsx"
    
    else:
        return None, "Formato de etiquetas não suportado"

# ===========================================
# APIS E ENDPOINTS AUXILIARES ADICIONAIS
# ===========================================

@login_required
def api_movimentacoes_peca(request, peca_id):
    """
    API que retorna as movimentações de uma peça específica
    Usado para mostrar o histórico de movimentações em gráficos ou tabelas
    """
    try:
        # Verificar se a peça existe
        peca = Peca.objects.get(id=peca_id)
        
        # Parâmetros de filtro
        dias = request.GET.get('dias', '90')  # Últimos 90 dias por padrão
        tipo = request.GET.get('tipo', '')    # Todos os tipos de movimentação
        
        try:
            dias = int(dias)
            if dias <= 0:
                dias = 90
        except ValueError:
            dias = 90
        
        # Data limite para o período
        data_limite = timezone.now() - timedelta(days=dias)
        
        # Obter as movimentações
        movimentacoes = MovimentacaoStock.objects.filter(
            peca=peca,
            data_movimentacao__gte=data_limite
        ).order_by('data_movimentacao')
        
        # Aplicar filtro por tipo
        if tipo and tipo in ['entrada', 'saida']:
            movimentacoes = movimentacoes.filter(tipo=tipo)
        
        # Formatar resultados
        resultados = []
        saldo_acumulado = peca.stock_atual
        
        # Somar quantidades de movimentações mais recentes que o período para 
        # calcular o saldo no início do período
        movimentacoes_posteriores = MovimentacaoStock.objects.filter(
            peca=peca,
            data_movimentacao__gt=data_limite
        )
        
        for mov in movimentacoes_posteriores:
            if mov.tipo == 'entrada':
                saldo_acumulado -= mov.quantidade
            else:
                saldo_acumulado += mov.quantidade
        
        # Processar movimentações para o período solicitado
        for mov in movimentacoes:
            # Calcular saldo após esta movimentação
            if mov.tipo == 'entrada':
                saldo_acumulado += mov.quantidade
            else:
                saldo_acumulado -= mov.quantidade
            
            resultados.append({
                'id': mov.id,
                'data': mov.data_movimentacao.strftime('%Y-%m-%d %H:%M'),
                'tipo': mov.tipo,
                'motivo': mov.get_motivo_display(),
                'quantidade': mov.quantidade,
                'saldo_apos': saldo_acumulado,
                'preco_unitario': float(mov.preco_unitario) if mov.preco_unitario else None,
                'fornecedor': mov.fornecedor.nome if mov.fornecedor else None,
                'utilizador': mov.utilizador.get_full_name() if mov.utilizador else None,
                'observacao': mov.observacao
            })
        
        return JsonResponse({
            'success': True,
            'peca': {
                'id': peca.id,
                'codigo': peca.codigo,
                'nome': peca.nome,
                'stock_atual': peca.stock_atual
            },
            'periodo_dias': dias,
            'data_inicio': data_limite.strftime('%Y-%m-%d'),
            'data_fim': timezone.now().strftime('%Y-%m-%d'),
            'total_movimentacoes': len(resultados),
            'movimentacoes': resultados
        })
        
    except Peca.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Peça não encontrada'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def api_sugerir_compras(request):
    """
    API que sugere peças a serem compradas baseado no stock mínimo e encomendas pendentes
    Útil para o dashboard e recomendações de reposição de stock
    """
    # Obter peças com stock abaixo do mínimo
    pecas_baixo_stock = Peca.objects.filter(
        stock_atual__lt=models.F('stock_minimo')
    ).annotate(
        deficit=models.F('stock_minimo') - models.F('stock_atual')
    ).select_related('categoria')
    
    sugestoes = []
    
    for peca in pecas_baixo_stock:
        # Verificar se já existe encomenda pendente para esta peça
        quantidade_encomendada = ItemEncomenda.objects.filter(
            peca=peca,
            encomenda__status__in=['pendente', 'encomendada'],
            quantidade_recebida__lt=models.F('quantidade')
        ).aggregate(
            total=models.Sum(models.F('quantidade') - models.F('quantidade_recebida'))
        )['total'] or 0
        
        # Calcular quantidade a comprar (para chegar ao stock ideal)
        quantidade_comprar = max(0, peca.stock_ideal - peca.stock_atual - quantidade_encomendada)
        
        if quantidade_comprar > 0:
            # Obter fornecedor preferencial
            fornecedor_preferencial = FornecedorPeca.objects.filter(
                peca=peca,
                fornecedor_preferencial=True
            ).select_related('fornecedor').first()
            
            sugestao = {
                'id': peca.id,
                'codigo': peca.codigo,
                'nome': peca.nome,
                'categoria': peca.categoria.nome if peca.categoria else None,
                'stock_atual': peca.stock_atual,
                'stock_minimo': peca.stock_minimo,
                'stock_ideal': peca.stock_ideal,
                'deficit': peca.deficit,
                'quantidade_encomendada': quantidade_encomendada,
                'quantidade_sugerida': quantidade_comprar,
                'url': request.build_absolute_uri(reverse('detalhes_peca', args=[peca.id]))
            }
            
            # Adicionar informações do fornecedor preferencial
            if fornecedor_preferencial:
                sugestao['fornecedor'] = {
                    'id': fornecedor_preferencial.fornecedor.id,
                    'nome': fornecedor_preferencial.fornecedor.nome,
                    'preco_unitario': float(fornecedor_preferencial.preco_unitario) if fornecedor_preferencial.preco_unitario else None,
                    'tempo_entrega': fornecedor_preferencial.tempo_entrega,
                    'url': request.build_absolute_uri(reverse('detalhes_fornecedor', args=[fornecedor_preferencial.fornecedor.id]))
                }
            
            sugestoes.append(sugestao)
    
    return JsonResponse({
        'success': True,
        'total_sugestoes': len(sugestoes),
        'sugestoes': sugestoes
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def api_relatorio_valorizado(request):
    """
    API que retorna um relatório valorizado do stock atual
    Usado para análises financeiras e inventário
    """
    # Parâmetros de filtro
    categoria_id = request.GET.get('categoria')
    valorizar_por = request.GET.get('valor', 'custo')  # custo ou venda
    
    # Query base
    pecas = Peca.objects.all().select_related('categoria')
    
    # Aplicar filtros
    if categoria_id and categoria_id.isdigit():
        pecas = pecas.filter(categoria_id=categoria_id)
    
    # Calcular valores
    total_valor = 0
    itens = []
    
    for peca in pecas:
        if peca.stock_atual > 0:
            # Determinar o valor unitário (custo ou venda)
            valor_unitario = 0
            if valorizar_por == 'custo':
                valor_unitario = peca.preco_custo or 0
            else:  # venda
                valor_unitario = peca.preco_venda or 0
            
            valor_total = peca.stock_atual * valor_unitario
            total_valor += valor_total
            
            itens.append({
                'id': peca.id,
                'codigo': peca.codigo,
                'nome': peca.nome,
                'categoria': peca.categoria.nome if peca.categoria else None,
                'stock_atual': peca.stock_atual,
                'valor_unitario': float(valor_unitario),
                'valor_total': float(valor_total)
            })
    
    # Agrupar por categoria
    categorias = {}
    for item in itens:
        categoria = item['categoria'] or 'Sem Categoria'
        if categoria not in categorias:
            categorias[categoria] = {
                'nome': categoria,
                'itens': 0,
                'valor': 0
            }
        
        categorias[categoria]['itens'] += 1
        categorias[categoria]['valor'] += item['valor_total']
    
    return JsonResponse({
        'success': True,
        'valorizado_por': valorizar_por,
        'total_itens': len(itens),
        'total_valor': float(total_valor),
        'itens': itens,
        'categorias': list(categorias.values())
    })


@login_required
def api_encomendas_pendentes(request):
    """
    API que retorna encomendas pendentes e seu status
    Usado para monitoramento e dashboards
    """
    # Obter encomendas não concluídas ou canceladas
    encomendas = EncomendaPeca.objects.filter(
        status__in=['pendente', 'encomendada', 'parcial']
    ).select_related('fornecedor').order_by('data_encomenda')
    
    # Formatar resultados
    resultados = []
    for encomenda in encomendas:
        # Calcular resumo dos itens
        itens = ItemEncomenda.objects.filter(encomenda=encomenda)
        total_itens = itens.count()
        total_unidades = itens.aggregate(
            total=models.Sum('quantidade')
        )['total'] or 0
        unidades_recebidas = itens.aggregate(
            recebidas=models.Sum('quantidade_recebida')
        )['recebidas'] or 0
        
        # Calcular valor total
        valor_total = itens.aggregate(
            valor=models.Sum(models.F('quantidade') * models.F('preco_unitario'))
        )['valor'] or 0
        
        # Calcular dias pendentes e previsão de atraso
        dias_pendentes = 0
        atrasado = False
        dias_atraso = 0
        
        if encomenda.data_encomenda:
            dias_pendentes = (timezone.now().date() - encomenda.data_encomenda).days
        
        if encomenda.prazo_entrega and timezone.now().date() > encomenda.prazo_entrega:
            atrasado = True
            dias_atraso = (timezone.now().date() - encomenda.prazo_entrega).days
        
        resultados.append({
            'id': encomenda.id,
            'numero_pedido': encomenda.numero_pedido,
            'data_encomenda': encomenda.data_encomenda.strftime('%Y-%m-%d') if encomenda.data_encomenda else None,
            'prazo_entrega': encomenda.prazo_entrega.strftime('%Y-%m-%d') if encomenda.prazo_entrega else None,
            'fornecedor': {
                'id': encomenda.fornecedor.id,
                'nome': encomenda.fornecedor.nome
            },
            'status': encomenda.status,
            'status_display': encomenda.get_status_display(),
            'total_itens': total_itens,
            'total_unidades': total_unidades,
            'unidades_recebidas': unidades_recebidas,
            'progresso': int((unidades_recebidas / total_unidades * 100) if total_unidades > 0 else 0),
            'valor_total': float(valor_total),
            'dias_pendentes': dias_pendentes,
            'atrasado': atrasado,
            'dias_atraso': dias_atraso,
            'url': request.build_absolute_uri(reverse('detalhes_encomenda', args=[encomenda.id]))
        })
    
    return JsonResponse({
        'success': True,
        'total_encomendas': len(resultados),
        'encomendas': resultados
    })


@login_required
@group_required(['Administradores'])
def criar_multiplas_pecas(request):
    """
    Cria múltiplas peças em sequência, útil para inicialização rápida
    """
    if request.method == 'POST':
        # Parâmetros para criar as peças
        prefixo = request.POST.get('prefixo', 'P')
        quantidade = request.POST.get('quantidade', '1')
        categoria_id = request.POST.get('categoria')
        nome_base = request.POST.get('nome_base', 'Peça')
        
        try:
            quantidade = int(quantidade)
            if quantidade <= 0 or quantidade > 100:
                messages.error(request, _('Quantidade inválida. Deve ser entre 1 e 100.'))
                return redirect('stock/criar_multiplas_pecas')
            
            # Obter categoria
            categoria = None
            if categoria_id and categoria_id.isdigit():
                try:
                    categoria = CategoriaPeca.objects.get(id=categoria_id)
                except CategoriaPeca.DoesNotExist:
                    pass
            
            # Criar as peças
            pecas_criadas = 0
            ultimo_codigo = None
            
            for i in range(quantidade):
                # Gerar código sequencial
                codigo = gerar_cod_peca_sequencial(prefixo)
                
                # Criar peça
                peca = Peca.objects.create(
                    codigo=codigo,
                    nome=f"{nome_base} {codigo}",
                    categoria=categoria,
                    stock_atual=0,
                    stock_minimo=1,
                    stock_ideal=5
                )
                
                pecas_criadas += 1
                ultimo_codigo = codigo
            
            messages.success(request, _(
                f'{pecas_criadas} peças criadas com sucesso. '
                f'Último código gerado: {ultimo_codigo}'
            ))
            return redirect('stock/listar_pecas')
            
        except ValueError:
            messages.error(request, _('Quantidade deve ser um número inteiro.'))
        except Exception as e:
            messages.error(request, _(f'Erro ao processar: {str(e)}'))
    
    # Obter categorias para o formulário
    categorias = CategoriaPeca.objects.all().order_by('nome')
    
    return render(request, 'stock/criar_multiplas_pecas.html', {
        'categorias': categorias
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def gerar_encomenda_automatica(request):
    """
    Gera uma encomenda automaticamente baseada em necessidades de stock
    """
    if request.method == 'POST':
        # Parâmetros da encomenda
        fornecedor_id = request.POST.get('fornecedor')
        incluir_stock_baixo = request.POST.get('incluir_stock_baixo') == 'on'
        incluir_stock_zero = request.POST.get('incluir_stock_zero') == 'on'
        
        if not fornecedor_id:
            messages.error(request, _('É necessário selecionar um fornecedor.'))
            return redirect('stock/gerar_encomenda_automatica')
        
        try:
            fornecedor = Fornecedor.objects.get(id=fornecedor_id)
            
            # Obter peças fornecidas por este fornecedor
            pecas_fornecedor = FornecedorPeca.objects.filter(fornecedor=fornecedor)
            
            # Filtrar peças com necessidade de compra
            pecas_para_encomendar = []
            
            for associacao in pecas_fornecedor:
                peca = associacao.peca
                
                # Verificar se atende aos critérios de stock
                if (incluir_stock_baixo and peca.stock_atual < peca.stock_minimo and peca.stock_atual > 0) or \
                   (incluir_stock_zero and peca.stock_atual == 0):
                    
                    # Verificar se já existe encomenda pendente para esta peça
                    quantidade_encomendada = ItemEncomenda.objects.filter(
                        peca=peca,
                        encomenda__status__in=['pendente', 'encomendada'],
                        quantidade_recebida__lt=models.F('quantidade')
                    ).aggregate(
                        total=models.Sum(models.F('quantidade') - models.F('quantidade_recebida'))
                    )['total'] or 0
                    
                    # Calcular quantidade a comprar (para chegar ao stock ideal)
                    quantidade_comprar = max(0, peca.stock_ideal - peca.stock_atual - quantidade_encomendada)
                    
                    if quantidade_comprar > 0:
                        pecas_para_encomendar.append({
                            'peca': peca,
                            'associacao': associacao,
                            'quantidade': quantidade_comprar
                        })
            
            # Verificar se há peças para encomendar
            if not pecas_para_encomendar:
                messages.warning(request, _(
                    'Não há peças que atendam aos critérios selecionados. '
                    'Tente incluir mais critérios ou selecione outro fornecedor.'
                ))
                return redirect('stock/gerar_encomenda_automatica')
            
            # Criar a encomenda
            encomenda = EncomendaPeca.objects.create(
                fornecedor=fornecedor,
                data_encomenda=timezone.now().date(),
                status='pendente',
                utilizador=request.user,
                observacoes=_('Encomenda gerada automaticamente pelo sistema')
            )
            
            # Gerar número de pedido sequencial
            ultimo_numero = EncomendaPeca.objects.exclude(id=encomenda.id).order_by('-data_encomenda').values_list('numero_pedido', flat=True).first()
            
            if ultimo_numero and ultimo_numero.startswith('ENC'):
                try:
                    numero = int(ultimo_numero[3:]) + 1
                except ValueError:
                    numero = 1
            else:
                numero = 1
            
            encomenda.numero_pedido = f'ENC{numero:06d}'
            encomenda.save()
            
            # Adicionar itens à encomenda
            for item in pecas_para_encomendar:
                ItemEncomenda.objects.create(
                    encomenda=encomenda,
                    peca=item['peca'],
                    quantidade=item['quantidade'],
                    preco_unitario=item['associacao'].preco_unitario or 0,
                    fornecedor_peca=item['associacao']
                )
            
            messages.success(request, _(
                f'Encomenda "{encomenda.numero_pedido}" criada com {len(pecas_para_encomendar)} itens.'
            ))
            return redirect('stock/detalhes_encomenda', encomenda_id=encomenda.id)
            
        except Fornecedor.DoesNotExist:
            messages.error(request, _('Fornecedor não encontrado.'))
        except Exception as e:
            messages.error(request, _(f'Erro ao processar: {str(e)}'))
    
    # Obter fornecedores ativos
    fornecedores = Fornecedor.objects.filter(ativo=True).order_by('nome')
    
    return render(request, 'stock/gerar_encomenda_automatica.html', {
        'fornecedores': fornecedores
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
@require_POST
def clonar_encomenda(request, encomenda_id):
    """
    Clona uma encomenda existente, criando uma nova com os mesmos itens
    """
    encomenda_original = get_object_or_404(EncomendaPeca, id=encomenda_id)
    
    try:
        # Criar nova encomenda com base na original
        nova_encomenda = EncomendaPeca.objects.create(
            fornecedor=encomenda_original.fornecedor,
            data_encomenda=timezone.now().date(),
            status='pendente',
            prazo_entrega=None,  # Prazo diferente da original
            referencia_interna=encomenda_original.referencia_interna,
            referencia_fornecedor=encomenda_original.referencia_fornecedor,
            observacoes=_('Clonada da encomenda %(original)s') % {'original': encomenda_original.numero_pedido},
            utilizador=request.user
        )
        
        # Gerar número de pedido sequencial
        ultimo_numero = EncomendaPeca.objects.exclude(id=nova_encomenda.id).order_by('-data_encomenda').values_list('numero_pedido', flat=True).first()
        
        if ultimo_numero and ultimo_numero.startswith('ENC'):
            try:
                numero = int(ultimo_numero[3:]) + 1
            except ValueError:
                numero = 1
        else:
            numero = 1
        
        nova_encomenda.numero_pedido = f'ENC{numero:06d}'
        nova_encomenda.save()
        
        # Copiar itens da encomenda original
        itens_originais = ItemEncomenda.objects.filter(encomenda=encomenda_original)
        itens_adicionados = 0
        
        for item_original in itens_originais:
            # Verificar se queremos apenas itens pendentes
            incluir_apenas_pendentes = request.POST.get('apenas_pendentes') == 'on'
            quantidade_pendente = item_original.quantidade - item_original.quantidade_recebida
            
            if not incluir_apenas_pendentes or quantidade_pendente > 0:
                # Determinar quantidade para o novo item
                quantidade = quantidade_pendente if incluir_apenas_pendentes else item_original.quantidade
                
                # Criar novo item
                novo_item = ItemEncomenda.objects.create(
                    encomenda=nova_encomenda,
                    peca=item_original.peca,
                    quantidade=quantidade,
                    quantidade_recebida=0,  # Sempre começa com zero recebido
                    preco_unitario=item_original.preco_unitario,
                    fornecedor_peca=item_original.fornecedor_peca,
                    status='pendente'
                )
                
                itens_adicionados += 1
        
        if itens_adicionados > 0:
            messages.success(request, _(
                f'Encomenda clonada com sucesso. Nova encomenda: {nova_encomenda.numero_pedido} '
                f'com {itens_adicionados} itens.'
            ))
        else:
            # Se não foi adicionado nenhum item, excluir a encomenda criada
            nova_encomenda.delete()
            messages.warning(request, _(
                'Nenhum item foi adicionado à nova encomenda. '
                'A operação foi cancelada.'
            ))
            return redirect('stock/detalhes_encomenda', encomenda_id=encomenda_original.id)
        
        return redirect('stock/detalhes_encomenda', encomenda_id=nova_encomenda.id)
        
    except Exception as e:
        messages.error(request, _(f'Erro ao clonar encomenda: {str(e)}'))
        return redirect('stock/detalhes_encomenda', encomenda_id=encomenda_original.id)


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def atualizar_preco_peca(request, peca_id):
    """
    Atualiza o preço de custo de uma peça com base no último preço de compra
    """
    peca = get_object_or_404(Peca, id=peca_id)
    
    # Obter a última compra desta peça
    ultima_compra = MovimentacaoStock.objects.filter(
        peca=peca,
        tipo='entrada',
        motivo='compra',
        preco_unitario__gt=0
    ).order_by('-data_movimentacao').first()
    
    if not ultima_compra:
        messages.warning(request, _(
            'Não há registos de compra para esta peça. '
            'Impossível atualizar o preço de custo.'
        ))
    else:
        # Atualizar o preço de custo
        preco_anterior = peca.preco_custo
        peca.preco_custo = ultima_compra.preco_unitario
        peca.save(update_fields=['preco_custo'])
        
        messages.success(request, _(
            'Preço de custo atualizado. '
            'De %(anterior)s para %(atual)s.'
        ) % {
            'anterior': preco_anterior or 0,
            'atual': peca.preco_custo
        })
    
    return redirect('stock/detalhes_peca', peca_id=peca.id)


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def calcular_preco_medio_peca(request, peca_id):
    """
    Calcula o preço médio de uma peça com base nas últimas compras
    """
    peca = get_object_or_404(Peca, id=peca_id)
    
    # Obter as últimas 5 compras desta peça
    ultimas_compras = MovimentacaoStock.objects.filter(
        peca=peca,
        tipo='entrada',
        motivo='compra',
        preco_unitario__gt=0
    ).order_by('-data_movimentacao')[:5]
    
    if not ultimas_compras:
        messages.warning(request, _(
            'Não há registos de compra para esta peça. '
            'Impossível calcular o preço médio.'
        ))
    else:
        # Calcular preço médio ponderado pela quantidade
        total_valor = 0
        total_quantidade = 0
        
        for compra in ultimas_compras:
            total_valor += compra.preco_unitario * compra.quantidade
            total_quantidade += compra.quantidade
        
        preco_medio = total_valor / total_quantidade if total_quantidade > 0 else 0
        
        # Atualizar o preço de custo
        preco_anterior = peca.preco_custo
        peca.preco_custo = preco_medio
        peca.save(update_fields=['preco_custo'])
        
        messages.success(request, _(
            'Preço de custo atualizado para a média das últimas %(num)s compras. '
            'De %(anterior)s para %(atual)s.'
        ) % {
            'num': ultimas_compras.count(),
            'anterior': preco_anterior or 0,
            'atual': peca.preco_custo
        })
    
    return redirect('stock/detalhes_peca', peca_id=peca.id)


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def definir_fornecedor_preferencial(request, associacao_id):
    """
    Define um fornecedor como preferencial para uma peça, 
    removendo a marcação de preferencial de outros fornecedores
    """
    associacao = get_object_or_404(FornecedorPeca, id=associacao_id)
    peca = associacao.peca
    
    # Desmarcar outros fornecedores preferenciais para esta peça
    FornecedorPeca.objects.filter(
        peca=peca
    ).update(fornecedor_preferencial=False)
    
    # Marcar este fornecedor como preferencial
    associacao.fornecedor_preferencial = True
    associacao.save(update_fields=['fornecedor_preferencial'])
    
    messages.success(request, _(
        f'Fornecedor "{associacao.fornecedor.nome}" definido como preferencial '
        f'para a peça "{peca.codigo}".'
    ))
    
    return redirect('stock/detalhes_peca', peca_id=peca.id)


@login_required
def api_pesquisar_pecas_fornecedor(request, fornecedor_id):
    """
    API para pesquisar peças que podem ser fornecidas por um fornecedor específico
    Usado para facilitar a adição de peças a encomendas
    """
    try:
        fornecedor = Fornecedor.objects.get(id=fornecedor_id)
    except Fornecedor.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Fornecedor não encontrado'
        }, status=404)
    
    # Parâmetros de pesquisa
    query = request.GET.get('q', '').strip()
    incluir_todas = request.GET.get('incluir_todas') == 'true'
    only_baixo_stock = request.GET.get('baixo_stock') == 'true'
    
    # Obter associações existentes
    associacoes = FornecedorPeca.objects.filter(
        fornecedor=fornecedor
    ).select_related('peca', 'peca__categoria')
    
    # Se não incluir todas, filtrar apenas peças já associadas
    if not incluir_todas:
        pecas_ids = [assoc.peca_id for assoc in associacoes]
        
        # Base query
        pecas = Peca.objects.filter(id__in=pecas_ids)
    else:
        # Todas as peças
        pecas = Peca.objects.all()
    
    # Aplicar filtros adicionais
    if query:
        pecas = pecas.filter(
            models.Q(codigo__icontains=query) | 
            models.Q(nome__icontains=query)
        )
    
    if only_baixo_stock:
        pecas = pecas.filter(
            models.Q(stock_atual__lt=models.F('stock_minimo')) | 
            models.Q(stock_atual=0)
        )
    
    # Limitar resultados
    pecas = pecas.select_related('categoria').order_by('codigo')[:50]
    
    # Criar dicionário para mapear peças a associações
    associacoes_por_peca = {assoc.peca_id: assoc for assoc in associacoes}
    
    # Formatar resultados
    resultados = []
    for peca in pecas:
        resultado = {
            'id': peca.id,
            'codigo': peca.codigo,
            'nome': peca.nome,
            'categoria': peca.categoria.nome if peca.categoria else None,
            'stock_atual': peca.stock_atual,
            'stock_minimo': peca.stock_minimo,
            'status_stock': 'ok' if peca.stock_atual >= peca.stock_minimo else (
                'baixo' if peca.stock_atual > 0 else 'esgotado'
            ),
            'associado': peca.id in associacoes_por_peca
        }
        
        # Adicionar detalhes da associação se existir
        if peca.id in associacoes_por_peca:
            assoc = associacoes_por_peca[peca.id]
            resultado['associacao'] = {
                'id': assoc.id,
                'preco': float(assoc.preco_unitario) if assoc.preco_unitario else None,
                'referencia': assoc.referencia_fornecedor,
                'tempo_entrega': assoc.tempo_entrega,
                'preferencial': assoc.fornecedor_preferencial
            }
        
        resultados.append(resultado)
    
    return JsonResponse({
        'success': True,
        'fornecedor': {
            'id': fornecedor.id,
            'nome': fornecedor.nome
        },
        'total_resultados': len(resultados),
        'resultados': resultados
    })

# ===========================================
# IMPORTAÇÃO/EXPORTAÇÃO DE DADOS
# ===========================================

@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def importar_exportar(request):
    """
    Página principal para importação e exportação de dados
    """
    context = {
        'pandas_disponivel': PANDAS_AVAILABLE
    }
    return render(request, 'stock/importar_exportar.html', context)


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def importar_pecas(request):
    """
    Importa peças de um arquivo CSV ou Excel
    """
    if not PANDAS_AVAILABLE:
        messages.error(request, _('Bibliotecas necessárias para importação não estão instaladas.'))
        return redirect('stock/importar_exportar')
    
    if request.method == 'POST' and request.FILES.get('arquivo_import'):
        arquivo = request.FILES['arquivo_import']
        
        # Verificar extensão do arquivo
        nome, extensao = os.path.splitext(arquivo.name)
        extensao = extensao.lower()
        
        if extensao not in ['.csv', '.xlsx', '.xls']:
            messages.error(request, _('Formato de arquivo não suportado. Use CSV ou Excel (xlsx/xls).'))
            return redirect('stock/importar_pecas')
        
        try:
            # Carregar dados do arquivo
            if extensao == '.csv':
                df = pd.read_csv(arquivo, encoding='utf-8')
            else:
                df = pd.read_excel(arquivo)
            
            # Verificar se as colunas obrigatórias existem
            colunas_obrigatorias = ['codigo', 'nome']
            for coluna in colunas_obrigatorias:
                if coluna not in df.columns:
                    messages.error(request, _(f'Coluna obrigatória "{coluna}" não encontrada no arquivo.'))
                    return redirect('stock/importar_pecas')
            
            # Processar cada linha
            total_importadas = 0
            total_atualizadas = 0
            erros = []
            
            for index, row in df.iterrows():
                try:
                    codigo = str(row['codigo']).strip()
                    nome = str(row['nome']).strip()
                    
                    if not codigo or not nome:
                        erros.append(f"Linha {index+2}: Código ou nome em branco")
                        continue
                    
                    # Verificar se a peça já existe
                    peca, created = Peca.objects.update_or_create(
                        codigo=codigo,
                        defaults={
                            'nome': nome,
                            'descricao': str(row.get('descricao', '')),
                            'categoria': CategoriaPeca.objects.get_or_create(nome=str(row.get('categoria', 'Sem Categoria')))[0],
                            'unidade': str(row.get('unidade', 'un')),
                            'localizacao': str(row.get('localizacao', '')),
                            'notas': str(row.get('notas', '')),
                            'stock_minimo': int(row.get('stock_minimo', 0)),
                            'stock_ideal': int(row.get('stock_ideal', 0)),
                            'preco_custo': float(row.get('preco_custo', 0)),
                            'preco_venda': float(row.get('preco_venda', 0))
                        }
                    )
                    
                    # Atualizar stock inicial se for peça nova
                    if created and 'stock_inicial' in row:
                        stock_inicial = int(row['stock_inicial'])
                        peca.stock_atual = stock_inicial
                        peca.save()
                        
                        # Registrar movimentação de stock
                        if stock_inicial > 0:
                            MovimentacaoStock.objects.create(
                                peca=peca,
                                tipo='entrada',
                                motivo='ajuste',
                                quantidade=stock_inicial,
                                data_movimentacao=timezone.now(),
                                utilizador=request.user,
                                observacao='Stock inicial via importação'
                            )
                    
                    if created:
                        total_importadas += 1
                    else:
                        total_atualizadas += 1
                    
                except Exception as e:
                    erros.append(f"Linha {index+2}: {str(e)}")
            
            # Mensagens de sucesso ou erro
            if total_importadas > 0 or total_atualizadas > 0:
                messages.success(request, _(
                    f'Importação concluída: {total_importadas} peças novas, '
                    f'{total_atualizadas} peças atualizadas.'
                ))
            
            if erros:
                request.session['import_errors'] = erros
                messages.warning(request, _(
                    f'Importação concluída com {len(erros)} erros. '
                    'Clique para ver detalhes.'
                ))
            
            return redirect('stock/listar_pecas')
            
        except Exception as e:
            messages.error(request, _(f'Erro na importação: {str(e)}'))
    
    return render(request, 'stock/importar_pecas.html')


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def exportar_pecas(request):
    """
    Exporta peças para um arquivo CSV ou Excel
    """
    if not PANDAS_AVAILABLE:
        messages.error(request, _('Bibliotecas necessárias para exportação não estão instaladas.'))
        return redirect('stock/importar_exportar')
    
    formato = request.GET.get('formato', 'excel')
    
    # Obter todas as peças
    pecas = Peca.objects.all().select_related('categoria')
    
    # Criar DataFrame
    data = []
    for peca in pecas:
        row = {
            'codigo': peca.codigo,
            'nome': peca.nome,
            'descricao': peca.descricao,
            'categoria': peca.categoria.nome if peca.categoria else '',
            'unidade': peca.unidade,
            'localizacao': peca.localizacao,
            'stock_atual': peca.stock_atual,
            'stock_minimo': peca.stock_minimo,
            'stock_ideal': peca.stock_ideal,
            'preco_custo': float(peca.preco_custo) if peca.preco_custo else 0,
            'preco_venda': float(peca.preco_venda) if peca.preco_venda else 0,
            'notas': peca.notas
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # Exportar nos formatos suportados
    if formato == 'excel':
        # Gerar Excel
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=pecas_export.xlsx'
        
        with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Peças', index=False)
        
        return response
    
    elif formato == 'csv':
        # Gerar CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=pecas_export.csv'
        
        df.to_csv(response, index=False, encoding='utf-8-sig')
        return response
    
    else:
        messages.error(request, _('Formato de exportação não suportado.'))
        return redirect('stock/importar_exportar')


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def importar_fornecedores(request):
    """
    Importa fornecedores de um arquivo CSV ou Excel
    """
    if not PANDAS_AVAILABLE:
        messages.error(request, _('Bibliotecas necessárias para importação não estão instaladas.'))
        return redirect('stock/importar_exportar')
    
    if request.method == 'POST' and request.FILES.get('arquivo_import'):
        arquivo = request.FILES['arquivo_import']
        
        # Verificar extensão do arquivo
        nome, extensao = os.path.splitext(arquivo.name)
        extensao = extensao.lower()
        
        if extensao not in ['.csv', '.xlsx', '.xls']:
            messages.error(request, _('Formato de arquivo não suportado. Use CSV ou Excel (xlsx/xls).'))
            return redirect('stock/importar_fornecedores')
        
        try:
            # Carregar dados do arquivo
            if extensao == '.csv':
                df = pd.read_csv(arquivo, encoding='utf-8')
            else:
                df = pd.read_excel(arquivo)
            
            # Verificar se as colunas obrigatórias existem
            colunas_obrigatorias = ['nome']
            for coluna in colunas_obrigatorias:
                if coluna not in df.columns:
                    messages.error(request, _(f'Coluna obrigatória "{coluna}" não encontrada no arquivo.'))
                    return redirect('stock/importar_fornecedores')
            
            # Processar cada linha
            total_importados = 0
            total_atualizados = 0
            erros = []
            
            for index, row in df.iterrows():
                try:
                    nome = str(row['nome']).strip()
                    
                    if not nome:
                        erros.append(f"Linha {index+2}: Nome em branco")
                        continue
                    
                    # Verificar se o fornecedor já existe
                    fornecedor, created = Fornecedor.objects.update_or_create(
                        nome=nome,
                        defaults={
                            'contacto': str(row.get('contacto', '')),
                            'telefone': str(row.get('telefone', '')),
                            'email': str(row.get('email', '')),
                            'website': str(row.get('website', '')),
                            'notas': str(row.get('notas', '')),
                            'ativo': bool(row.get('ativo', True))
                        }
                    )
                    
                    if created:
                        total_importados += 1
                    else:
                        total_atualizados += 1
                    
                except Exception as e:
                    erros.append(f"Linha {index+2}: {str(e)}")
            
            # Mensagens de sucesso ou erro
            if total_importados > 0 or total_atualizados > 0:
                messages.success(request, _(
                    f'Importação concluída: {total_importados} fornecedores novos, '
                    f'{total_atualizados} fornecedores atualizados.'
                ))
            
            if erros:
                request.session['import_errors'] = erros
                messages.warning(request, _(
                    f'Importação concluída com {len(erros)} erros. '
                    'Clique para ver detalhes.'
                ))
            
            return redirect('stock/listar_fornecedores')
            
        except Exception as e:
            messages.error(request, _(f'Erro na importação: {str(e)}'))
    
    return render(request, 'stock/importar_fornecedores.html')


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def exportar_fornecedores(request):
    """
    Exporta fornecedores para um arquivo CSV ou Excel
    """
    if not PANDAS_AVAILABLE:
        messages.error(request, _('Bibliotecas necessárias para exportação não estão instaladas.'))
        return redirect('stock/importar_exportar')
    
    formato = request.GET.get('formato', 'excel')
    
    # Obter todos os fornecedores
    fornecedores = Fornecedor.objects.all()
    
    # Criar DataFrame
    data = []
    for fornecedor in fornecedores:
        row = {
            'nome': fornecedor.nome,
            'contacto': fornecedor.contacto,
            'telefone': fornecedor.telefone,
            'email': fornecedor.email,
            'website': fornecedor.website,
            'notas': fornecedor.notas,
            'ativo': fornecedor.ativo
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # Exportar nos formatos suportados
    if formato == 'excel':
        # Gerar Excel
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=fornecedores_export.xlsx'
        
        with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Fornecedores', index=False)
        
        return response
    
    elif formato == 'csv':
        # Gerar CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=fornecedores_export.csv'
        
        df.to_csv(response, index=False, encoding='utf-8-sig')
        return response
    
    else:
        messages.error(request, _('Formato de exportação não suportado.'))
        return redirect('stock/importar_exportar')


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def importar_associacoes(request):
    """
    Importa associações entre peças e fornecedores de um arquivo CSV ou Excel
    """
    if not PANDAS_AVAILABLE:
        messages.error(request, _('Bibliotecas necessárias para importação não estão instaladas.'))
        return redirect('stock/importar_exportar')
    
    if request.method == 'POST' and request.FILES.get('arquivo_import'):
        arquivo = request.FILES['arquivo_import']
        
        # Verificar extensão do arquivo
        nome, extensao = os.path.splitext(arquivo.name)
        extensao = extensao.lower()
        
        if extensao not in ['.csv', '.xlsx', '.xls']:
            messages.error(request, _('Formato de arquivo não suportado. Use CSV ou Excel (xlsx/xls).'))
            return redirect('stock/importar_associacoes')
        
        try:
            # Carregar dados do arquivo
            if extensao == '.csv':
                df = pd.read_csv(arquivo, encoding='utf-8')
            else:
                df = pd.read_excel(arquivo)
            
            # Verificar se as colunas obrigatórias existem
            colunas_obrigatorias = ['codigo_peca', 'nome_fornecedor']
            for coluna in colunas_obrigatorias:
                if coluna not in df.columns:
                    messages.error(request, _(f'Coluna obrigatória "{coluna}" não encontrada no arquivo.'))
                    return redirect('stock/importar_associacoes')
            
            # Processar cada linha
            total_importadas = 0
            total_atualizadas = 0
            erros = []
            
            for index, row in df.iterrows():
                try:
                    codigo_peca = str(row['codigo_peca']).strip()
                    nome_fornecedor = str(row['nome_fornecedor']).strip()
                    
                    if not codigo_peca or not nome_fornecedor:
                        erros.append(f"Linha {index+2}: Código da peça ou nome do fornecedor em branco")
                        continue
                    
                    # Obter objetos correspondentes
                    try:
                        peca = Peca.objects.get(codigo=codigo_peca)
                    except Peca.DoesNotExist:
                        erros.append(f"Linha {index+2}: Peça com código '{codigo_peca}' não encontrada")
                        continue
                    
                    try:
                        fornecedor = Fornecedor.objects.get(nome=nome_fornecedor)
                    except Fornecedor.DoesNotExist:
                        erros.append(f"Linha {index+2}: Fornecedor '{nome_fornecedor}' não encontrado")
                        continue
                    
                    # Valores para criar/atualizar
                    defaults = {
                        'referencia_fornecedor': str(row.get('referencia_fornecedor', '')),
                        'tempo_entrega': int(row.get('tempo_entrega', 0)) if pd.notna(row.get('tempo_entrega', 0)) else 0,
                        'notas': str(row.get('notas', '')),
                    }
                    
                    # Verificar se temos preço
                    if 'preco_unitario' in row and pd.notna(row['preco_unitario']):
                        defaults['preco_unitario'] = float(row['preco_unitario'])
                    
                    # Verificar se é fornecedor preferencial
                    if 'preferencial' in row:
                        defaults['fornecedor_preferencial'] = bool(row['preferencial'])
                    
                    # Verificar se a associação já existe
                    associacao, created = FornecedorPeca.objects.update_or_create(
                        peca=peca,
                        fornecedor=fornecedor,
                        defaults=defaults
                    )
                    
                    # Registrar histórico de preço se necessário
                    if created and 'preco_unitario' in row and pd.notna(row['preco_unitario']):
                        HistoricoPrecoFornecedor.objects.create(
                            fornecedor_peca=associacao,
                            preco_unitario=float(row['preco_unitario']),
                            utilizador=request.user
                        )
                    
                    if created:
                        total_importadas += 1
                    else:
                        total_atualizadas += 1
                    
                except Exception as e:
                    erros.append(f"Linha {index+2}: {str(e)}")
            
            # Mensagens de sucesso ou erro
            if total_importadas > 0 or total_atualizadas > 0:
                messages.success(request, _(
                    f'Importação concluída: {total_importadas} associações novas, '
                    f'{total_atualizadas} associações atualizadas.'
                ))
            
            if erros:
                request.session['import_errors'] = erros
                messages.warning(request, _(
                    f'Importação concluída com {len(erros)} erros. '
                    'Clique para ver detalhes.'
                ))
            
            return redirect('stock/associar_fornecedores_pecas')
            
        except Exception as e:
            messages.error(request, _(f'Erro na importação: {str(e)}'))
    
    return render(request, 'stock/importar_associacoes.html')


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def associar_fornecedores_pecas(request):
    """
    Página principal para gestão de associações entre peças e fornecedores
    """
    # Contexto inicial
    context = {
        'tab_active': request.GET.get('tab', 'peca')
    }
    
    # Se temos peça ou fornecedor específico
    peca_id = request.GET.get('peca_id')
    fornecedor_id = request.GET.get('fornecedor_id')
    
    if peca_id:
        context['peca'] = get_object_or_404(Peca, id=peca_id)
        context['tab_active'] = 'peca'
    
    if fornecedor_id:
        context['fornecedor'] = get_object_or_404(Fornecedor, id=fornecedor_id)
        context['tab_active'] = 'fornecedor'
    
    return render(request, 'stock/associar_fornecedores_pecas.html', context)


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def adicionar_varias_pecas_fornecedor(request, fornecedor_id):
    """
    Adiciona múltiplas peças a um fornecedor de uma vez
    """
    fornecedor = get_object_or_404(Fornecedor, id=fornecedor_id)
    
    if request.method == 'POST':
        # Processar formulário
        pecas_ids = request.POST.getlist('pecas')
        referencia_padrao = request.POST.get('referencia_padrao', '')
        preco_padrao = request.POST.get('preco_padrao', 0)
        tempo_entrega_padrao = request.POST.get('tempo_entrega_padrao', 0)
        preferencial = request.POST.get('preferencial', False) == 'on'
        
        try:
            # Converter para tipos apropriados
            preco_padrao = float(preco_padrao) if preco_padrao else 0
            tempo_entrega_padrao = int(tempo_entrega_padrao) if tempo_entrega_padrao else 0
            
            # Processar cada peça selecionada
            total_adicionadas = 0
            total_atualizadas = 0
            
            for peca_id in pecas_ids:
                try:
                    peca = Peca.objects.get(id=peca_id)
                    associacao, created = FornecedorPeca.objects.update_or_create(
                        peca=peca,
                        fornecedor=fornecedor,
                        defaults={
                            'referencia_fornecedor': referencia_padrao,
                            'preco_unitario': preco_padrao,
                            'tempo_entrega': tempo_entrega_padrao,
                            'fornecedor_preferencial': preferencial
                        }
                    )
                    
                    # Registrar histórico de preço se necessário
                    if created and preco_padrao > 0:
                        HistoricoPrecoFornecedor.objects.create(
                            fornecedor_peca=associacao,
                            preco_unitario=preco_padrao,
                            utilizador=request.user
                        )
                    
                    if created:
                        total_adicionadas += 1
                    else:
                        total_atualizadas += 1
                
                except Peca.DoesNotExist:
                    messages.warning(request, _(f'Peça ID {peca_id} não encontrada, pulando...'))
            
            # Mensagens de sucesso
            if total_adicionadas > 0 or total_atualizadas > 0:
                messages.success(request, _(
                    f'Processamento concluído: {total_adicionadas} associações novas, '
                    f'{total_atualizadas} associações atualizadas.'
                ))
                return redirect('stock/detalhes_fornecedor', fornecedor_id=fornecedor.id)
            else:
                messages.warning(request, _('Nenhuma peça foi processada. Verifique suas seleções.'))
        
        except ValueError as e:
            messages.error(request, _(f'Erro ao processar valores: {str(e)}'))
    
    # Buscar todas as peças para seleção
    pecas = Peca.objects.all().select_related('categoria')
    
    # Obter peças que já são fornecidas por este fornecedor
    pecas_existentes = FornecedorPeca.objects.filter(
        fornecedor=fornecedor
    ).values_list('peca_id', flat=True)
    
    # Contexto para o template
    context = {
        'fornecedor': fornecedor,
        'pecas': pecas,
        'pecas_existentes': list(pecas_existentes)
    }
    
    return render(request, 'stock/adicionar_varias_pecas_fornecedor.html', context)


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def adicionar_varios_fornecedores_peca(request, peca_id):
    """
    Adiciona múltiplos fornecedores a uma peça de uma vez
    """
    peca = get_object_or_404(Peca, id=peca_id)
    
    if request.method == 'POST':
        # Processar formulário
        fornecedores_ids = request.POST.getlist('fornecedores')
        referencia_padrao = request.POST.get('referencia_padrao', '')
        preco_padrao = request.POST.get('preco_padrao', 0)
        tempo_entrega_padrao = request.POST.get('tempo_entrega_padrao', 0)
        preferencial = request.POST.get('preferencial', False) == 'on'
        
        try:
            # Converter para tipos apropriados
            preco_padrao = float(preco_padrao) if preco_padrao else 0
            tempo_entrega_padrao = int(tempo_entrega_padrao) if tempo_entrega_padrao else 0
            
            # Se múltiplos fornecedores, não podemos marcar todos como preferenciais
            if preferencial and len(fornecedores_ids) > 1:
                messages.warning(request, _(
                    'Múltiplos fornecedores selecionados. '
                    'A opção "Fornecedor Preferencial" será ignorada.'
                ))
                preferencial = False
            
            # Processar cada fornecedor selecionado
            total_adicionados = 0
            total_atualizados = 0
            
            for fornecedor_id in fornecedores_ids:
                try:
                    fornecedor = Fornecedor.objects.get(id=fornecedor_id)
                    
                    # Determinar se este é o fornecedor preferencial
                    # Só permitir um fornecedor preferencial por peça
                    is_preferencial = preferencial
                    if is_preferencial:
                        # Desmarcar outros fornecedores preferenciais para esta peça
                        FornecedorPeca.objects.filter(
                            peca=peca, 
                            fornecedor_preferencial=True
                        ).exclude(fornecedor=fornecedor).update(
                            fornecedor_preferencial=False
                        )
                    
                    associacao, created = FornecedorPeca.objects.update_or_create(
                        peca=peca,
                        fornecedor=fornecedor,
                        defaults={
                            'referencia_fornecedor': referencia_padrao,
                            'preco_unitario': preco_padrao,
                            'tempo_entrega': tempo_entrega_padrao,
                            'fornecedor_preferencial': is_preferencial
                        }
                    )
                    
                    # Registrar histórico de preço se necessário
                    if created and preco_padrao > 0:
                        HistoricoPrecoFornecedor.objects.create(
                            fornecedor_peca=associacao,
                            preco_unitario=preco_padrao,
                            utilizador=request.user
                        )
                    
                    if created:
                        total_adicionados += 1
                    else:
                        total_atualizados += 1
                
                except Fornecedor.DoesNotExist:
                    messages.warning(request, _(f'Fornecedor ID {fornecedor_id} não encontrado, pulando...'))
            
            # Mensagens de sucesso
            if total_adicionados > 0 or total_atualizados > 0:
                messages.success(request, _(
                    f'Processamento concluído: {total_adicionados} associações novas, '
                    f'{total_atualizados} associações atualizadas.'
                ))
                return redirect('stock/detalhes_peca', peca_id=peca.id)
            else:
                messages.warning(request, _('Nenhum fornecedor foi processado. Verifique suas seleções.'))
        
        except ValueError as e:
            messages.error(request, _(f'Erro ao processar valores: {str(e)}'))
    
    # Buscar todos os fornecedores para seleção
    fornecedores = Fornecedor.objects.filter(ativo=True)
    
    # Obter fornecedores que já fornecem esta peça
    fornecedores_existentes = FornecedorPeca.objects.filter(
        peca=peca
    ).values_list('fornecedor_id', flat=True)
    
    # Contexto para o template
    context = {
        'peca': peca,
        'fornecedores': fornecedores,
        'fornecedores_existentes': list(fornecedores_existentes)
    }
    
    return render(request, 'stock/adicionar_varios_fornecedores_peca.html', context)


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
@require_POST
def excluir_associacao_peca_fornecedor(request, associacao_id):
    """
    Exclui uma associação entre peça e fornecedor
    """
    associacao = get_object_or_404(FornecedorPeca, id=associacao_id)
    
    # Guardar referências antes de excluir
    peca_id = associacao.peca.id
    fornecedor_id = associacao.fornecedor.id
    
    # Verificar se veio de uma página de peça ou fornecedor
    referer = request.META.get('HTTP_REFERER', '')
    from_peca = f'peca/{peca_id}' in referer
    from_fornecedor = f'fornecedor/{fornecedor_id}' in referer
    
    # Excluir associação
    associacao.delete()
    
    messages.success(request, _('Associação excluída com sucesso.'))
    
    # Redirecionar de volta para a página apropriada
    if from_peca:
        return redirect('stock/detalhes_peca', peca_id=peca_id)
    elif from_fornecedor:
        return redirect('stock/detalhes_fornecedor', fornecedor_id=fornecedor_id)
    else:
        return redirect('stock/associar_fornecedores_pecas')


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def api_baixo_stock(request):
    """
    API para listar peças com stock baixo (abaixo do mínimo) ou zero
    """
    # Filtrar peças com stock baixo
    pecas_baixo = Peca.objects.filter(
        stock_atual__lt=models.F('stock_minimo'),
        stock_atual__gt=0
    ).order_by('stock_atual')
    
    # Filtrar peças com stock zero
    pecas_zero = Peca.objects.filter(stock_atual=0).order_by('codigo')
    
    # Formatar resultados
    baixo_stock = []
    for peca in pecas_baixo:
        fornecedor_pref = FornecedorPeca.objects.filter(
            peca=peca, 
            fornecedor_preferencial=True
        ).select_related('fornecedor').first()
        
        baixo_stock.append({
            'id': peca.id,
            'codigo': peca.codigo,
            'nome': peca.nome,
            'categoria': peca.categoria.nome if peca.categoria else None,
            'stock_atual': peca.stock_atual,
            'stock_minimo': peca.stock_minimo,
            'stock_ideal': peca.stock_ideal,
            'fornecedor': fornecedor_pref.fornecedor.nome if fornecedor_pref else None,
            'url': request.build_absolute_uri(reverse('detalhes_peca', args=[peca.id]))
        })
    
    zero_stock = []
    for peca in pecas_zero:
        fornecedor_pref = FornecedorPeca.objects.filter(
            peca=peca, 
            fornecedor_preferencial=True
        ).select_related('fornecedor').first()
        
        zero_stock.append({
            'id': peca.id,
            'codigo': peca.codigo,
            'nome': peca.nome,
            'categoria': peca.categoria.nome if peca.categoria else None,
            'stock_minimo': peca.stock_minimo,
            'stock_ideal': peca.stock_ideal,
            'fornecedor': fornecedor_pref.fornecedor.nome if fornecedor_pref else None,
            'url': request.build_absolute_uri(reverse('detalhes_peca', args=[peca.id]))
        })
    
    return JsonResponse({
        'success': True,
        'baixo_stock': {
            'total': len(baixo_stock),
            'items': baixo_stock
        },
        'zero_stock': {
            'total': len(zero_stock),
            'items': zero_stock
        }
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def api_listar_pecas_fornecedor(request, fornecedor_id):
    """
    API para listar todas as peças de um fornecedor
    """
    fornecedor = get_object_or_404(Fornecedor, id=fornecedor_id)
    
    # Obter associações deste fornecedor
    associacoes = FornecedorPeca.objects.filter(
        fornecedor=fornecedor
    ).select_related('peca', 'peca__categoria')
    
    # Formatar resultados
    pecas = []
    for assoc in associacoes:
        pecas.append({
            'id': assoc.peca.id,
            'codigo': assoc.peca.codigo,
            'nome': assoc.peca.nome,
            'categoria': assoc.peca.categoria.nome if assoc.peca.categoria else None,
            'referencia': assoc.referencia_fornecedor,
            'preco': float(assoc.preco_unitario) if assoc.preco_unitario else None,
            'preferencial': assoc.fornecedor_preferencial,
            'tempo_entrega': assoc.tempo_entrega,
            'stock_atual': assoc.peca.stock_atual,
            'url': request.build_absolute_uri(reverse('detalhes_peca', args=[assoc.peca.id]))
        })
    
    return JsonResponse({
        'success': True,
        'fornecedor': {
            'id': fornecedor.id,
            'nome': fornecedor.nome
        },
        'total_pecas': len(pecas),
        'pecas': pecas
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def api_listar_itens_encomenda(request, encomenda_id):
    """
    API para listar itens de uma encomenda
    """
    encomenda = get_object_or_404(EncomendaPeca, id=encomenda_id)
    
    # Obter itens desta encomenda
    itens = ItemEncomenda.objects.filter(
        encomenda=encomenda
    ).select_related('peca')
    
    # Formatar resultados
    items_list = []
    for item in itens:
        items_list.append({
            'id': item.id,
            'peca_id': item.peca.id,
            'peca_codigo': item.peca.codigo,
            'peca_nome': item.peca.nome,
            'quantidade': item.quantidade,
            'quantidade_recebida': item.quantidade_recebida,
            'preco_unitario': float(item.preco_unitario) if item.preco_unitario else 0,
            'valor_total': float(item.preco_unitario * item.quantidade) if item.preco_unitario else 0,
            'status': item.status,
            'status_display': item.get_status_display()
        })
    
    return JsonResponse({
        'success': True,
        'encomenda': {
            'id': encomenda.id,
            'numero_pedido': encomenda.numero_pedido,
            'status': encomenda.status,
            'status_display': encomenda.get_status_display()
        },
        'total_itens': len(items_list),
        'total_recebidos': sum(item['quantidade_recebida'] for item in items_list),
        'total_pendentes': sum(item['quantidade'] - item['quantidade_recebida'] for item in items_list),
        'valor_total': sum(item['valor_total'] for item in items_list),
        'itens': items_list
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def api_precos_fornecedor(request):
    """
    API para obter preços de peças de um fornecedor específico
    """
    fornecedor_id = request.GET.get('fornecedor_id')
    pecas_ids = request.GET.getlist('pecas_ids[]')
    
    if not fornecedor_id or not pecas_ids:
        return JsonResponse({
            'success': False,
            'error': 'Parâmetros incompletos'
        }, status=400)
    
    try:
        fornecedor = Fornecedor.objects.get(id=fornecedor_id)
    except Fornecedor.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Fornecedor não encontrado'
        }, status=404)
    
    # Obter preços para as peças solicitadas
    associacoes = FornecedorPeca.objects.filter(
        fornecedor=fornecedor,
        peca_id__in=pecas_ids
    ).select_related('peca')
    
    # Formatar resultados
    precos = {}
    for assoc in associacoes:
        precos[str(assoc.peca.id)] = {
            'preco': float(assoc.preco_unitario) if assoc.preco_unitario else 0,
            'referencia': assoc.referencia_fornecedor
        }
    
    return JsonResponse({
        'success': True,
        'fornecedor': {
            'id': fornecedor.id,
            'nome': fornecedor.nome
        },
        'precos': precos
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def api_estatisticas_consumo_pecas(request):
    """
    API para estatísticas de consumo de peças por período
    """
    # Parâmetros
    periodo = request.GET.get('periodo', '30')  # dias
    limit = request.GET.get('limit', '10')      # top N peças
    
    try:
        periodo = int(periodo)
        limit = int(limit)
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'Parâmetros inválidos'
        }, status=400)
    
    # Data limite para o período
    data_limite = timezone.now() - timedelta(days=periodo)
    
    # Obter movimentações de saída no período
    saidas = MovimentacaoStock.objects.filter(
        tipo='saida',
        data_movimentacao__gte=data_limite
    ).select_related('peca')
    
    # Agrupar por peça e somar quantidades
    consumo_por_peca = {}
    for saida in saidas:
        peca_id = saida.peca.id
        if peca_id not in consumo_por_peca:
            consumo_por_peca[peca_id] = {
                'peca': saida.peca,
                'quantidade': 0,
                'valor': 0
            }
        
        consumo_por_peca[peca_id]['quantidade'] += saida.quantidade
        if saida.preco_unitario:
            consumo_por_peca[peca_id]['valor'] += saida.quantidade * saida.preco_unitario
    
    # Ordenar por quantidade e obter top N
    top_consumo = sorted(
        consumo_por_peca.values(),
        key=lambda x: x['quantidade'],
        reverse=True
    )[:limit]
    
    # Formatar resultados
    resultados = []
    for item in top_consumo:
        resultados.append({
            'id': item['peca'].id,
            'codigo': item['peca'].codigo,
            'nome': item['peca'].nome,
            'quantidade': item['quantidade'],
            'valor': float(item['valor']),
            'url': request.build_absolute_uri(reverse('detalhes_peca', args=[item['peca'].id]))
        })
    
    return JsonResponse({
        'success': True,
        'periodo': periodo,
        'data_inicio': data_limite.strftime('%Y-%m-%d'),
        'data_fim': timezone.now().strftime('%Y-%m-%d'),
        'total_resultados': len(resultados),
        'resultados': resultados
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def api_estatisticas_compras_fornecedores(request):
    """
    API para estatísticas de compras por fornecedor
    """
    # Parâmetros
    periodo = request.GET.get('periodo', '180')  # dias
    limit = request.GET.get('limit', '10')       # top N fornecedores
    
    try:
        periodo = int(periodo)
        limit = int(limit)
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'Parâmetros inválidos'
        }, status=400)
    
    # Data limite para o período
    data_limite = timezone.now() - timedelta(days=periodo)
    
    # Obter movimentações de entrada (compras) no período
    entradas = MovimentacaoStock.objects.filter(
        tipo='entrada',
        motivo='compra',
        data_movimentacao__gte=data_limite,
        fornecedor__isnull=False
    ).select_related('fornecedor')
    
    # Agrupar por fornecedor e somar valores
    compras_por_fornecedor = {}
    for entrada in entradas:
        fornecedor_id = entrada.fornecedor.id
        if fornecedor_id not in compras_por_fornecedor:
            compras_por_fornecedor[fornecedor_id] = {
                'fornecedor': entrada.fornecedor,
                'valor': 0,
                'quantidade_itens': 0
            }
        
        if entrada.preco_unitario:
            compras_por_fornecedor[fornecedor_id]['valor'] += entrada.quantidade * entrada.preco_unitario
        
        compras_por_fornecedor[fornecedor_id]['quantidade_itens'] += 1
    
    # Ordenar por valor e obter top N
    top_fornecedores = sorted(
        compras_por_fornecedor.values(),
        key=lambda x: x['valor'],
        reverse=True
    )[:limit]
    
    # Formatar resultados
    resultados = []
    for item in top_fornecedores:
        resultados.append({
            'id': item['fornecedor'].id,
            'nome': item['fornecedor'].nome,
            'valor': float(item['valor']),
            'quantidade_itens': item['quantidade_itens'],
            'url': request.build_absolute_uri(reverse('detalhes_fornecedor', args=[item['fornecedor'].id]))
        })
    
    return JsonResponse({
        'success': True,
        'periodo': periodo,
        'data_inicio': data_limite.strftime('%Y-%m-%d'),
        'data_fim': timezone.now().strftime('%Y-%m-%d'),
        'total_resultados': len(resultados),
        'resultados': resultados
    })

# ===========================================
# GESTÃO DE ENCOMENDAS
# ===========================================

@login_required
def listar_encomendas(request):
    """
    Lista todas as encomendas com filtros e paginação
    """
    # Parâmetros de filtro
    status = request.GET.get('status', '')
    fornecedor_id = request.GET.get('fornecedor', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    searchterm = request.GET.get('q', '').strip()
    
    # Query base
    encomendas = EncomendaPeca.objects.all()
    
    # Aplicar filtros
    if status:
        encomendas = encomendas.filter(status=status)
    
    if fornecedor_id and fornecedor_id.isdigit():
        encomendas = encomendas.filter(fornecedor_id=fornecedor_id)
    
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            encomendas = encomendas.filter(data_encomenda__gte=data_inicio_obj)
        except ValueError:
            pass
    
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            encomendas = encomendas.filter(data_encomenda__lte=data_fim_obj)
        except ValueError:
            pass
    
    if searchterm:
        encomendas = encomendas.filter(
            models.Q(numero_pedido__icontains=searchterm) | 
            models.Q(referencia_interna__icontains=searchterm) | 
            models.Q(referencia_fornecedor__icontains=searchterm) | 
            models.Q(fornecedor__nome__icontains=searchterm)
        )
    
    # Ordenação
    encomendas = encomendas.select_related('fornecedor').order_by('-data_encomenda')
    
    # Paginação
    paginator = Paginator(encomendas, 25)  # 25 encomendas por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'stock/listar_encomendas.html', {
        'page_obj': page_obj,
        'filtros': {
            'status': status,
            'fornecedor': fornecedor_id,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'q': searchterm
        },
        'total_resultados': paginator.count
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def adicionar_encomenda(request, fornecedor_id=None):
    """
    Adiciona uma nova encomenda ao sistema
    """
    # Contexto inicial
    contexto = {}
    
    # Se temos um fornecedor específico
    if fornecedor_id:
        fornecedor = get_object_or_404(Fornecedor, id=fornecedor_id)
        contexto['fornecedor'] = fornecedor
    
    if request.method == 'POST':
        form = EncomendaPecaForm(request.POST)
        
        # Predefinir fornecedor se fornecido
        if not form.has_field('fornecedor') and fornecedor_id:
            form.instance.fornecedor_id = fornecedor_id
        
        if form.is_valid():
            encomenda = form.save(commit=False)
            encomenda.utilizador = request.user
            
            # Gerar número de pedido sequencial, se não fornecido
            if not encomenda.numero_pedido:
                ultimo_numero = EncomendaPeca.objects.all().order_by('-data_encomenda').values_list('numero_pedido', flat=True).first()
                
                if ultimo_numero and ultimo_numero.startswith('ENC'):
                    try:
                        numero = int(ultimo_numero[3:]) + 1
                    except ValueError:
                        numero = 1
                else:
                    numero = 1
                
                encomenda.numero_pedido = f'ENC{numero:06d}'
            
            encomenda.save()
            
            messages.success(request, _(f'Encomenda "{encomenda.numero_pedido}" criada com sucesso.'))
            return redirect('stock/detalhes_encomenda', encomenda_id=encomenda.id)
    else:
        # Formulário vazio
        dados_iniciais = {'data_encomenda': timezone.now().date()}
        
        if fornecedor_id:
            dados_iniciais['fornecedor'] = fornecedor_id
        
        form = EncomendaPecaForm(initial=dados_iniciais)
        
        # Esconder campo de fornecedor se já definido
        if fornecedor_id:
            form.fields.pop('fornecedor', None)
    
    contexto['form'] = form
    return render(request, 'stock/form_encomenda.html', contexto)


@login_required
def detalhes_encomenda(request, encomenda_id):
    """
    Exibe os detalhes de uma encomenda específica
    """
    encomenda = get_object_or_404(EncomendaPeca, id=encomenda_id)
    
    # Itens desta encomenda
    itens = ItemEncomenda.objects.filter(
        encomenda=encomenda
    ).select_related('peca').order_by('peca__codigo')
    
    # Calcular totais
    total_valor = sum(item.quantidade * item.preco_unitario for item in itens if item.preco_unitario)
    total_itens = itens.count()
    total_unidades = sum(item.quantidade for item in itens)
    unidades_recebidas = sum(item.quantidade_recebida for item in itens)
    
    return render(request, 'stock/detalhes_encomenda.html', {
        'encomenda': encomenda,
        'itens': itens,
        'total_valor': total_valor,
        'total_itens': total_itens,
        'total_unidades': total_unidades,
        'unidades_recebidas': unidades_recebidas,
        'percentual_recebido': int((unidades_recebidas / total_unidades) * 100) if total_unidades > 0 else 0
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def editar_encomenda(request, encomenda_id):
    """
    Edita uma encomenda existente
    """
    encomenda = get_object_or_404(EncomendaPeca, id=encomenda_id)
    
    if request.method == 'POST':
        form = EncomendaPecaForm(request.POST, instance=encomenda)
        if form.is_valid():
            encomenda = form.save()
            messages.success(request, _(f'Encomenda "{encomenda.numero_pedido}" atualizada com sucesso.'))
            return redirect('stock/detalhes_encomenda', encomenda_id=encomenda.id)
    else:
        form = EncomendaPecaForm(instance=encomenda)
    
    return render(request, 'stock/form_encomenda.html', {
        'form': form,
        'encomenda': encomenda
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def excluir_encomenda(request, encomenda_id):
    """
    Exclui uma encomenda existente se não houver itens recebidos
    """
    encomenda = get_object_or_404(EncomendaPeca, id=encomenda_id)
    
    # Verificar se há itens com quantidades recebidas
    itens_recebidos = ItemEncomenda.objects.filter(
        encomenda=encomenda, quantidade_recebida__gt=0
    ).exists()
    
    if request.method == 'POST':
        if itens_recebidos:
            messages.error(request, _(
                'Não é possível excluir esta encomenda '
                'porque já existem itens recebidos.'
            ))
        else:
            numero_pedido = encomenda.numero_pedido  # Guardar para mensagem
            encomenda.delete()
            messages.success(request, _(f'Encomenda "{numero_pedido}" excluída com sucesso.'))
            return redirect('stock/listar_encomendas')
    
    return render(request, 'stock/excluir_encomenda.html', {
        'encomenda': encomenda,
        'itens_recebidos': itens_recebidos
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def adicionar_item_encomenda(request, encomenda_id):
    """
    Adiciona um novo item a uma encomenda
    """
    encomenda = get_object_or_404(EncomendaPeca, id=encomenda_id)
    
    if request.method == 'POST':
        form = ItemEncomendaForm(request.POST)
        
        # Predefinir a encomenda
        form.instance.encomenda = encomenda
        
        if form.is_valid():
            item = form.save()
            
            # Associar ao fornecedor_peca se existir
            try:
                fornecedor_peca = FornecedorPeca.objects.get(
                    fornecedor=encomenda.fornecedor,
                    peca=item.peca
                )
                item.fornecedor_peca = fornecedor_peca
                item.save()
            except FornecedorPeca.DoesNotExist:
                pass
            
            messages.success(request, _(f'Item "{item.peca.codigo}" adicionado com sucesso à encomenda.'))
            
            # Verificar se devemos adicionar outro item
            if 'save_and_add' in request.POST:
                return redirect('stock/adicionar_item_encomenda', encomenda_id=encomenda.id)
            else:
                return redirect('stock/detalhes_encomenda', encomenda_id=encomenda.id)
    else:
        form = ItemEncomendaForm()
        
        # Filtrar apenas peças do fornecedor, se houver configuração para isso
        # TODO: Adicionar configuração para controlar isso
        filtrar_apenas_fornecedor = False  # Temporário até implementar a configuração
        
        if filtrar_apenas_fornecedor:
            pecas_fornecedor = FornecedorPeca.objects.filter(
                fornecedor=encomenda.fornecedor
            ).values_list('peca_id', flat=True)
            
            form.fields['peca'].queryset = Peca.objects.filter(
                id__in=pecas_fornecedor
            ).order_by('codigo')
    
    return render(request, 'stock/adicionar_item_encomenda.html', {
        'form': form,
        'encomenda': encomenda
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def editar_item_encomenda(request, item_id):
    """
    Edita um item de encomenda existente
    """
    item = get_object_or_404(ItemEncomenda, id=item_id)
    encomenda = item.encomenda
    
    if request.method == 'POST':
        form = ItemEncomendaForm(request.POST, instance=item)
        if form.is_valid():
            item = form.save()
            
            # Atualizar associação ao fornecedor_peca se mudou a peça
            if form.has_changed() and 'peca' in form.changed_data:
                try:
                    fornecedor_peca = FornecedorPeca.objects.get(
                        fornecedor=encomenda.fornecedor,
                        peca=item.peca
                    )
                    item.fornecedor_peca = fornecedor_peca
                    item.save()
                except FornecedorPeca.DoesNotExist:
                    item.fornecedor_peca = None
                    item.save()
            
            messages.success(request, _(f'Item "{item.peca.codigo}" atualizado com sucesso.'))
            return redirect('stock/detalhes_encomenda', encomenda_id=encomenda.id)
    else:
        form = ItemEncomendaForm(instance=item)
    
    return render(request, 'stock/editar_item_encomenda.html', {
        'form': form,
        'item': item,
        'encomenda': encomenda
    })


@login_required
@group_required(['Administradores', 'Gestores de Stock'])
def excluir_item_encomenda(request, item_id):
    """
    Exclui um item de encomenda existente se não houver quantidades recebidas
    """
    item = get_object_or_404(ItemEncomenda, id=item_id)
    encomenda = item.encomenda
    
    if request.method == 'POST':
        if item.quantidade_recebida > 0:
            messages.error(request, _(
                'Não é possível excluir este item porque já existem quantidades recebidas.'
            ))
        else:
            peca_codigo = item.peca.codigo  # Guardar para mensagem
            item.delete()
            messages.success(request, _(f'Item "{peca_codigo}" excluído com sucesso.'))
        
        return redirect('stock/detalhes_encomenda', encomenda_id=encomenda.id)
    
    return render(request, 'stock/excluir_item_encomenda.html', {
        'item': item,
        'encomenda': encomenda
    })