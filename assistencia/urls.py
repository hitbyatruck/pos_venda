from django.urls import path
from . import views

app_name = 'assistencia'

urlpatterns = [
    # List views
    path('', views.listar_pats, name='listar_pats'),

    # CRUD operations
    path('criar/', views.criar_pat, name='criar_pat'),
    path('<int:pat_id>/', views.detalhes_pat, name='detalhes_pat'),
    path('<int:pat_id>/editar/', views.editar_pat, name='editar_pat'),
    path('<int:pat_id>/excluir/', views.excluir_pat, name='excluir_pat'),
    
    # API endpoints
    path('api/equipamentos/por-cliente/', views.equipamentos_por_cliente, name='equipamentos_por_cliente'),
    path('api/item/<int:item_id>/excluir/', views.excluir_item_pat, name='excluir_item_pat'),
]