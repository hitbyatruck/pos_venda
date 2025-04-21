from django.urls import path
from . import views

app_name = 'assistencia'

urlpatterns = [
    path('', views.listar_pats, name='listar_pats'),
    path('criar/', views.criar_pat, name='criar_pat'),
    path('<int:pat_id>/', views.detalhes_pat, name='detalhes_pat'),
    path('<int:pat_id>/editar/', views.editar_pat, name='editar_pat'),
    path('<int:pat_id>/excluir/', views.excluir_pat, name='excluir_pat'),
    path('equipamentos-por-cliente/', views.equipamentos_por_cliente, name='equipamentos_por_cliente'),
    path('item/<int:item_id>/excluir/', views.excluir_item_pat, name='excluir_item_pat'),
    path('mudar-status/<int:pat_id>/', views.mudar_status_pat, name='mudar_status_pat'),
    path('<int:pat_id>/historico/', views.historico_pat, name='historico_pat'),
]