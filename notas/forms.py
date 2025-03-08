# notas/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import Nota, Tarefa, PedidoAssistencia
from clientes.models import Cliente, EquipamentoCliente # Para filtrar o campo PAT
# Note: Não fazemos uma importação de PedidoAssistencia no nível do módulo
# para evitar problemas de escopo; ela será importada localmente no __init__.

# --- Formulário para Nota de Conversa ---
class NotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = ['titulo', 'cliente', 'pat', 'equipamento', 'conteudo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'pat': forms.Select(attrs={'class': 'form-control'}),
            'equipamento': forms.Select(attrs={'class': 'form-control'}),
            'conteudo': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super(NotaForm, self).__init__(*args, **kwargs)
        self.fields['cliente'].required = True
        self.fields['pat'].required = False  # PAT é opcional
        self.fields['equipamento'].required = False  # Equipamento também pode ser opcional

        cliente = self.initial.get('cliente') or (self.instance.cliente if self.instance.pk else None)

        from assistencia.models import PedidoAssistencia
        if cliente:
            self.fields['pat'].queryset = PedidoAssistencia.objects.filter(cliente=cliente)
        else:
            self.fields['pat'].queryset = PedidoAssistencia.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        cliente = cleaned_data.get('cliente')
        pat = cleaned_data.get('pat')
        equipamento = cleaned_data.get('equipamento')

        if pat and cliente and pat.cliente != cliente:
            self.add_error('pat', 'A PAT selecionada não pertence ao cliente escolhido.')

        if equipamento and cliente and equipamento.cliente != cliente:
            self.add_error('equipamento', 'O Equipamento selecionado não pertence ao cliente escolhido.')

        return cleaned_data


# --- Formulário para Tarefa (associada a uma Nota) ---
class TarefaForm(forms.ModelForm):
    class Meta:
        model = Tarefa
        # O usuário preencherá apenas a descrição e escolherá o status (que poderá ser um toggle via JS)
        fields = ['descricao', 'status']
        widgets = {
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

# Cria um formset inline para as tarefas associadas à nota.
TarefaFormSet = inlineformset_factory(
    Nota,
    Tarefa,
    form=TarefaForm,
    extra=1,
    can_delete=True
)

EditTarefaFormSet = inlineformset_factory(
    Nota,
    Tarefa,
    form=TarefaForm,
    extra=0,   # Na edição, não queremos formulário extra
    can_delete=True
)


# --- Formulário para Tarefa Independente ---
class TarefaIndependenteForm(forms.ModelForm):
    class Meta:
        model = Tarefa
        fields = ['cliente', 'pat', 'descricao', 'status']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'pat': forms.Select(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(TarefaIndependenteForm, self).__init__(*args, **kwargs)
        self.fields['cliente'].required = True  # 🔹 Torna o cliente obrigatório
        self.fields['pat'].required = False

        cliente = None
        if self.instance and self.instance.pk:
            cliente = self.instance.cliente
        elif 'cliente' in self.initial and self.initial['cliente']:
            try:
                from clientes.models import Cliente
                cliente = Cliente.objects.get(id=self.initial['cliente'])
            except Cliente.DoesNotExist:
                cliente = None
        
        from assistencia.models import PedidoAssistencia
        if cliente:
            self.fields['pat'].queryset = PedidoAssistencia.objects.filter(cliente=cliente)
        else:
            self.fields['pat'].queryset = PedidoAssistencia.objects.none()
