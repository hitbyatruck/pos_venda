from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import PedidoAssistencia, ItemPAT
from clientes.models import Cliente
from equipamentos.models import EquipamentoCliente
from django.utils.translation import gettext_lazy as _

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
    """Form for creating a new PAT"""

    class Meta:
        model = PedidoAssistencia
        fields = ['pat_number', 'cliente', 'equipamento', 'numero_serie_equipamento',
                 'data_entrada', 'estado', 'descricao_problema', 'relatorio', 'data_conclusao']
        widgets = {
            'pat_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Digite o número da PAT'), 'required': True}),
            'cliente': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'equipamento': forms.Select(attrs={'class': 'form-select'}),
            'numero_serie_equipamento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Se o equipamento não estiver cadastrado')}),
            'data_entrada': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': True}),
            'estado': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'descricao_problema': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'required': True}),
            'relatorio': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'data_conclusao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make these fields required
        self.fields['pat_number'].required = True
        self.fields['cliente'].required = True
        self.fields['data_entrada'].required = True
        self.fields['estado'].required = True
        self.fields['descricao_problema'].required = True

        # Make these fields optional
        self.fields['equipamento'].required = False
        self.fields['numero_serie_equipamento'].required = False
        self.fields['relatorio'].required = False
        self.fields['data_conclusao'].required = False

        # Generate a suggested PAT number if this is a new PAT
        if not self.instance.pk and not self.initial.get('pat_number'):
            from datetime import datetime
            today = datetime.now()
            prefix = f"PAT-{today.strftime('%Y%m%d')}"

            # Count existing PATs with today's prefix and increment
            count = PedidoAssistencia.objects.filter(pat_number__startswith=prefix).count()
            next_number = count + 1

            # Generate the PAT number
            self.initial['pat_number'] = f"{prefix}-{next_number:03d}"

        # Handle equipment queryset logic - IMPROVED version
        client_id = None
        equipment_id = None

        # Track the current state for debugging
        is_bound = self.is_bound
        has_instance = bool(self.instance and self.instance.pk)

        # First check POST data
        if self.is_bound and 'cliente' in self.data:
            client_id = self.data.get('cliente')
            equipment_id = self.data.get('equipamento')

        # Then check instance
        elif self.instance and self.instance.pk:
            if self.instance.cliente:
                client_id = self.instance.cliente.id
            if self.instance.equipamento:
                equipment_id = self.instance.equipamento.id

        # Lastly check initial data
        elif 'cliente' in self.initial:
            client_id = self.initial.get('cliente')
            equipment_id = self.initial.get('equipamento')

        # Set equipment queryset based on client ID
        if client_id:
            try:
                # Set the queryset to all equipment for this client
                self.fields['equipamento'].queryset = EquipamentoCliente.objects.filter(cliente_id=client_id)

                # If we have a specific equipment ID that's not in the queryset, add it
                if equipment_id and not self.fields['equipamento'].queryset.filter(id=equipment_id).exists():
                    try:
                        specific_equipment = EquipamentoCliente.objects.get(id=equipment_id)
                        # Create a special queryset that includes our specific equipment
                        self.fields['equipamento'].queryset = self.fields['equipamento'].queryset | EquipamentoCliente.objects.filter(id=equipment_id)
                    except EquipamentoCliente.DoesNotExist:
                        pass
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error setting equipment queryset: {str(e)}, bound={is_bound}, instance={has_instance}")
                self.fields['equipamento'].queryset = EquipamentoCliente.objects.none()
        else:
            self.fields['equipamento'].queryset = EquipamentoCliente.objects.none()

    def clean(self):
        cleaned_data = super().clean()

        # Ensure either equipamento or numero_serie_equipamento is provided
        equipamento = cleaned_data.get('equipamento')
        numero_serie = cleaned_data.get('numero_serie_equipamento')

        if not equipamento and not numero_serie:
            self.add_error('equipamento', _('Selecione um equipamento existente ou forneça um número de série.'))
            self.add_error('numero_serie_equipamento', _('Forneça um número de série ou selecione um equipamento existente.'))

        # Ensure that data_conclusao is only set when estado is 'concluido'
        estado = cleaned_data.get('estado')
        data_conclusao = cleaned_data.get('data_conclusao')

        if estado != 'concluido' and data_conclusao:
            self.add_error('data_conclusao', _('A data de conclusão só pode ser definida quando o estado é "Concluído".'))

        return cleaned_data


class ItemPatForm(forms.ModelForm):
    """Form for PAT line items (parts, services, components)"""

    class Meta:
        model = ItemPAT
        fields = ['tipo', 'referencia', 'designacao', 'quantidade', 'preco_unitario']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select tipo-select'}),
            'referencia': forms.TextInput(attrs={'class': 'form-control', 'required': False}),
            'designacao': forms.TextInput(attrs={'class': 'form-control', 'required': False}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01', 'required': False}),
            'preco_unitario': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01', 'required': False}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make all fields optional initially
        for field in self.fields.values():
            field.required = False

        # Add empty placeholder option to tipo field but PRESERVE the original choices
        original_choices = list(self.fields['tipo'].choices)
        self.fields['tipo'].choices = [('', _('Selecione o tipo de item'))] + original_choices[1:]

    def clean(self):
        """
        Custom validation to make fields required only if the item is not empty
        and the tipo field is selected
        """
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        referencia = cleaned_data.get('referencia')
        designacao = cleaned_data.get('designacao')
        quantidade = cleaned_data.get('quantidade')
        preco_unitario = cleaned_data.get('preco_unitario')

        # If tipo is empty (placeholder option selected), treat the entire row as empty
        # and don't perform validation regardless of other fields
        if not tipo:
            return cleaned_data

        # Check if this item has any data (not empty)
        has_data = tipo or referencia or designacao or quantidade or preco_unitario

        # If any field has data, then the item is not empty and certain fields become required
        if has_data:
            if not tipo:
                self.add_error('tipo', _('O tipo é obrigatório quando preenchendo um item.'))
            if not designacao:
                self.add_error('designacao', _('Este campo é obrigatório quando preenchendo um item.'))
            if not quantidade:
                self.add_error('quantidade', _('Este campo é obrigatório quando preenchendo um item.'))
            if not preco_unitario:
                self.add_error('preco_unitario', _('Este campo é obrigatório quando preenchendo um item.'))

        return cleaned_data


# Create formsets for handling multiple items - Make sure can_empty is True
PedidoAssistenciaFormSet = inlineformset_factory(
    PedidoAssistencia,
    ItemPAT,
    form=ItemPatForm,
    formset=BaseItemPatFormSet,
    extra=1,
    can_delete=True,
    fields=['tipo', 'referencia', 'designacao', 'quantidade', 'preco_unitario'],
    validate_min=False,  # Allow empty formset
    min_num=0,  # No minimum required
)

# Special formset for editing with no extra forms
EditItemPatFormSet = inlineformset_factory(
    PedidoAssistencia,
    ItemPAT,
    form=ItemPatForm,
    formset=BaseItemPatFormSet,
    extra=0,
    can_delete=True,
    fields=['tipo', 'referencia', 'designacao', 'quantidade', 'preco_unitario'],
    validate_min=False,  # Allow empty formset
    min_num=0,  # No minimum required
)

# Make sure your PatItemFormSet has a consistent prefix

from django.forms import inlineformset_factory
from .models import PedidoAssistencia, ItemPAT

class PatItemFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()

        for form in self.forms:
            # Skip if the form doesn't have cleaned_data
            if not hasattr(form, 'cleaned_data') or form.cleaned_data is None:
                continue

            # Skip forms marked for deletion
            if form.cleaned_data.get('DELETE', False):
                continue

            # Safely process referencia field - FIX THE NULL ISSUE
            referencia = form.cleaned_data.get('referencia')

            # Only add non-None references after stripping
            if referencia is not None:
                clean_ref = referencia.strip()
                # Additional validation can go here

            # Check for quantity and price
            quantidade = form.cleaned_data.get('quantidade')
            preco_unitario = form.cleaned_data.get('preco_unitario')

            if quantidade is not None and quantidade <= 0:
                form.add_error('quantidade', "Quantidade deve ser maior que zero.")

            if preco_unitario is not None and preco_unitario < 0:
                form.add_error('preco_unitario', "Preço não pode ser negativo.")

# Define the form for the ItemPAT model
class ItemPATForm(forms.ModelForm):
    class Meta:
        model = ItemPAT
        fields = ['tipo', 'referencia', 'designacao', 'quantidade', 'preco_unitario']
        widgets = {
            'quantidade': forms.NumberInput(attrs={'step': '1', 'min': '1'}),
            'preco_unitario': forms.NumberInput(attrs={'step': '0.01', 'min': '0'})
        }

# Create the inline formset factory using the models
PatItemFormSet = inlineformset_factory(
    PedidoAssistencia,
    ItemPAT,
    form=ItemPATForm,
    formset=PatItemFormSet,
    fields=['tipo', 'referencia', 'designacao', 'quantidade', 'preco_unitario'],
    extra=1,
    can_delete=True,
)

# These forms are used directly in views - add these back to fix import errors
class PatForm(PedidoAssistenciaForm):
    """Alias for PedidoAssistenciaForm for cleaner imports"""
    pass

# Ensure we have EditItemPatFormSet also available
EditItemPatFormSet = inlineformset_factory(
    PedidoAssistencia,
    ItemPAT,
    form=ItemPatForm,
    formset=BaseItemPatFormSet,
    extra=0,
    can_delete=True,
    fields=['tipo', 'referencia', 'designacao', 'quantidade', 'preco_unitario'],
    validate_min=False,
    min_num=0,
)