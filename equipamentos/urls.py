from django.urls import path
from . import views


app_name = 'equipamentos'

urlpatterns = [
    path('adicionar/', views.adicionar_equipamento_fabricado, name='adicionar_equipamento_fabricado'),
    path('lista/', views.listar_equipamentos_fabricados, name='listar_equipamentos_fabricados'),
    path('editar/<int:equipamento_id>/', views.editar_equipamento_fabricado, name='editar_equipamento_fabricado'),
    path('excluir/<int:equipamento_id>/', views.excluir_equipamento_fabricado, name='excluir_equipamento_fabricado'),
    path('upload_documento/<int:equipamento_id>/', views.upload_documento_equipamento, name='upload_documento_equipamento'),
    path('excluir_documento/<int:documento_id>/', views.excluir_documento, name='excluir_documento'),
    path('cliente/lista/', views.listar_equipamentos_cliente, name='lista_equipamentos_cliente'),
    path('<int:equipamento_id>/', views.detalhes_equipamento, name='detalhes_equipamento'),
    path('categorias/', views.listar_categorias, name='listar_categorias'),
    path('categorias/adicionar/', views.adicionar_categoria, name='adicionar_categoria'),
]
