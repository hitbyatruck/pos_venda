from django.contrib import admin
from .models import (
    Cliente, Empresa, Individual, Setor, 
    Contacto, TipoContacto, EquipamentoCliente,
    InteracaoCliente, TarefaCliente
)

@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ativo', 'data_criacao']
    list_filter = ['ativo']
    search_fields = ['nome', 'descricao']
    fieldsets = [
        (None, {'fields': ['nome', 'descricao']}),
        ('Estado', {'fields': ['ativo']}),
    ]

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'email', 'telefone', 'tipo', 'ativo', 'data_criacao']
    list_filter = ['tipo', 'ativo', 'data_criacao']
    search_fields = ['nome', 'email', 'telefone', 'nif']
    fieldsets = [
        (None, {'fields': ['tipo', 'nome', 'email', 'telefone', 'endereco']}),
        ('Informações Adicionais', {
            'fields': ['website', 'nif', 'morada', 'codigo_postal', 'cidade', 'pais', 'observacoes'],
            'classes': ['collapse']
        }),
        ('Estado', {'fields': ['ativo']}),
    ]

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'email', 'telefone', 'setor', 'ativo']
    list_filter = ['setor', 'ativo', 'data_criacao']
    search_fields = ['nome', 'email', 'telefone', 'nif']
    fieldsets = [
        (None, {'fields': ['nome', 'email', 'telefone', 'endereco']}),
        ('Informações Adicionais', {
            'fields': ['website', 'nif', 'morada', 'codigo_postal', 'cidade', 'pais', 'setor', 'nome_comercial', 'observacoes'],
            'classes': ['collapse']
        }),
        ('Estado', {'fields': ['ativo']}),
    ]

@admin.register(Individual)
class IndividualAdmin(admin.ModelAdmin):
    list_display = ['nome', 'email', 'telefone', 'empresa_associada', 'cargo', 'ativo']
    list_filter = ['ativo', 'data_criacao', 'empresa_associada']
    search_fields = ['nome', 'email', 'telefone', 'nif']
    fieldsets = [
        (None, {'fields': ['nome', 'email', 'telefone', 'endereco']}),
        ('Informações Adicionais', {
            'fields': ['website', 'nif', 'morada', 'codigo_postal', 'cidade', 'pais', 'empresa_associada', 'cargo', 'observacoes'],
            'classes': ['collapse']
        }),
        ('Estado', {'fields': ['ativo']}),
    ]

@admin.register(TipoContacto)
class TipoContactoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'icone', 'ativo']
    list_filter = ['ativo']
    search_fields = ['nome']

@admin.register(Contacto)
class ContactoAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'tipo', 'valor', 'nome_contacto', 'principal']
    list_filter = ['tipo', 'principal']
    search_fields = ['valor', 'nome_contacto', 'cargo']

@admin.register(EquipamentoCliente)
class EquipamentoClienteAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'equipamento_fabricado', 'numero_serie', 'data_aquisicao', 'data_instalacao']
    list_filter = ['data_aquisicao', 'data_instalacao']
    search_fields = ['numero_serie', 'cliente__nome', 'equipamento_fabricado__modelo']
    date_hierarchy = 'data_aquisicao'

@admin.register(InteracaoCliente)
class InteracaoClienteAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'tipo', 'assunto', 'data', 'responsavel']
    list_filter = ['tipo', 'data', 'responsavel']
    search_fields = ['cliente__nome', 'assunto', 'descricao']
    date_hierarchy = 'data'

@admin.register(TarefaCliente)
class TarefaClienteAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'titulo', 'prioridade', 'data_limite', 'concluida', 'responsavel']
    list_filter = ['prioridade', 'concluida', 'data_limite', 'responsavel']
    search_fields = ['cliente__nome', 'titulo', 'descricao']
    date_hierarchy = 'data_limite'