from django import forms
from .models import EquipamentoCliente

class EquipamentoClienteForm(forms.ModelForm):
    data_aquisicao = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        label="Data de Aquisição"
    )

    class Meta:
        model = EquipamentoCliente
        fields = ["equipamento_fabricado", "numero_serie", "data_aquisicao"]
        widgets = {
            "equipamento_fabricado": forms.Select(attrs={"class": "form-control"}),
            "numero_serie": forms.TextInput(attrs={"class": "form-control"}),
        }
        labels = {
            "equipamento_fabricado": "Equipamento",
            "numero_serie": "Número de Série",
        }
    # Compare this snippet from clientes/views.py:          
