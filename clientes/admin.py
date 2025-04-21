from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Cliente, Contacto, TipoContacto, Setor, CategoriaCliente
from simple_history.admin import SimpleHistoryAdmin

class ContactoInline(admin.TabularInline):
    model = Contacto
    extra = 1

@admin.register(Cliente)
class ClienteAdmin(SimpleHistoryAdmin):
    list_display = ('nome', 'nif', 'cidade', 'pais')
    list_filter = ('ativo', 'setor')
    search_fields = ('nome', 'nif', 'cidade', 'morada')
    inlines = [ContactoInline]

    fieldsets = (
        (_('Informações básicas'), {
            'fields': ('nome', 'nif', 'setor', 'imagem')
        }),
        (_('Endereço'), {
            'fields': ('morada', 'codigo_postal', 'cidade', 'pais')
        }),
        (_('Informações adicionais'), {
            'fields': ('website', 'observacoes', 'ativo')
        }),
    )

@admin.register(Contacto)
class ContactoAdmin(admin.ModelAdmin):
    list_display = ('nome_contacto', 'cargo', 'cliente', 'tipo', 'valor', 'principal')
    list_filter = ('tipo', 'principal')
    search_fields = ('nome_contacto', 'valor', 'cliente__nome')

@admin.register(TipoContacto)
class TipoContactoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo')
    list_filter = ('ativo',)
    search_fields = ('nome',)

@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome', 'descricao')

@admin.register(CategoriaCliente)
class CategoriaClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome', 'descricao')