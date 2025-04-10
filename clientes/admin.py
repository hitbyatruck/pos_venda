from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Cliente, Contacto, TipoContacto, Setor, CategoriaCliente

@admin.register(Cliente)
class ClienteAdmin(SimpleHistoryAdmin):
    list_display = ['nome', 'email_principal', 'cidade', 'ativo']
    list_filter = ['setor', 'cidade', 'pais', 'ativo']
    search_fields = ['nome', 'email_principal', 'nif', 'morada', 'cidade']
    readonly_fields = ['data_criacao', 'data_atualizacao']
    fieldsets = [
        ('Informações Básicas', {
            'fields': ('nome', 'email_principal', 'website', 'setor', 'imagem')
        }),
        ('Vinculação à Empresa', {
            'fields': ('empresa_associada', 'cargo'),
            'classes': ('collapse',),
        }),
        ('Informações Fiscais', {
            'fields': ('nif', 'percentagem_iva', 'desconto'),
            'classes': ('collapse',),
        }),
        ('Endereço', {
            'fields': ('morada', 'codigo_postal', 'cidade', 'pais'),
        }),
        ('Endereço de Entrega', {
            'fields': ('usar_mesma_morada', 'morada_entrega', 'codigo_postal_entrega', 'cidade_entrega', 'pais_entrega'),
            'classes': ('collapse',),
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',),
        }),
        ('Metadados', {
            'fields': ('ativo', 'data_criacao', 'data_atualizacao'),
            'classes': ('collapse',),
        }),
    ]

    # Define actions
    actions = ['deactivate_clients', 'activate_clients']
    
    # Action to deactivate selected clients
    def deactivate_clients(self, request, queryset):
        updated = queryset.update(ativo=False)
        self.message_user(request, f"{updated} clientes desativados com sucesso.")
    deactivate_clients.short_description = "Desativar clientes selecionados"
    
    # Action to activate selected clients
    def activate_clients(self, request, queryset):
        updated = queryset.update(ativo=True)
        self.message_user(request, f"{updated} clientes ativados com sucesso.")
    activate_clients.short_description = "Ativar clientes selecionados"

@admin.register(Contacto)
class ContactoAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'tipo', 'valor', 'principal']
    list_filter = ['tipo', 'principal']
    search_fields = ['valor', 'nome_contacto', 'cliente__nome']

@admin.register(TipoContacto)
class TipoContactoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ativo']
    list_filter = ['ativo']
    search_fields = ['nome']

@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ativo']
    list_filter = ['ativo']
    search_fields = ['nome', 'descricao']

@admin.register(CategoriaCliente)
class CategoriaClienteAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome', 'descricao')