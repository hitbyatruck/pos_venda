# notas/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import Nota, Tarefa
from clientes.models import Cliente  # Para filtrar o campo PAT
# Note: Não fazemos uma importação de PedidoAssistencia no nível do módulo
# para evitar problemas de escopo; ela será importada localmente no __init__.

# --- Formulário para Nota de Conversa ---
class NotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        # Os campos que o usuário preenche; 'cliente' é obrigatório no modelo,
        # mas a partir dos detalhes do cliente já virá pré-definido.
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
        # Garanta que o campo 'cliente' seja obrigatório (já que na criação vem da página de detalhes)
        self.fields['cliente'].required = True
        self.fields['pat'].required = False  # PAT é opcional

        # Tente obter o cliente a partir da instância (se já salva) ou dos dados iniciais
        cliente = None
        if self.instance and self.instance.pk:
            cliente = self.instance.cliente
        elif 'cliente' in self.initial and self.initial['cliente']:
            try:
                cliente = Cliente.objects.get(id=self.initial['cliente'])
            except Cliente.DoesNotExist:
                cliente = None

        # Importação local de PedidoAssistencia com alias para evitar conflitos
        from assistencia.models import PedidoAssistencia as PA
        if cliente:
            # Limitar o queryset do campo PAT às PAT's associadas ao cliente
            self.fields['pat'].queryset = PA.objects.filter(cliente=cliente)
        else:
            self.fields['pat'].queryset = PA.objects.none()


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
        # Torna os campos 'cliente' e 'pat' opcionais
        self.fields['cliente'].required = False
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
        from assistencia.models import PedidoAssistencia as PA
        if cliente:
            self.fields['pat'].queryset = PA.objects.filter(cliente=cliente)
        else:
            self.fields['pat'].queryset = PA.objects.none()
