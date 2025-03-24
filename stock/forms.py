"""
Formulários para o módulo de Gestão de Stock
"""
# ===========================================
# IMPORTS
# ===========================================
from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory

from .models import (
    Peca, CategoriaPeca, Fornecedor, FornecedorPeca,
    EncomendaPeca, ItemEncomenda, MovimentacaoStock
)


# ===========================================
# FORMULÁRIOS DE PEÇAS E CATEGORIAS
# ===========================================
class PecaForm(forms.ModelForm):
    """
    Formulário para adicionar/editar peças
    """
    class Meta:
        model = Peca
        fields = [
            'codigo', 'nome', 'descricao', 'categoria', 'stock_minimo',
            'stock_atual', 'stock_ideal', 'localizacao',
            'preco_custo', 'preco_venda', 'imagem'
        ]
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'localizacao': forms.TextInput(attrs={'placeholder': _('Ex: Prateleira A, Gaveta 3')}),
        }
        labels = {
            'codigo': _('Código'),
            'descricao': _('Descrição'),
            'localizacao': _('Localização'),
            'preco_custo': _('Preço de Custo (€)'),
            'preco_venda': _('Preço de Venda (€)'),
        }
        help_texts = {
            'stock_minimo': _('Quantidade mínima em stock, abaixo da qual é gerado um alerta'),
            'stock_ideal': _('Quantidade ideal a ter em stock'),
            'localizacao': _('Onde esta peça está armazenada na empresa'),
        }


class CategoriaForm(forms.ModelForm):
    """
    Formulário para adicionar/editar categorias de peças
    """
    class Meta:
        model = CategoriaPeca
        fields = ['nome', 'descricao']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'descricao': _('Descrição'),
        }


# ===========================================
# FORMULÁRIOS DE FORNECEDORES
# ===========================================
class FornecedorForm(forms.ModelForm):
    """
    Formulário para adicionar/editar fornecedores
    """
    class Meta:
        model = Fornecedor
        fields = [
            'nome', 'contacto', 'telefone', 'email', 
            'website', 'notas'
        ]
        widgets = {
            'contacto': forms.TextInput(attrs={'placeholder': _('Nome do contacto')}),
            'notas': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'nome': _('Nome da Empresa'),
            'contacto': _('Pessoa de Contacto'),
            'telefone': _('Contacto Telefónico'),
            'email': _('Email'),
            'website': _('Website'),
            'notas': _('Notas')
        }
        help_texts = {
            'telefone': _('Inclua o indicativo internacional, ex: +351'),
            'notas': _('Informações adicionais sobre o fornecedor')
        }


class FornecedorPecaForm(forms.ModelForm):
    """
    Formulário para associações entre fornecedores e peças
    """
    class Meta:
        model = FornecedorPeca
        fields = [
            'fornecedor', 'peca', 'referencia_fornecedor',
            'preco_unitario', 'tempo_entrega', 'fornecedor_preferencial',
            'notas'
        ]
        widgets = {
            'notas': forms.Textarea(attrs={'rows': 2}),
            'tempo_entrega': forms.NumberInput(attrs={'min': 1, 'placeholder': _('Dias úteis')}),
        }
        labels = {
            'referencia_fornecedor': _('Referência do Fornecedor'),
            'preco_unitario': _('Preço Unitário (€)'),
            'tempo_entrega': _('Tempo Médio de Entrega (dias)'),
            'fornecedor_preferencial': _('Fornecedor Preferencial'),
            'notas': _('Notas Adicionais'),
        }
        help_texts = {
            'referencia_fornecedor': _('Código/referência que o fornecedor utiliza para esta peça'),
            'fornecedor_preferencial': _('Marcar este fornecedor como preferencial para esta peça'),
            'tempo_entrega': _('Tempo médio que o fornecedor demora a entregar esta peça')
        }


# ===========================================
# FORMULÁRIOS DE ENCOMENDAS
# ===========================================
class EncomendaPecaForm(forms.ModelForm):
    """
    Formulário para encomendas de peças
    """
    class Meta:
        model = EncomendaPeca
        fields = [
            'fornecedor', 'numero_pedido', 'data_encomenda',
            'prazo_entrega', 'observacoes', 'referencia_interna', 
            'referencia_fornecedor'
        ]
        widgets = {
            'data_encomenda': forms.DateInput(attrs={'type': 'date'}),
            'prazo_entrega': forms.DateInput(attrs={'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'numero_pedido': _('Número de Pedido'),
            'data_encomenda': _('Data da Encomenda'),
            'prazo_entrega': _('Prazo de Entrega'),
            'observacoes': _('Observações'),
            'referencia_interna': _('Referência Interna'),
            'referencia_fornecedor': _('Referência do Fornecedor')
        }
        help_texts = {
            'numero_pedido': _('Número de referência interno para esta encomenda'),
        }


class ItemEncomendaForm(forms.ModelForm):
    """
    Formulário para itens de encomenda
    """
    class Meta:
        model = ItemEncomenda
        fields = [
            'peca', 'quantidade', 'preco_unitario',
            'fornecedor_peca'
        ]
        labels = {
            'peca': _('Peça'),
            'preco_unitario': _('Preço Unitário (€)'),
            'fornecedor_peca': _('Referência do Fornecedor'),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar peças por código
        self.fields['peca'].queryset = Peca.objects.all().order_by('codigo')


# ===========================================
# FORMULÁRIOS DE MOVIMENTAÇÕES DE STOCK
# ===========================================
class MovimentacaoStockForm(forms.ModelForm):
    """
    Formulário para registar movimentações de stock
    """
    class Meta:
        model = MovimentacaoStock
        fields = [
            'peca', 'tipo', 'quantidade', 'motivo',
            'fornecedor', 'fornecedor_peca', 'num_fatura',
            'preco_unitario', 'observacao'
        ]
        widgets = {
            'observacao': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {
            'peca': _('Peça'),
            'tipo': _('Tipo de Movimentação'),
            'motivo': _('Motivo'),
            'num_fatura': _('Número da Fatura'),
            'preco_unitario': _('Preço Unitário (€)'),
            'observacao': _('Observação'),
        }
        help_texts = {
            'tipo': _('Entrada: aumenta o stock. Saída: diminui o stock.'),
            'motivo': _('Razão desta movimentação de stock'),
            'num_fatura': _('Para compras, indique o número da fatura do fornecedor'),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar peças por código
        self.fields['peca'].queryset = Peca.objects.all().order_by('codigo')
        
        # Campo fornecedor_peca inicialmente vazio
        self.fields['fornecedor_peca'].queryset = FornecedorPeca.objects.none()
        
        # Se já existir uma instância e tiver uma peça, carregar os fornecedores dessa peça
        if 'instance' in kwargs and kwargs['instance'] and kwargs['instance'].peca:
            peca = kwargs['instance'].peca
            self.fields['fornecedor_peca'].queryset = FornecedorPeca.objects.filter(
                peca=peca
            ).select_related('fornecedor')


# ===========================================
# FORMSETS
# ===========================================
# Formset para múltiplos itens numa encomenda
ItemEncomendaFormSet = inlineformset_factory(
    EncomendaPeca, 
    ItemEncomenda,
    form=ItemEncomendaForm,
    extra=1,
    can_delete=True
)