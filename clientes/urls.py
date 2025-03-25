from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    # URLs existentes
    path('listar/', views.listar_clientes, name='listar_clientes'),
    path('adicionar/', views.adicionar_cliente, name='adicionar_cliente'),
    path('detalhes/<int:cliente_id>/', views.detalhes_cliente, name='detalhes_cliente'),
    path('editar/<int:cliente_id>/', views.editar_cliente, name='editar_cliente'),
    path('excluir/<int:cliente_id>/', views.excluir_cliente, name='excluir_cliente'),
    
    # Nova URL para a visualização de contactos
    path('detalhes/<int:cliente_id>/contactos/', views.cliente_contactos, name='cliente_contactos'),
    
    # Outras URLs existentes
    path('adicionar_equipamento/<int:cliente_id>/', views.adicionar_equipamento_cliente, name='adicionar_equipamento_cliente'),
    path('desassociar_equipamento/<int:equipamento_cliente_id>/', views.desassociar_equipamento, name='desassociar_equipamento'),
    path('desassociar_equipamento_cliente/<int:equipamento_id>/', views.desassociar_equipamento_cliente, name='desassociar_equipamento_cliente'),
    path('equipamentos_por_cliente/', views.equipamentos_por_cliente, name='equipamentos_por_cliente'),

    path('detalhes/<int:cliente_id>/equipamentos/', views.cliente_equipamentos, name='cliente_equipamentos'),
path('detalhes/<int:cliente_id>/assistencias/', views.cliente_assistencias, name='cliente_assistencias'),
path('detalhes/<int:cliente_id>/notas/', views.cliente_notas, name='cliente_notas'),
]