from django import forms
from .models import EquipamentoCliente, Cliente
from equipamentos.models import EquipamentoFabricado

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
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'empresa', 'telefone', 'email', 'endereco']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'empresa': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da empresa'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telefone'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Endereço', 'rows': 3}),
        }

class EquipamentoForm(forms.ModelForm):
    equipamento_fabricado = forms.ModelChoiceField(
        queryset=EquipamentoFabricado.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Equipamento Fabricado"
    )
    numero_serie = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Número de Série"
    )
    data_aquisicao = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Data de Aquisição"
    )

    class Meta:
        model = EquipamentoCliente
        fields = ['equipamento_fabricado', 'numero_serie', 'data_aquisicao']

    def clean_numero_serie(self):
        numero = self.cleaned_data.get('numero_serie')
        # Verifica se já existe um equipamento com o mesmo número de série
        if EquipamentoCliente.objects.filter(numero_serie=numero).exists():
            raise forms.ValidationError("Este número de série já está associado a outro equipamento e/ou cliente.")
        return numero