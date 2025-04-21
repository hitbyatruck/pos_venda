from django.contrib import admin
from .models import ConfiguracaoSistema, SystemSettings, BackupLog, CustomField, CustomFieldValue

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

@admin.register(CustomField)
class CustomFieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'key', 'model', 'field_type', 'required', 'active')
    list_filter = ('model', 'field_type', 'required', 'active')
    search_fields = ('name', 'key', 'description')
    prepopulated_fields = {'key': ('name',)}
    list_per_page = 20

@admin.register(CustomFieldValue)
class CustomFieldValueAdmin(admin.ModelAdmin):
    list_display = ('custom_field', 'content_type', 'object_id', 'value')
    list_filter = ('custom_field',)
    search_fields = ('value',)
    list_per_page = 20

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('General', {
            'fields': ('system_name', 'timezone', 'email_from')
        }),
        ('Appearance', {
            'fields': ('site_logo', 'theme', 'custom_css')
        }),
        ('Notifications', {
            'fields': ('notify_on_new_pat', 'notify_on_pat_status_change', 'notify_on_new_client')
        }),
    )

    def has_add_permission(self, request):
        # Prevent adding multiple settings objects (singleton pattern)
        return not SystemSettings.objects.exists()

@admin.register(BackupLog)
class BackupLogAdmin(admin.ModelAdmin):
    list_display = ('filename', 'date_created', 'backup_type', 'created_by')
    list_filter = ('backup_type', 'date_created')
    search_fields = ('filename',)
    readonly_fields = ('date_created', 'created_by', 'file_size')
    list_per_page = 20