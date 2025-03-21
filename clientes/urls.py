from django.urls import path
from .views import adicionar_cliente, listar_clientes, editar_cliente, excluir_cliente, detalhes_cliente, adicionar_equipamento_cliente
from . import views


app_name = 'clientes'

urlpatterns = [
    path('adicionar/', adicionar_cliente, name='adicionar_cliente'),
    path('lista/', listar_clientes, name='listar_clientes'),
    path('detalhes/<int:cliente_id>/', views.detalhes_cliente, name='detalhes_cliente'),
    path('editar/<int:cliente_id>/', editar_cliente, name='editar_cliente'),
    path('excluir/<int:cliente_id>/', views.excluir_cliente, name='excluir_cliente'),
    path('desassociar_equipamento/<int:equipamento_cliente_id>/', views.desassociar_equipamento, name='desassociar_equipamento'),
    path('cliente/adicionar_equipamento/<int:cliente_id>/', views.adicionar_equipamento_cliente, name='adicionar_equipamento_cliente'),
    path('equipamentos-por-cliente/', views.equipamentos_por_cliente, name='equipamentos_por_cliente'),
    
]
