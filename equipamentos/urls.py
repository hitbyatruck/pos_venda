from django.urls import path
from . import views

app_name = 'equipamentos'

urlpatterns = [
    # Main paths
    path('', views.index, name='index'),
    
    # Standard equipment routes
    path('listar/', views.listar_equipamentos, name='listar_equipamentos'),
    
    # Manufactured equipment (EquipamentoFabricado)
    path('fabricados/lista/', views.listar_equipamentos_fabricados, name='listar_fabricados'),
    path('fabricados/adicionar/', views.adicionar_equipamento_fabricado, name='adicionar_fabricado'),
    path('fabricados/<int:equipamento_id>/', views.detalhes_equipamento_fabricado, name='detalhes_fabricado'),
    path('fabricados/<int:equipamento_id>/editar/', views.editar_equipamento_fabricado, name='editar_fabricado'),
    path('fabricados/<int:equipamento_id>/excluir/', views.excluir_equipamento_fabricado, name='excluir_fabricado'),
    
    # Client equipment (EquipamentoCliente)
    path('cliente/lista/', views.listar_equipamentos_cliente, name='listar_cliente'),
    path('cliente/adicionar/', views.adicionar_equipamento_cliente, name='adicionar_cliente'),
    path('cliente/<int:equipamento_id>/', views.detalhes_equipamento_cliente, name='detalhes_cliente'),
    path('cliente/<int:equipamento_id>/editar/', views.editar_equipamento_cliente, name='editar_cliente'),
    path('cliente/<int:equipamento_id>/excluir/', views.excluir_equipamento_cliente, name='excluir_cliente'),
    
    # Categories
    path('categorias/', views.listar_categorias, name='listar_categorias'),
    path('categorias/adicionar/', views.adicionar_categoria, name='adicionar_categoria'),
    path('categorias/<int:categoria_id>/', views.detalhes_categoria, name='detalhes_categoria'),
    path('categorias/<int:categoria_id>/editar/', views.editar_categoria, name='editar_categoria'),
    path('categorias/<int:categoria_id>/excluir/', views.excluir_categoria, name='excluir_categoria'),
]