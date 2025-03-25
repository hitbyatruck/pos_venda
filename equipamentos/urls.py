from django.urls import path
from . import views

app_name = 'equipamentos'

urlpatterns = [
    # Manter como está
    path('fabricados/adicionar/', views.adicionar_equipamento_fabricado, name='adicionar_equipamento_fabricado'),
    path('fabricados/lista/', views.listar_equipamentos_fabricados, name='listar_equipamentos_fabricados'),
    
    # Atualizar a URL para cliente/listar em vez de cliente/lista
    path('cliente/listar/', views.listar_equipamentos_cliente, name='listar_equipamentos_cliente'),
    
    # Resto das URLs permanecem iguais
    path('fabricados/editar/<int:equipamento_id>/', views.editar_equipamento_fabricado, name='editar_equipamento_fabricado'),
    path('fabricados/excluir/<int:pk>/', views.excluir_equipamento_fabricado, name='excluir_equipamento_fabricado'),
    path('fabricados/upload_documento/<int:equipamento_id>/', views.upload_documento_equipamento, name='upload_documento_equipamento'),
    path('fabricados/excluir_documento/<int:documento_id>/', views.excluir_documento, name='excluir_documento'),
    path('<int:equipamento_id>/', views.detalhes_equipamento, name='detalhes_equipamento'),
    path('categorias/', views.listar_categorias, name='listar_categorias'),
    path('categorias/adicionar/', views.adicionar_categoria, name='adicionar_categoria'),
]