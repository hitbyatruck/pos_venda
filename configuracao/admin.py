from django.contrib import admin
from .models import ConfiguracaoSistema

@admin.register(ConfiguracaoSistema)
class ConfiguracaoSistemaAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Informações da Empresa', {
            'fields': ('nome_empresa', 'logo')
        }),
        ('Aparência', {
            'fields': ('cor_primaria', 'cor_secundaria', 'tema')
        }),
        ('Configurações de Clientes', {
            'fields': ('clientes_por_pagina', 'permitir_cadastro_duplicado')
        }),
    )
    
    # Impedir a adição de novas configurações (manter como singleton)
    def has_add_permission(self, request):
        return ConfiguracaoSistema.objects.count() == 0