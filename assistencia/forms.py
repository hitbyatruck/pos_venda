from django import forms
from .models import PedidoAssistencia
from equipamentos.models import EquipamentoCliente

class PedidoAssistenciaForm(forms.ModelForm):
    class Meta:
        model = PedidoAssistencia
        fields = ['cliente', 'numero_pedido', 'equipamento', 'em_garantia', 'data_entrada', 'data_reparacao', 'estado']

    def __init__(self, *args, **kwargs):
        cliente_id = kwargs.pop('cliente_id', None)  # Obtém cliente_id passado da view
        super().__init__(*args, **kwargs)
        
        # Inicializa o campo equipamento apenas se houver cliente selecionado
        if cliente_id:
            self.fields['equipamento'].queryset = EquipamentoCliente.objects.filter(cliente_id=cliente_id)
        else:
            self.fields['equipamento'].queryset = EquipamentoCliente.objects.none()