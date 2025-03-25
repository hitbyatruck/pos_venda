from django import forms
from .models import EquipamentoCliente, Cliente
from equipamentos.models import EquipamentoFabricado

class EquipamentoClienteForm(forms.ModelForm):
    class Meta:
        model = EquipamentoCliente
        fields = ['equipamento_fabricado', 'numero_serie', 'data_aquisicao']
        widgets = {
            'equipamento_fabricado': forms.Select(attrs={'class': 'form-control'}),
            'numero_serie': forms.TextInput(attrs={'class': 'form-control'}),
            'data_aquisicao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        
        
              
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'empresa', 'telefone', 'email', 'morada', 'codigo_postal', 'localidade', 'pais', 'nif', 'contacto_principal']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'morada': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'codigo_postal': forms.TextInput(attrs={'class': 'form-control'}),
            'localidade': forms.TextInput(attrs={'class': 'form-control'}),
            'pais': forms.TextInput(attrs={'class': 'form-control'}),
            'nif': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_principal': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'nome': 'Nome',
            'empresa': 'Empresa',
            'telefone': 'Telefone',
            'email': 'Email',
            'morada': 'Morada',
            'codigo_postal': 'Código Postal',
            'localidade': 'Localidade',
            'pais': 'País',
            'nif': 'NIF',
            'contacto_principal': 'Contacto Principal',
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