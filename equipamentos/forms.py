from django import forms
from django.utils.translation import gettext_lazy as _  # Add this import
from django.db.models import Max
from .models import EquipamentoFabricado, EquipamentoCliente, CategoriaEquipamento, DocumentoEquipamento
from .widgets import CustomClearableFileInput

class EquipamentoFabricadoForm(forms.ModelForm):
    class Meta:
        model = EquipamentoFabricado
        fields = ['nome', 'referencia_interna', 'descricao', 'especificacoes', 'categoria', 'fotografia']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'referencia_interna': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control'}),
            'especificacoes': forms.Textarea(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'fotografia': CustomClearableFileInput(attrs={'class': 'form-control'}),
        }

class DocumentoEquipamentoForm(forms.ModelForm):
    class Meta:
        model = DocumentoEquipamento
        fields = ['arquivo']
        widgets = {
            'arquivo': forms.FileInput(attrs={'class': 'form-control'})
        }

class EquipamentoClienteForm(forms.ModelForm):
    equipamento = forms.ModelChoiceField(
        queryset=EquipamentoFabricado.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Equipamento Fabricado"
    )
    numero_serie = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Número de Série"
    )
    data_aquisicao = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Data de Aquisição"
    )

    class Meta:
        model = EquipamentoCliente
        fields = ['equipamento', 'numero_serie', 'data_aquisicao']

class CategoriaEquipamentoForm(forms.ModelForm):
    pai = forms.ModelChoiceField(
        queryset=CategoriaEquipamento.objects.all(),
        required=False,
        label=_("Categoria Pai"),
        help_text=_("Deixe em branco para criar uma categoria de nível raiz"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = CategoriaEquipamento
        fields = ['nome', 'descricao', 'pai', 'ativo']  # Keep ordem as auto-generated
        # You can add ordem to fields if you want users to set it manually
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def save(self, commit=True):
        # Call parent's save to get the instance
        instance = super().save(commit=False)

        # Auto-generate ordem value if it's not set
        if not instance.ordem:
            # Get the highest ordem value and add 1
            max_ordem = CategoriaEquipamento.objects.aggregate(Max('ordem'))['ordem__max'] or 0
            instance.ordem = max_ordem + 10  # Use increments of 10 for easier reordering later

        if commit:
            instance.save()
        return instance
