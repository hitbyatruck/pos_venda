from django import forms
from django.utils.translation import gettext_lazy as _
import pytz
import json

from .models import SystemSettings, CustomField

class SystemSettingsForm(forms.ModelForm):
    """Form for system settings"""
    class Meta:
        model = SystemSettings
        fields = [
            'site_name', 'site_logo', 'default_language', 'timezone',
            'date_format', 'time_format', 'cache_timeout'
        ]

    def clean_timezone(self):
        timezone = self.cleaned_data.get('timezone')
        if timezone not in pytz.all_timezones:
            raise forms.ValidationError(_('Fuso horário inválido'))
        return timezone


class BackupForm(forms.Form):
    """Form for creating backups"""
    backup_type = forms.ChoiceField(
        label=_('Tipo de Backup'),
        choices=[
            ('full', _('Completo')),
            ('db', _('Apenas Banco de Dados')),
            ('files', _('Apenas Arquivos')),
        ],
        initial='full',
        widget=forms.RadioSelect
    )


class CustomFieldForm(forms.ModelForm):
    """Form for custom fields"""
    options = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 4}),
        help_text=_('Uma opção por linha para campos de seleção')
    )

    class Meta:
        model = CustomField
        fields = [
            'name', 'key', 'description', 'field_type',
            'options', 'model', 'required', 'active', 'order'
        ]

    def clean_options(self):
        """Convert options from textarea (one per line) to JSON list"""
        options = self.cleaned_data.get('options')
        field_type = self.cleaned_data.get('field_type')

        if field_type in ['select', 'multi_select']:
            if not options.strip():
                raise forms.ValidationError(_('Campos de seleção precisam ter pelo menos uma opção'))

            # Convert from one-per-line to JSON array
            option_list = [opt.strip() for opt in options.split('\n') if opt.strip()]
            return json.dumps(option_list)

        return ''

    def clean_key(self):
        """Ensure key is valid and unique for the model"""
        key = self.cleaned_data.get('key')
        model = self.cleaned_data.get('model')

        if not key.isalnum() and not '_' in key:
            raise forms.ValidationError(_('A chave deve conter apenas letras, números e underscores'))

        # Check uniqueness within model
        qs = CustomField.objects.filter(key=key, model=model)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError(_('Já existe um campo com esta chave para este modelo'))

        return key
