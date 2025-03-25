from django.urls import path
from . import views

app_name = 'clientes'


urlpatterns = [
    path('adicionar/', views.adicionar_cliente, name='adicionar_cliente'),
    path('lista/', views.listar_clientes, name='listar_clientes'),
    path('editar/<int:cliente_id>/', views.editar_cliente, name='editar_cliente'),
    path('excluir/<int:cliente_id>/', views.excluir_cliente, name='excluir_cliente'),
    path('detalhes/<int:cliente_id>/', views.detalhes_cliente, name='detalhes_cliente'),
    path('adicionar_equipamento/<int:cliente_id>/', views.adicionar_equipamento_cliente, name='adicionar_equipamento_cliente'),
    path('desassociar_equipamento/<int:equipamento_id>/', views.desassociar_equipamento_cliente, name='desassociar_equipamento_cliente'),
]