from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Cliente (genérico)
    path('listar/', views.listar_clientes, name='listar_clientes'),
    path('adicionar/', views.adicionar_cliente, name='adicionar_cliente'),
    path('detalhes/<int:cliente_id>/', views.detalhes_cliente, name='detalhes_cliente'),
    path('editar/<int:cliente_id>/', views.editar_cliente, name='editar_cliente'),
    path('excluir/<int:cliente_id>/', views.excluir_cliente, name='excluir_cliente'),
    path('exportar/', views.exportar_clientes, name='exportar_clientes'),
    path('importar/', views.importar_clientes, name='importar_clientes'),
    
    # Cliente específico (empresa/individual)
    path('adicionar/empresa/', views.adicionar_empresa, name='adicionar_empresa'),
    path('adicionar/individual/', views.adicionar_individual, name='adicionar_individual'),
    
    # Empresas
    path('empresas/', views.listar_empresas, name='listar_empresas'),
    path('empresas/<int:empresa_id>/', views.detalhes_empresa, name='detalhes_empresa'),
    path('empresas/<int:empresa_id>/editar/', views.editar_empresa, name='editar_empresa'),
    path('empresas/<int:empresa_id>/excluir/', views.excluir_empresa, name='excluir_empresa'),
    path('empresas/listar/', views.listar_empresas, name='listar_empresas'),
    
    # Individuais
    path('individuais/listar/', views.listar_individuais, name='listar_individuais'),
    
    # Setores
    path('configuracoes/setores/', views.listar_setores, name='listar_setores'),
    path('configuracoes/setores/adicionar/', views.adicionar_setor, name='adicionar_setor'),
    path('configuracoes/setores/<int:setor_id>/', views.detalhes_setor, name='detalhes_setor'),
    path('configuracoes/setores/<int:setor_id>/editar/', views.editar_setor, name='editar_setor'),
    path('configuracoes/setores/<int:setor_id>/excluir/', views.excluir_setor, name='excluir_setor'),
    
    # Tipos de Contacto
    path('configuracoes/tipos-contacto/', views.listar_tipos_contacto, name='listar_tipos_contacto'),
    path('configuracoes/tipos-contacto/adicionar/', views.adicionar_tipo_contacto, name='adicionar_tipo_contacto'),
    path('configuracoes/tipos-contacto/<int:tipo_id>/', views.detalhes_tipo_contacto, name='detalhes_tipo_contacto'),
    path('configuracoes/tipos-contacto/<int:tipo_id>/editar/', views.editar_tipo_contacto, name='editar_tipo_contacto'),
    path('configuracoes/tipos-contacto/<int:tipo_id>/excluir/', views.excluir_tipo_contacto, name='excluir_tipo_contacto'),
    
    # Detalhes de cliente (abas)
    path('detalhes/<int:cliente_id>/contactos/', views.cliente_contactos, name='cliente_contactos'),
    path('detalhes/<int:cliente_id>/equipamentos/', views.cliente_equipamentos, name='cliente_equipamentos'),
    path('detalhes/<int:cliente_id>/assistencias/', views.cliente_assistencias, name='cliente_assistencias'),
    path('detalhes/<int:cliente_id>/notas/', views.cliente_notas, name='cliente_notas'),
    
    # Equipamentos
    path('adicionar_equipamento/<int:cliente_id>/', views.adicionar_equipamento_cliente, name='adicionar_equipamento_cliente'),
    path('desassociar_equipamento/<int:equipamento_cliente_id>/', views.desassociar_equipamento, name='desassociar_equipamento'),
    path('equipamentos_por_cliente/', views.equipamentos_por_cliente, name='equipamentos_por_cliente'),

    # Contactos
    path('contactos/excluir/', views.excluir_contacto, name='excluir_contacto'),

    # Busca unificada
    path('busca/', views.busca_unificada, name='busca_unificada'),

    # Index
    path('', views.index, name='index'),
]