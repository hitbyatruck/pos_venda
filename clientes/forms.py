from django import forms
from django.utils.translation import gettext_lazy as _
from django_countries.widgets import CountrySelectWidget
from django.forms import inlineformset_factory
from .models import Cliente, Empresa, Individual, Setor, Contacto, TipoContacto, EquipamentoCliente

class SetorForm(forms.ModelForm):
    """
    Form para criação e edição de setores de empresas.
    """
    class Meta:
        model = Setor
        fields = ['nome', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nome do setor')}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Descrição do setor')}),
        }

class ClienteBaseForm(forms.ModelForm):
    """Form base para os campos comuns de empresa e individual"""
    class Meta:
        model = Cliente
        fields = [
            'nome', 'website', 'setor', 'imagem',
            'nif', 'regime_iva', 'desconto_padrao',
            'morada', 'codigo_postal', 'cidade', 'pais',
            'observacoes', 'ativo'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'setor': forms.Select(attrs={'class': 'form-control select2'}),
            'imagem': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'nif': forms.TextInput(attrs={'class': 'form-control'}),
            'regime_iva': forms.Select(attrs={'class': 'form-control'}),
            'desconto_padrao': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'morada': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_postal': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'pais': CountrySelectWidget(attrs={'class': 'form-control select2'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nome': _('Nome'),
            'website': _('Website'),
            'setor': _('Setor de Atividade'),
            'imagem': _('Imagem'),
            'nif': _('NIF'),
            'regime_iva': _('Regime de IVA'),
            'desconto_padrao': _('Desconto Padrão (%)'),
            'morada': _('Morada'),
            'codigo_postal': _('Código Postal'),
            'cidade': _('Cidade'),
            'pais': _('País'),
            'observacoes': _('Observações'),
            'ativo': _('Cliente Ativo'),
        }

class EmpresaForm(ClienteBaseForm):
    """Form para Empresas"""
    class Meta(ClienteBaseForm.Meta):
        model = Empresa
        fields = ClienteBaseForm.Meta.fields + ['nome_comercial']
        widgets = {
            **ClienteBaseForm.Meta.widgets,
            'nome_comercial': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['tipo'] = 'empresa'
    
    def save(self, commit=True):
        # Garantir que o tipo seja sempre "empresa"
        instance = super().save(commit=False)
        instance.tipo = 'empresa'
        if commit:
            instance.save()
        return instance

class IndividualForm(ClienteBaseForm):
    """Form para Clientes Individuais"""
    class Meta(ClienteBaseForm.Meta):
        model = Individual
        fields = ClienteBaseForm.Meta.fields + ['empresa_associada', 'cargo']
        widgets = {
            **ClienteBaseForm.Meta.widgets,
            'empresa_associada': forms.Select(attrs={'class': 'form-control select2'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['tipo'] = 'individual'
    
    def save(self, commit=True):
        # Garantir que o tipo seja sempre "individual"
        instance = super().save(commit=False)
        instance.tipo = 'individual'
        if commit:
            instance.save()
        return instance

class ContactoForm(forms.ModelForm):
    """
    Form para o modelo Contacto com campos melhorados para usabilidade.
    """
    
    class Meta:
        model = Contacto
        fields = ['tipo', 'valor', 'nome_contacto', 'cargo', 'principal', 'observacoes']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control select2', 'placeholder': 'Selecione o tipo'}),
            'valor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email, telefone, etc.'}),
            'nome_contacto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da pessoa de contacto'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cargo ou posição'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'tipo': 'Tipo de Contacto',
            'valor': 'Contacto',
            'nome_contacto': 'Nome do Contacto',
            'cargo': 'Cargo',
            'principal': 'É Principal',
            'observacoes': 'Observações'
        }

# Use ModelFormSet_factory para criar um formset para contactos
ContactoFormSet = forms.inlineformset_factory(
    Cliente, 
    Contacto,
    form=ContactoForm,
    extra=1, 
    can_delete=True,
    can_delete_extra=True
)

class EquipamentoClienteForm(forms.ModelForm):
    """Form para associar equipamentos a clientes"""
    class Meta:
        model = EquipamentoCliente
        fields = ['cliente', 'equipamento_fabricado', 'numero_serie', 'data_aquisicao', 'data_instalacao', 'observacoes']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control select2'}),
            'equipamento_fabricado': forms.Select(attrs={'class': 'form-control select2'}),
            'numero_serie': forms.TextInput(attrs={'class': 'form-control'}),
            'data_aquisicao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_instalacao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        cliente_id = kwargs.pop('cliente_id', None)
        super().__init__(*args, **kwargs)
        
        if cliente_id:
            self.fields['cliente'].initial = cliente_id
            self.fields['cliente'].widget.attrs['readonly'] = True

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'email', 'telefone', 'endereco']  # Ensure these fields match the model
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class TipoContactoForm(forms.ModelForm):
    """
    Form para criação e edição de tipos de contacto.
    """
    class Meta:
        model = TipoContacto
        fields = ['nome', 'icone', 'validador_regex', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nome do tipo de contacto')}),
            'icone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ex: fa-envelope, fa-phone')}),
            'validador_regex': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Expressão regular para validação')}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'icone': _('Classe CSS para ícone FontAwesome (ex: fa-envelope, fa-phone).'),
            'validador_regex': _('Expressão regular para validação do formato do contacto (opcional).'),
        }