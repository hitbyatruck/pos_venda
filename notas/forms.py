# notas/forms.py
from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import Nota, Tarefa, PedidoAssistencia
from clientes.models import Cliente, EquipamentoCliente  # Para filtrar o campo PAT

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

        from assistencia.models import PedidoAssistencia
        # Se houver dados no POST (self.data), usamos para filtrar o queryset.
        if 'cliente' in self.data:
            try:
                cliente_id = int(self.data.get('cliente'))
                self.fields['pat'].queryset = PedidoAssistencia.objects.filter(cliente=cliente_id)
            except (ValueError, TypeError):
                self.fields['pat'].queryset = PedidoAssistencia.objects.none()
        elif self.instance and self.instance.pk:
            self.fields['pat'].queryset = PedidoAssistencia.objects.filter(cliente=self.instance.cliente)
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
        fields = ['descricao', 'status']
        widgets = {
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

# --- Classe base customizada para o formset de Tarefa ---
class BaseTarefaFormSet(BaseInlineFormSet):
    def save_new(self, form, commit=True):
        """Save new task and ensure it has the correct client"""
        instance = super().save_new(form, commit=False)
        
        # Always set the client from the parent nota
        instance.cliente = self.instance.cliente
        
        if commit:
            instance.save()
            # Save many-to-many data if commit=True
            form.save_m2m()
        
        return instance

# Cria o formset inline para as tarefas associadas à nota, usando a classe base customizada.
TarefaFormSet = inlineformset_factory(
    Nota,
    Tarefa,
    form=TarefaForm,
    formset=BaseTarefaFormSet,
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
        self.fields['cliente'].required = True
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
