from django import forms
from .models import EquipamentoFabricado, DocumentoEquipamento, CategoriaEquipamento
from clientes.models import EquipamentoCliente

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
            'fotografia': forms.ClearableFileInput(attrs={'class': 'form-control'})
        }

class DocumentoEquipamentoForm(forms.ModelForm):
    class Meta:
        model = DocumentoEquipamento
        fields = ['arquivo']
        widgets = {
            'arquivo': forms.FileInput(attrs={'class': 'form-control'})  # Um arquivo por vez
        }
    
class EquipamentoClienteForm(forms.ModelForm):
    class Meta:
        model = EquipamentoCliente
        fields = ['equipamento_fabricado', 'numero_serie']

    def __init__(self, *args, **kwargs):
        super(EquipamentoClienteForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class CategoriaEquipamentoForm(forms.ModelForm):
    class Meta:
        model = CategoriaEquipamento
        fields = ['nome']