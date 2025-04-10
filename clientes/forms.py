from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Cliente, Setor, Contacto, TipoContacto, CategoriaCliente
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

class ClienteForm(forms.ModelForm):
    """Form for all customers (unified form)"""
    class Meta:
        model = Cliente
        fields = [
            'nome', 'imagem', 'website', 'email_principal', 'setor',
            'nif', 'percentagem_iva', 'desconto',
            'morada', 'codigo_postal', 'cidade', 'pais',
            'usar_mesma_morada', 'morada_entrega', 'codigo_postal_entrega', 
            'cidade_entrega', 'pais_entrega', 'observacoes'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'imagem': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'email_principal': forms.EmailInput(attrs={'class': 'form-control'}),
            'setor': forms.Select(attrs={'class': 'form-control'}),
            'nif': forms.TextInput(attrs={'class': 'form-control'}),
            'percentagem_iva': forms.NumberInput(attrs={'class': 'form-control'}),
            'desconto': forms.NumberInput(attrs={'class': 'form-control'}),
            'morada': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_postal': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'pais': CountrySelectWidget(attrs={'class': 'form-control'}),
            'usar_mesma_morada': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'morada_entrega': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_postal_entrega': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade_entrega': forms.TextInput(attrs={'class': 'form-control'}),
            'pais_entrega': CountrySelectWidget(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make some fields required
        self.fields['nome'].required = True
        
        # Setup shipping address toggle
        self.fields['usar_mesma_morada'].widget.attrs['onchange'] = 'toggleShippingAddress(this.checked)'

class ContactoForm(forms.ModelForm):
    class Meta:
        model = Contacto
        fields = ['tipo', 'valor', 'nome_contacto', 'cargo', 'principal', 'observacoes']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'valor': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_contacto': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'principal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class SetorForm(forms.ModelForm):
    class Meta:
        model = Setor
        fields = ['nome', 'descricao', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class TipoContactoForm(forms.ModelForm):
    # Common regex patterns - fix invalid escape sequences with raw strings (r prefix)
    REGEX_PATTERNS = [
        ('', _('Sem validação')),
        (r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', _('Email')),
        (r'^\+?(\d{1,3})?[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}$', _('Telefone')),
        (r'^(https?|ftp):\/\/[^\s/$.?#].[^\s]*$', _('URL/Website')),
        (r'^\d{4}-\d{3}$', _('Código Postal (Portugal)')),
        (r'^\d{9}$', _('NIF (Portugal)')),
    ]
    
    # Most common FontAwesome icons for contacts
    ICON_CHOICES = [
        ('', _('Sem ícone')),
        ('fa-envelope', _('✉️ Email (fa-envelope)')),
        ('fa-phone', _('📞 Telefone (fa-phone)')),
        ('fa-mobile-alt', _('📱 Celular (fa-mobile-alt)')),
        ('fa-fax', _('📠 Fax (fa-fax)')),
        ('fa-whatsapp', _('WhatsApp (fa-whatsapp)')),
        ('fa-facebook', _('Facebook (fa-facebook)')),
        ('fa-linkedin', _('LinkedIn (fa-linkedin)')),
        ('fa-twitter', _('Twitter (fa-twitter)')),
        ('fa-instagram', _('Instagram (fa-instagram)')),
        ('fa-skype', _('Skype (fa-skype)')),
        ('fa-map-marker-alt', _('📍 Localização (fa-map-marker-alt)')),
        ('fa-globe', _('🌐 Website (fa-globe)')),
    ]
    
    # Override field to provide choices
    regex_pattern = forms.ChoiceField(
        choices=REGEX_PATTERNS,
        required=False,
        label=_("Padrão de Validação"),
        help_text=_('Selecione um padrão de validação ou deixe em branco para não validar'),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    
    # Custom field for icon selection
    icon_choice = forms.ChoiceField(
        choices=ICON_CHOICES,
        required=False,
        label=_("Ícone"),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'onchange': 'updateIconPreview(this.value)'
        }),
    )
    
    class Meta:
        model = TipoContacto
        fields = ['nome', 'icone', 'validador_regex', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'icone': forms.HiddenInput(),  # We'll use our custom field instead
            'validador_regex': forms.HiddenInput(),  # We'll use our custom field instead
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'icone': _('Classe CSS do FontAwesome (ex: fa-envelope, fa-phone)'),
            'validador_regex': _('Expressão regular para validar o valor do contacto (opcional)'),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial values for custom fields if we're editing an existing instance
        if self.instance and self.instance.pk:
            # Set the icon choice from the instance
            if self.instance.icone:
                self.fields['icon_choice'].initial = self.instance.icone
            
            # Set the regex pattern choice from the instance
            if self.instance.validador_regex:
                # Try to find a matching pattern in our choices
                for pattern, _ in self.REGEX_PATTERNS:
                    if pattern == self.instance.validador_regex:
                        self.fields['regex_pattern'].initial = pattern
                        break
    
    def clean(self):
        cleaned_data = super().clean()
        # Copy values from our custom fields to the model fields
        cleaned_data['icone'] = cleaned_data.get('icon_choice', '')
        cleaned_data['validador_regex'] = cleaned_data.get('regex_pattern', '')
        return cleaned_data