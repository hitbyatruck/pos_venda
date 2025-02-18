from django.urls import path
from . import views

urlpatterns = [
    path('criar/', views.criar_pat, name='criar_pat'),
    path('listar/', views.listar_pats, name='listar_pats'),
    path('<int:pat_id>/', views.detalhes_pat, name='detalhes_pat'),
    path('editar/<int:pat_id>/', views.editar_pat, name='editar_pat'),
    path('excluir/<int:pat_id>/', views.excluir_pat, name='excluir_pat'),
    path('equipamentos-por-cliente/', views.equipamentos_por_cliente, name='equipamentos_por_cliente'),

]
