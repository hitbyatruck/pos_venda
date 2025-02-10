from django import forms
from .models import EquipamentoFabricado, DocumentoEquipamento, CategoriaEquipamento, EquipamentoCliente

class EquipamentoFabricadoForm(forms.ModelForm):
    class Meta:
        model = EquipamentoFabricado
        fields = ['nome', 'referencia_interna', 'descricao', 'especificacoes', 'categoria', 'foto']

    def __init__(self, *args, **kwargs):
        super(EquipamentoFabricadoForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class DocumentoEquipamentoForm(forms.ModelForm):
    class Meta:
        model = DocumentoEquipamento
        fields = ['arquivo']

    def __init__(self, *args, **kwargs):
        super(DocumentoEquipamentoForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
    
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