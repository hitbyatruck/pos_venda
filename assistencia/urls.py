from django.urls import path
from . import views

app_name = 'assistencia'

urlpatterns = [
    # List and Create views
    path('', views.listar_pats, name='listar_pats'),
    path('criar/', views.criar_pat, name='criar_pat'),
    
    # Detail, Edit and Delete views
    path('<int:pat_id>/', views.detalhes_pat, name='detalhes_pat'),
    path('<int:pat_id>/editar/', views.editar_pat, name='editar_pat'),
    path('<int:pat_id>/excluir/', views.excluir_pat, name='excluir_pat'),
    
    # API endpoints for AJAX operations
    path('api/equipamentos/', views.equipamentos_por_cliente, name='equipamentos_por_cliente'),
]