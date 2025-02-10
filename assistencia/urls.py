from django.urls import path
from . import views

urlpatterns = [
    path('lista/', views.lista_pats, name='lista_pats'),
    path('adicionar/', views.adicionar_pedido_assistencia, name='adicionar_pedido_assistencia'),
    path('<int:pedido_id>/', views.detalhes_pedido_assistencia, name='detalhes_pedido_assistencia'),
    path("editar/<int:pat_id>/", views.editar_pedido_assistencia, name="editar_pedido_assistencia"),
    path("excluir/<int:pat_id>/", views.excluir_pedido_assistencia, name="excluir_pedido_assistencia"),
    path("get_equipamentos/<int:cliente_id>/", views.get_equipamentos, name="get_equipamentos"),
    path('lista/', views.lista_pats, name='lista_pats'),
    
]