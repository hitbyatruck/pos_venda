from django import forms
from .models import PedidoAssistencia, ItemPat
from django.forms import inlineformset_factory

class PedidoAssistenciaForm(forms.ModelForm):
    class Meta:
        model = PedidoAssistencia
        fields = [
            'cliente', 
            'pat_number', 
            'data_entrada', 
            'estado', 
            'equipamento', 
            'relatorio',
            'garantia',
            'data_reparacao',
        ]
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control', 'id': 'id_cliente'}),
            'pat_number': forms.TextInput(attrs={'class': 'form-control'}),
            'data_entrada': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'equipamento': forms.Select(attrs={'class': 'form-control', 'id': 'id_equipamento'}),
            'relatorio': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'garantia': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'data_reparacao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'garantia': 'Em Garantia'
        }
        help_texts = {
            'garantia': 'Marque se o equipamento estiver em garantia.',
        }

class ItemPatFormSet(forms.ModelForm):
    class Meta:
        model = ItemPat
        fields = ['tipo', 'referencia', 'designacao', 'quantidade', 'preco']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'referencia': forms.TextInput(attrs={'class': 'form-control'}),
            'designacao': forms.TextInput(attrs={'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'preco': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class ItemPatForm(forms.ModelForm):
    class Meta:
        model = ItemPat
        fields = ['tipo', 'referencia', 'designacao', 'quantidade', 'preco']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'referencia': forms.TextInput(attrs={'class': 'form-control'}),
            'designacao': forms.TextInput(attrs={'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'preco': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

# Formset para criação (pode ter um extra)
PedidoAssistenciaFormSet = inlineformset_factory(
    PedidoAssistencia, 
    ItemPat, 
    form=ItemPatFormSet, 
    extra=1, 
    can_delete=True
)

# Formset para edição: não renderiza formulário extra
EditItemPatFormSet = inlineformset_factory(
    PedidoAssistencia, 
    ItemPat, 
    form=ItemPatFormSet, 
    extra=1, 
    can_delete=True
)