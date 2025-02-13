from django.urls import path
from . import views
from .views import (
    
    adicionar_equipamento_fabricado,
    listar_equipamentos_fabricados, 
    editar_equipamento_fabricado,
    excluir_equipamento_fabricado,
 
    listar_equipamentos_cliente,
        
    detalhes_equipamento, 
    excluir_documento,

    listar_categorias, 
    adicionar_categoria,
)

urlpatterns = [
    path("fabricados/adicionar/", adicionar_equipamento_fabricado, name="adicionar_equipamento_fabricado"),
    path('fabricados/lista/', views.listar_equipamentos_fabricados, name='lista_equipamentos_fabricados'),
    path('fabricados/editar/<int:equipamento_id>/', editar_equipamento_fabricado, name='editar_equipamento_fabricado'),
    path('fabricados/excluir/<int:equipamento_id>/', excluir_equipamento_fabricado, name='excluir_equipamento_fabricado'),


    
    path('cliente/lista/', listar_equipamentos_cliente, name='lista_equipamentos_cliente'),
    path('<int:equipamento_id>/', detalhes_equipamento, name='detalhes_equipamento'),
    path('documentos/excluir/<int:documento_id>/', views.excluir_documento, name='excluir_documento'),

    path('categorias/', listar_categorias, name='listar_categorias'),
    path('categorias/adicionar/', adicionar_categoria, name='adicionar_categoria'),
    

]
