from django.urls import path
from .views import adicionar_cliente, listar_clientes, editar_cliente, excluir_cliente, detalhes_cliente

urlpatterns = [
    path('adicionar/', adicionar_cliente, name='adicionar_cliente'),
    path('lista/', listar_clientes, name='lista_clientes'),
    path('detalhes/<int:cliente_id>/', detalhes_cliente, name='detalhes_cliente'),
    path('editar/<int:cliente_id>/', editar_cliente, name='editar_cliente'),
    path('excluir/<int:cliente_id>/', excluir_cliente, name='excluir_cliente'),
    
]
