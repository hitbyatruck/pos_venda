from django.urls import path
from . import views

app_name = 'notas'

urlpatterns = [
    path('', views.listar_notas, name='listar_notas'),
    path('criar/', views.criar_nota, name='criar_nota'),
    path('<int:nota_id>/', views.detalhes_nota, name='detalhes_nota'),
    path('editar/<int:nota_id>/', views.editar_nota, name='editar_nota'),
    path('excluir/<int:nota_id>/', views.excluir_nota, name='excluir_nota'),
    path('tarefas-a-fazer/', views.listar_tarefas_a_fazer, name='listar_tarefas_a_fazer'),
    path('tarefa/criar/', views.criar_tarefa, name='criar_tarefa'),
    path('detalhes_tarefa/<int:tarefa_id>/', views.detalhes_tarefa, name='detalhes_tarefa'),
    path('editar_tarefa/<int:tarefa_id>/', views.editar_tarefa, name='editar_tarefa'),
    path('excluir_tarefa/<int:tarefa_id>/', views.excluir_tarefa, name='excluir_tarefa'),
    path('fechar_tarefa/<int:tarefa_id>/', views.fechar_tarefa, name='fechar_tarefa'),
    path('reabrir_tarefa/<int:tarefa_id>/', views.reabrir_tarefa, name='reabrir_tarefa'),
]
