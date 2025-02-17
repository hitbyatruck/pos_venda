from django import forms
from .models import EquipamentoFabricado, DocumentoEquipamento, CategoriaEquipamento
from clientes.models import EquipamentoCliente
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
            'arquivo': forms.FileInput(attrs={'class': 'form-control'})  # Corrigido para suportar um ficheiro de cada vez
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
    class Meta:
        model = CategoriaEquipamento
        fields = ['nome']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'})
        }
