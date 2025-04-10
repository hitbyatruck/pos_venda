from django.urls import path
from . import views

app_name = 'equipamentos'

urlpatterns = [
    # Main paths
    path('', views.index, name='index'),
    
    # All equipments (combined view)
    path('listar/', views.listar_equipamentos, name='listar_equipamentos'),
    
    # Equipamentos Fabricados (Models)
    path('fabricados/', views.listar_equipamentos_fabricados, name='listar_fabricados'),  # This is the correct name
    path('fabricados/adicionar/', views.adicionar_equipamento_fabricado, name='adicionar_fabricado'),
    path('fabricados/<int:equipamento_id>/', views.detalhes_equipamento_fabricado, name='detalhes_fabricado'),
    path('fabricados/<int:equipamento_id>/editar/', views.editar_equipamento_fabricado, name='editar_fabricado'),
    path('fabricados/<int:equipamento_id>/excluir/', views.excluir_equipamento_fabricado, name='excluir_fabricado'),
    path('fabricados/exportar/', views.exportar_equipamentos_fabricados, name='exportar_fabricados'),
    
    # Equipamentos do Cliente (Instances)
    path('cliente/', views.listar_equipamentos_cliente, name='listar_cliente'),
    path('cliente/adicionar/', views.adicionar_equipamento_cliente, name='adicionar_cliente'),
    path('cliente/<int:equipamento_id>/', views.detalhes_equipamento_cliente, name='detalhes_cliente'),
    path('cliente/<int:equipamento_id>/editar/', views.editar_equipamento_cliente, name='editar_cliente'),
    path('cliente/<int:equipamento_id>/excluir/', views.excluir_equipamento_cliente, name='excluir_cliente'),
    path('cliente/historico/<int:equipamento_id>/', views.historico_equipamento_cliente, name='historico_equipamento_cliente'),
    
    # Categorias
    path('categorias/', views.listar_categorias, name='listar_categorias'),
    path('categorias/adicionar/', views.adicionar_categoria, name='adicionar_categoria'),
    path('categorias/<int:categoria_id>/', views.detalhes_categoria, name='detalhes_categoria'),
    path('categorias/<int:categoria_id>/editar/', views.editar_categoria, name='editar_categoria'),
    path('categorias/<int:categoria_id>/excluir/', views.excluir_categoria, name='excluir_categoria'),
    
    # Documentos
    path('documentos/upload/<int:equipamento_id>/', views.upload_documento_equipamento, name='upload_documento'),
    path('documentos/excluir/<int:documento_id>/', views.excluir_documento, name='excluir_documento'),
    
    # Transferência
    path('cliente/<int:equipamento_id>/transferir/', views.transferir_equipamento, name='transferir_equipamento'),
    
    # Ajax e API
    path('api/cliente/<int:cliente_id>/', views.api_equipamentos_cliente, name='api_equipamentos_cliente'),
]