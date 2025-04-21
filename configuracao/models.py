from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
import pytz
import json
import os

class ConfiguracaoSistema(models.Model):
    nome_empresa = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='config/logos/', null=True, blank=True)
    cor_primaria = models.CharField(max_length=7, default='#4e73df', help_text='Código de cor hexadecimal')
    cor_secundaria = models.CharField(max_length=7, default='#1cc88a', help_text='Código de cor hexadecimal')
    tema = models.CharField(max_length=20, default='default', choices=[
        ('default', 'Padrão'),
        ('dark', 'Escuro'),
        ('light', 'Claro'),
    ])

    # Configurações específicas do módulo de clientes
    clientes_por_pagina = models.PositiveIntegerField(default=25)
    permitir_cadastro_duplicado = models.BooleanField(default=False)

    # Método para garantir que exista apenas uma instância (singleton)
    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"Configurações do Sistema: {self.nome_empresa}"

    class Meta:
        verbose_name = 'Configuração do Sistema'
        verbose_name_plural = 'Configurações do Sistema'


class SystemSettings(models.Model):
    """
    Singleton model to store system-wide settings.
    """
    # Timezone settings
    timezone = models.CharField(
        max_length=50,
        default='Europe/Lisbon',
        choices=[(tz, tz) for tz in pytz.common_timezones],
        verbose_name=_('Fuso Horário')
    )

    # General settings
    site_name = models.CharField(max_length=100, default="Sistema de Pós-Venda", verbose_name=_('Nome do Sistema'))
    site_logo = models.ImageField(upload_to='logos/', null=True, blank=True, verbose_name=_('Logo do Sistema'))
    default_language = models.CharField(
        max_length=10,
        default='pt',
        choices=settings.LANGUAGES,
        verbose_name=_('Idioma Padrão')
    )

    # Email settings
    email_from = models.EmailField(verbose_name=_('Email Para Envio'), default='no-reply@example.com')
    email_signature = models.TextField(verbose_name=_('Assinatura de Email'), blank=True)

    # Notification settings
    notify_on_new_pat = models.BooleanField(default=True, verbose_name=_('Notificar Nova PAT'))
    notify_on_pat_status_change = models.BooleanField(default=True, verbose_name=_('Notificar Mudança de Status da PAT'))
    notify_on_new_client = models.BooleanField(default=False, verbose_name=_('Notificar Novo Cliente'))

    # System settings
    maintenance_mode = models.BooleanField(default=False, verbose_name=_('Modo de Manutenção'))
    maintenance_message = models.TextField(blank=True, verbose_name=_('Mensagem de Manutenção'))
    last_backup = models.DateTimeField(null=True, blank=True, verbose_name=_('Último Backup'))

    # Appearance settings
    theme = models.CharField(
        max_length=20,
        choices=[
            ('light', _('Tema Claro')),
            ('dark', _('Tema Escuro')),
            ('auto', _('Automático (baseado no navegador)'))
        ],
        default='auto',
        verbose_name=_('Tema')
    )

    # Analytics (optional)
    analytics_id = models.CharField(max_length=50, blank=True, verbose_name=_('ID do Google Analytics'))

    # Customization options
    custom_css = models.TextField(blank=True, verbose_name=_('CSS Personalizado'))

    # Cache settings
    cache_timeout = models.PositiveIntegerField(default=3600, verbose_name=_('Tempo de Cache (segundos)'))

    # Date and time formats
    date_format = models.CharField(
        max_length=20,
        default='d/m/Y',
        verbose_name=_('Formato de Data')
    )

    time_format = models.CharField(
        max_length=20,
        default='H:i',
        verbose_name=_('Formato de Hora')
    )

    class Meta:
        verbose_name = _('Configuração do Sistema')
        verbose_name_plural = _('Configurações do Sistema')

    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton)"""
        self.pk = 1
        super().save(*args, **kwargs)

        # Update cache
        cache.set('system_settings', self)

        # Update timezone in settings
        os.environ['TZ'] = self.timezone

    def delete(self, *args, **kwargs):
        """Prevent deletion of the singleton"""
        pass

    @classmethod
    def get_settings(cls):
        """Get the settings instance - creating it if it doesn't exist"""
        settings = cache.get('system_settings')

        if not settings:
            try:
                settings, created = cls.objects.get_or_create(pk=1)
                cache.set('system_settings', settings)
            except Exception as e:
                # Handle case where table doesn't exist yet (e.g., during initial migration)
                import logging
                logging.getLogger('django').warning(f"Error getting SystemSettings: {e}")
                # Return a default instance without saving to DB
                settings = cls()

        return settings


class BackupLog(models.Model):
    """Log of system backups"""
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_('Data de Criação'))
    filename = models.CharField(max_length=255, verbose_name=_('Nome do Arquivo'))
    file_size = models.BigIntegerField(default=0, verbose_name=_('Tamanho do Arquivo'))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Criado Por')
    )
    is_auto = models.BooleanField(default=False, verbose_name=_('Backup Automático'))
    backup_type = models.CharField(
        max_length=20,
        choices=[
            ('full', _('Completo')),
            ('db', _('Apenas Banco de Dados')),
            ('files', _('Apenas Arquivos')),
        ],
        default='full',
        verbose_name=_('Tipo de Backup')
    )

    class Meta:
        verbose_name = _('Log de Backup')
        verbose_name_plural = _('Logs de Backup')
        ordering = ['-date_created']


class CustomField(models.Model):
    """Custom fields for various models in the system"""
    name = models.CharField(max_length=100, verbose_name=_('Nome'))
    key = models.SlugField(max_length=100, verbose_name=_('Chave'))
    description = models.TextField(blank=True, verbose_name=_('Descrição'))

    FIELD_TYPES = [
        ('text', _('Texto')),
        ('number', _('Número')),
        ('boolean', _('Sim/Não')),
        ('date', _('Data')),
        ('select', _('Seleção')),
        ('multi_select', _('Múltipla Escolha')),
    ]

    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, verbose_name=_('Tipo de Campo'))

    # For select/multi_select types, store options as JSON
    options = models.TextField(blank=True, help_text=_('Opções para seleção (JSON)'), verbose_name=_('Opções'))

    # Which model this field applies to
    MODEL_CHOICES = [
        ('cliente', _('Cliente')),
        ('equipamento', _('Equipamento')),
        ('pat', _('PAT')),
        ('nota', _('Nota')),
        ('peca', _('Peça')),
    ]

    model = models.CharField(max_length=20, choices=MODEL_CHOICES, verbose_name=_('Modelo'))

    # If this field is required
    required = models.BooleanField(default=False, verbose_name=_('Obrigatório'))

    # If this field is active
    active = models.BooleanField(default=True, verbose_name=_('Ativo'))

    # Order for display
    order = models.PositiveSmallIntegerField(default=0, verbose_name=_('Ordem'))

    class Meta:
        verbose_name = _('Campo Personalizado')
        verbose_name_plural = _('Campos Personalizados')
        ordering = ['model', 'order']
        unique_together = [('key', 'model')]

    def __str__(self):
        return f"{self.name} ({self.get_model_display()})"

    def get_options_list(self):
        """Return options as a Python list"""
        if not self.options:
            return []
        try:
            return json.loads(self.options)
        except json.JSONDecodeError:
            return []


class CustomFieldValue(models.Model):
    """Values for custom fields"""
    custom_field = models.ForeignKey(
        CustomField,
        on_delete=models.CASCADE,
        related_name='values',
        verbose_name=_('Campo Personalizado')
    )

    # Store content type and object ID to create generic relationship
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE,
        verbose_name=_('Tipo de Conteúdo')
    )
    object_id = models.PositiveIntegerField(verbose_name=_('ID do Objeto'))

    # Store the actual value as text - will be converted based on field_type
    value = models.TextField(blank=True, null=True, verbose_name=_('Valor'))

    class Meta:
        verbose_name = _('Valor de Campo Personalizado')
        verbose_name_plural = _('Valores de Campos Personalizados')
        unique_together = [('custom_field', 'content_type', 'object_id')]