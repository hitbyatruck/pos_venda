from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import PedidoAssistencia, ItemPat

class BaseItemPatFormSet(BaseInlineFormSet):
    def clean(self):
        """Validação simplificada do formset"""
        super().clean()
        
        # Retorna se não tiver dados limpos
        if not hasattr(self, 'cleaned_data'):
            return
        
        for form in self.forms:
            if not hasattr(form, 'cleaned_data'):
                continue
                
            # Pula formulários marcados para deleção
            if form.cleaned_data.get('DELETE', False):
                continue
                
            # Verifica se a linha está vazia (todos os campos principais vazios)
            is_empty = not any([
                form.cleaned_data.get('tipo'),
                form.cleaned_data.get('referencia', '').strip(),
                form.cleaned_data.get('designacao', '').strip()
            ])
            
            # Se estiver vazia, marca para exclusão se tiver ID
            if is_empty:
                if form.cleaned_data.get('id'):
                    form.cleaned_data['DELETE'] = True
                continue
            
            # Se não estiver vazia, verifica se está completa
            tipo = form.cleaned_data.get('tipo')
            referencia = form.cleaned_data.get('referencia', '').strip()
            designacao = form.cleaned_data.get('designacao', '').strip()
            
            if not tipo:
                form.add_error('tipo', 'Este campo é obrigatório')
            if not referencia:
                form.add_error('referencia', 'Este campo é obrigatório')
            if not designacao:
                form.add_error('designacao', 'Este campo é obrigatório')



class PedidoAssistenciaForm(forms.ModelForm):
    class Meta:
        model = PedidoAssistencia
        fields = [
            'cliente',
            'data_entrada',
            'estado',
            'equipamento',
            'relatorio',
            'garantia',
            'data_reparacao',
            'pat_number',
        ]
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control', 'id': 'id_cliente'}),
            'data_entrada': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'equipamento': forms.Select(attrs={'class': 'form-control', 'id': 'id_equipamento'}),
            'relatorio': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'garantia': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'data_reparacao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'pat_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex.: PAT-2025-001'
            }),
        }
        help_texts = {
            'garantia': 'Marque se o equipamento estiver em garantia.',
            'data_entrada': 'Data em que o equipamento foi recebido.',
            'data_reparacao': 'Data em que o equipamento foi reparado (se aplicável).',
            'estado': 'Estado atual do pedido de assistência.',
            'equipamento': 'Equipamento associado ao pedido.',
            'relatorio': 'Relatório técnico sobre o pedido de assistência.',
            'pat_number': 'Número do pedido de assistência técnica.',
        }
        labels = {
            'garantia': 'Em Garantia',
            'data_entrada': 'Data de Entrada',
            'data_reparacao': 'Data de Reparação',
            'estado': 'Estado da PAT',
            'equipamento': 'Equipamento',
            'relatorio': 'Relatório',
            'pat_number': 'Número da PAT',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Adicionar classes is-invalid para campos com erros
        for field_name, field in self.fields.items():
            if field_name in self.errors:
                css_class = field.widget.attrs.get('class', '') + ' is-invalid'
                field.widget.attrs['class'] = css_class.strip()

# Alias for PedidoAssistenciaForm - used in the views
PatForm = PedidoAssistenciaForm

class ItemPatForm(forms.ModelForm):
    class Meta:
        model = ItemPat
        fields = ['tipo', 'referencia', 'designacao', 'quantidade', 'preco']
        widgets = {
            'tipo': forms.Select(attrs={
                'class': 'form-control',
                'data-empty-option': 'Selecione um tipo'
            }),
            'referencia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Referência'
            }),
            'designacao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Designação'
            }),
            'quantidade': forms.NumberInput(attrs={
                'class': 'form-control quantidade',
                'min': '1',
                'value': '1'
            }),
            'preco': forms.NumberInput(attrs={
                'class': 'form-control preco',
                'step': '0.01',
                'value': '0.00'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False
        
        # Garantir valores iniciais para novos formulários
        if not self.instance.pk:
            self.fields['quantidade'].initial = 1
            self.fields['preco'].initial = 0.00
        
        # Adicionar classes is-invalid para campos com erros
        if self.errors:
            for field_name, field in self.fields.items():
                if field_name in self.errors:
                    css_class = field.widget.attrs.get('class', '') + ' is-invalid'
                    field.widget.attrs['class'] = css_class.strip()

    def clean(self):
        cleaned_data = super().clean()
        
        # Se marcado para exclusão, retorna sem validar
        if cleaned_data.get('DELETE', False):
            return cleaned_data
            
        # Garante valores padrão
        cleaned_data['quantidade'] = cleaned_data.get('quantidade', 1) or 1
        cleaned_data['preco'] = cleaned_data.get('preco', 0.00) or 0.00
        
        return cleaned_data
    
PedidoAssistenciaFormSet = inlineformset_factory(
    PedidoAssistencia,
    ItemPat,
    form=ItemPatForm,
    formset=BaseItemPatFormSet,
    extra=1,
    can_delete=True,
    fields=['tipo', 'referencia', 'designacao', 'quantidade', 'preco'],
    validate_min=False,
    validate_max=False,
    min_num=0
)

PatItemFormSet = PedidoAssistenciaFormSet

EditItemPatFormSet = inlineformset_factory(
    PedidoAssistencia,
    ItemPat,
    form=ItemPatForm,
    formset=BaseItemPatFormSet,
    extra=0,
    can_delete=True,
    fields=['tipo', 'referencia', 'designacao', 'quantidade', 'preco'],
    validate_min=False,
    validate_max=False,
    min_num=0
)