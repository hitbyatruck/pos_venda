from django.urls import path
from . import views

app_name = 'stock'

urlpatterns = [
    # ==============================
    # DASHBOARD E PÁGINAS PRINCIPAIS
    # ==============================
    path('dashboard/', views.dashboard_stock, name='dashboard_stock'),
    # path('configuracoes/', views.configuracoes_stock, name='configuracoes_stock'),
    
    # ==============================
    # GESTÃO DE PEÇAS
    # ==============================
    # Listagens e visões gerais
    path('pecas/', views.listar_pecas, name='listar_pecas'),
    path('pecas/baixo-stock/', views.pecas_baixo_stock, name='pecas_baixo_stock'),
    path('pecas/registar-entrada/', views.registar_entrada, name='registar_entrada'),
    path('pecas/registar-saida/', views.registar_saida, name='registar_saida'),

    # CRUD de peças
    path('pecas/adicionar/', views.adicionar_peca, name='adicionar_peca'),
    path('pecas/<int:peca_id>/', views.detalhes_peca, name='detalhes_peca'),
    path('pecas/<int:peca_id>/editar/', views.editar_peca, name='editar_peca'),
    path('pecas/<int:peca_id>/excluir/', views.excluir_peca, name='excluir_peca'),
    
    # Categorias de peças
    path('categorias/', views.listar_categorias, name='listar_categorias'),
    path('categorias/adicionar/', views.adicionar_categoria, name='adicionar_categoria'),
    path('categorias/<int:categoria_id>/editar/', views.editar_categoria, name='editar_categoria'),
    path('categorias/<int:categoria_id>/excluir/', views.excluir_categoria, name='excluir_categoria'),


    # Importação/Exportação de peças
    path('pecas/importar/', views.importar_pecas, name='importar_pecas'),
    path('pecas/exportar/', views.exportar_pecas, name='exportar_pecas'),
    
    # ==============================
    # GESTÃO DE FORNECEDORES
    # ==============================
    # Listagens e visões gerais
    path('fornecedores/', views.listar_fornecedores, name='listar_fornecedores'),
    
    # CRUD de fornecedores
    path('fornecedores/adicionar/', views.adicionar_fornecedor, name='adicionar_fornecedor'),
    path('fornecedores/<int:fornecedor_id>/', views.detalhes_fornecedor, name='detalhes_fornecedor'),
    path('fornecedores/<int:fornecedor_id>/editar/', views.editar_fornecedor, name='editar_fornecedor'),
    path('fornecedores/<int:fornecedor_id>/excluir/', views.excluir_fornecedor, name='excluir_fornecedor'),
    
    # ==============================
    # ASSOCIAÇÕES PEÇAS-FORNECEDORES
    # ==============================
    path('associacoes/', views.associar_fornecedores_pecas, name='associar_fornecedores_pecas'),
    path('associacoes/adicionar-varios-fornecedores/', views.adicionar_varios_fornecedores_peca, name='adicionar_varios_fornecedores_peca'),
    path('associacoes/adicionar-varias-pecas/', views.adicionar_varias_pecas_fornecedor, name='adicionar_varias_pecas_fornecedor'),
    path('associacoes/<int:associacao_id>/excluir/', views.excluir_associacao_peca_fornecedor, name='excluir_associacao_fornecedor_peca'),
    
    # ==============================
    # GESTÃO DE ENCOMENDAS
    # ==============================
    # Listagens e visões gerais
    path('encomendas/', views.listar_encomendas, name='listar_encomendas'),
    
    # CRUD de encomendas
    path('encomendas/adicionar/', views.adicionar_encomenda, name='adicionar_encomenda'),
    path('encomendas/<int:encomenda_id>/', views.detalhes_encomenda, name='detalhes_encomenda'),
    path('encomendas/<int:encomenda_id>/editar/', views.editar_encomenda, name='editar_encomenda'),
    path('encomendas/<int:encomenda_id>/excluir/', views.excluir_encomenda, name='excluir_encomenda'),
    
    # Itens de encomenda
    path('encomendas/<int:encomenda_id>/adicionar-item/', views.adicionar_item_encomenda, name='adicionar_item_encomenda'),
    path('encomendas/itens/<int:item_id>/editar/', views.editar_item_encomenda, name='editar_item_encomenda'),
    path('encomendas/itens/<int:item_id>/excluir/', views.excluir_item_encomenda, name='excluir_item_encomenda'),
    
    # Ações de encomenda
    path('encomendas/<int:encomenda_id>/receber/', views.receber_encomenda, name='receber_encomenda'),
    path('encomendas/<int:encomenda_id>/cancelar/', views.cancelar_encomenda, name='cancelar_encomenda'),
    
    # ==============================
    # MOVIMENTAÇÕES DE STOCK
    # ==============================
    path('movimentacoes/', views.listar_movimentacoes, name='listar_movimentacoes'),
    path('movimentacoes/adicionar/', views.adicionar_movimentacao, name='adicionar_movimentacao'),
    path('movimentacoes/<int:movimentacao_id>/', views.detalhes_movimentacao, name='detalhes_movimentacao'),
    
    # ==============================
    # APIS PARA AJAX
    # ==============================
    # APIs para peças
    path('api/filtrar-pecas/', views.api_filtrar_pecas, name='api_filtrar_pecas'),
    path('api/historico-preco/<int:peca_id>/', views.api_historico_precos_peca, name='api_historico_precos_peca'),
    path('api/baixo-stock/', views.api_baixo_stock, name='api_baixo_stock'),
    path('api/pecas-modelo/<int:modelo_id>/', views.api_pecas_modelo, name='api_pecas_modelo'),
    
    # APIs para fornecedores
    path('api/filtrar-fornecedores/', views.api_filtrar_fornecedores, name='api_filtrar_fornecedores'),
    path('api/fornecedores/<int:fornecedor_id>/pecas/', views.api_listar_pecas_fornecedor, name='api_listar_pecas_fornecedor'),
    
    # APIs para encomendas
    path('api/encomendas/itens/<int:encomenda_id>/', views.api_listar_itens_encomenda, name='api_listar_itens_encomenda'),
    path('api/encomendas/precos-fornecedor/', views.api_precos_fornecedor, name='api_precos_fornecedor'),
    
    # APIs para estatísticas
    path('api/estatisticas/consumo-pecas/', views.api_estatisticas_consumo_pecas, name='api_estatisticas_consumo_pecas'),
    path('api/estatisticas/compras-fornecedores/', views.api_estatisticas_compras_fornecedores, name='api_estatisticas_compras_fornecedores'),
    
    # ==============================
    # IMPORTAÇÃO/EXPORTAÇÃO DE DADOS
    # ==============================
    path('importar-exportar/', views.importar_exportar, name='importar_exportar'),
    path('importar/fornecedores/', views.importar_fornecedores, name='importar_fornecedores'),
    path('importar/associacoes/', views.importar_associacoes, name='importar_associacoes'),
    
    path('exportar/fornecedores/', views.exportar_fornecedores, name='exportar_fornecedores'),
    path('exportar/pecas/', views.exportar_pecas, name='exportar_pecas'),
    path('exportar/associacoes/', views.exportar_associacoes, name='exportar_associacoes'),
]