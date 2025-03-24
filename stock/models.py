from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from simple_history.models import HistoricalRecords
from equipamentos.models import EquipamentoFabricado

# ==========================================
# MODELOS BASE: FORNECEDORES E CATEGORIAS
# ==========================================

class Fornecedor(models.Model):
    """Modelo para fornecedores de peças"""
    nome = models.CharField(_('Nome'), max_length=100)
    contacto = models.CharField(_('Contacto'), max_length=100, blank=True)
    telefone = models.CharField(_('Telefone'), max_length=20, blank=True)
    email = models.EmailField(_('Email'), blank=True)
    website = models.URLField(_('Website'), blank=True)
    notas = models.TextField(_('Notas'), blank=True)
    data_cadastro = models.DateTimeField(_('Data de cadastro'), auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = _('Fornecedor')
        verbose_name_plural = _('Fornecedores')
        ordering = ['nome']
    
    def count_preferential_pieces(self):
        """Retorna a contagem de peças onde este fornecedor é preferencial"""
        return self.pecas_fornecidas.filter(fornecedor_preferencial=True).count()

    def __str__(self):
        return self.nome


class CategoriaPeca(models.Model):
    """Modelo para categorias de peças"""
    nome = models.CharField(_('Nome'), max_length=100)
    descricao = models.TextField(_('Descrição'), blank=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = _('Categoria de Peça')
        verbose_name_plural = _('Categorias de Peças')
        ordering = ['nome']

    def __str__(self):
        return self.nome


# ==========================================
# MODELOS DE INVENTÁRIO: PEÇAS E COMPONENTES
# ==========================================

class Peca(models.Model):
    """Modelo para peças de substituição"""
    codigo = models.CharField(_('Código Interno'), max_length=50, unique=True)
    nome = models.CharField(_('Nome'), max_length=200)
    descricao = models.TextField(_('Descrição'), blank=True)
    categoria = models.ForeignKey('CategoriaPeca', on_delete=models.SET_NULL, null=True, verbose_name=_('Categoria'))
    stock_minimo = models.PositiveIntegerField(_('Stock Mínimo'), default=0)
    stock_atual = models.PositiveIntegerField(_('Stock Atual'), default=0)
    localizacao = models.CharField(_('Localização'), max_length=100, blank=True)
    unidade = models.CharField(_('Unidade'), max_length=20, default='un')
    # Removido o campo de fornecedores direto, agora é via FornecedorPeca
    preco_custo = models.DecimalField(_('Preço de Custo'), max_digits=10, decimal_places=2, default=0)
    preco_venda = models.DecimalField(_('Preço de Venda'), max_digits=10, decimal_places=2, default=0)
    stock_ideal = models.PositiveIntegerField(_('Stock Ideal'), default=5)
    compativel_com = models.ManyToManyField(EquipamentoFabricado, blank=True, 
                                           verbose_name=_('Compatível com'), related_name='pecas_compativeis')
    data_cadastro = models.DateTimeField(_('Data de cadastro'), auto_now_add=True)
    ultima_atualizacao = models.DateTimeField(_('Última atualização'), auto_now=True)
    imagem = models.ImageField(_('Imagem'), upload_to='pecas/', blank=True, null=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = _('Peça')
        verbose_name_plural = _('Peças')
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    @property
    def status_stock(self):
        """Retorna o status do stock (OK, Baixo, Crítico)"""
        if self.stock_atual <= 0:
            return "esgotado"
        elif self.stock_atual < self.stock_minimo:
            return "critico"
        elif self.stock_atual < self.stock_ideal:
            return "baixo"
        return "ok"
    
    def get_status_class(self):
        """Retorna a classe CSS para o status do stock"""
        status_classes = {
            "esgotado": "danger",
            "critico": "danger",
            "baixo": "warning",
            "ok": "success"
        }
        return status_classes.get(self.status_stock, "secondary")


# ==========================================
# RELACIONAMENTOS E ASSOCIAÇÕES
# ==========================================

class FornecedorPeca(models.Model):
    """Relação entre peças e fornecedores, com informações específicas"""
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.CASCADE, 
                                   verbose_name=_('Fornecedor'), related_name='pecas_fornecidas')
    peca = models.ForeignKey(Peca, on_delete=models.CASCADE, 
                             verbose_name=_('Peça'), related_name='fornecedores')
    referencia_fornecedor = models.CharField(_('Referência do Fornecedor'), max_length=100)
    preco_unitario = models.DecimalField(_('Preço Unitário'), max_digits=10, decimal_places=2)
    tempo_entrega = models.PositiveIntegerField(_('Tempo Médio de Entrega (dias)'), null=True, blank=True)
    preco_ultima_atualizacao = models.DateField(_('Data Última Atualização de Preço'), auto_now=True)
    fornecedor_preferencial = models.BooleanField(_('Fornecedor Preferencial'), default=False)
    notas = models.TextField(_('Notas'), blank=True)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Fornecedor de Peça')
        verbose_name_plural = _('Fornecedores de Peças')
        unique_together = ('fornecedor', 'peca')  # Um fornecedor só pode ter uma entrada por peça

    def __str__(self):
        return f"{self.peca.codigo} - {self.fornecedor.nome} ({self.referencia_fornecedor})"
    
    def save(self, *args, **kwargs):
        # Se este fornecedor for marcado como preferencial, desmarcar outros
        if self.fornecedor_preferencial:
            FornecedorPeca.objects.filter(
                peca=self.peca, 
                fornecedor_preferencial=True
            ).exclude(id=self.id).update(fornecedor_preferencial=False)
        
        super().save(*args, **kwargs)


# ==========================================
# ENCOMENDAS E GESTÃO DE COMPRAS
# ==========================================

class EncomendaPeca(models.Model):
    """Modelo para encomendas de peças"""
    STATUS_CHOICES = [
        ('pendente', _('Pendente')),
        ('encomendada', _('Encomendada')),
        ('parcial', _('Recebida Parcialmente')),
        ('recebida', _('Recebida')),
        ('cancelada', _('Cancelada')),
    ]
    
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.CASCADE, 
                                  verbose_name=_('Fornecedor'), related_name='encomendas')
    data_encomenda = models.DateField(_('Data da Encomenda'), default=timezone.now)
    prazo_entrega = models.DateField(_('Prazo de Entrega'), null=True, blank=True)
    numero_pedido = models.CharField(_('Número do Pedido'), max_length=50, blank=True)
    status = models.CharField(_('Status'), max_length=15, choices=STATUS_CHOICES, default='pendente')
    observacoes = models.TextField(_('Observações'), blank=True)
    utilizador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                               null=True, verbose_name=_('Utilizador'))
    referencia_interna = models.CharField(_('Referência Interna'), max_length=50, blank=True, null=True)
    referencia_fornecedor = models.CharField(_('Referência do Fornecedor'), max_length=50, blank=True, null=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = _('Encomenda de Peça')
        verbose_name_plural = _('Encomendas de Peças')
        ordering = ['-data_encomenda']

    def __str__(self):
        return f"Encomenda #{self.id} - {self.fornecedor}"
    
    def get_status_class(self):
        """Retorna a classe CSS para o status da encomenda"""
        status_classes = {
            "pendente": "warning",
            "encomendada": "info",
            "parcial": "primary",
            "recebida": "success",
            "cancelada": "danger"
        }
        return status_classes.get(self.status, "secondary")
    
    @property
    def valor_total(self):
        """Calcula o valor total da encomenda"""
        return sum(item.subtotal for item in self.itens.all())


class ItemEncomenda(models.Model):
    """Modelo para itens de uma encomenda"""
    encomenda = models.ForeignKey(EncomendaPeca, on_delete=models.CASCADE, 
                                 verbose_name=_('Encomenda'), related_name='itens')
    peca = models.ForeignKey(Peca, on_delete=models.CASCADE, 
                            verbose_name=_('Peça'), related_name='itens_encomenda')
    fornecedor_peca = models.ForeignKey(FornecedorPeca, on_delete=models.SET_NULL,
                                       null=True, blank=True, 
                                       verbose_name=_('Referência do Fornecedor'),
                                       related_name='itens_encomenda')
    quantidade = models.PositiveIntegerField(_('Quantidade'))
    preco_unitario = models.DecimalField(_('Preço Unitário'), max_digits=10, decimal_places=2)
    quantidade_recebida = models.PositiveIntegerField(_('Quantidade Recebida'), default=0)
    history = HistoricalRecords()

    class Meta:
        verbose_name = _('Item de Encomenda')
        verbose_name_plural = _('Itens de Encomenda')
    
    def __str__(self):
        ref_fornecedor = f" ({self.fornecedor_peca.referencia_fornecedor})" if self.fornecedor_peca else ""
        return f"{self.quantidade}x {self.peca.nome}{ref_fornecedor}"
    
    @property
    def subtotal(self):
        """Calcula o subtotal do item"""
        return self.quantidade * self.preco_unitario
    
    @property
    def status(self):
        """Retorna o status do item"""
        if self.quantidade_recebida == 0:
            return "pendente"
        elif self.quantidade_recebida < self.quantidade:
            return "parcial"
        return "completo"
    
    def clean(self):
        """Validações personalizadas"""
        if self.fornecedor_peca and self.fornecedor_peca.peca != self.peca:
            raise ValidationError(_('A referência do fornecedor deve corresponder à peça selecionada.'))
        
        if self.fornecedor_peca and self.fornecedor_peca.fornecedor != self.encomenda.fornecedor:
            raise ValidationError(_('A referência do fornecedor deve ser do mesmo fornecedor da encomenda.'))


# ==========================================
# MOVIMENTAÇÕES DE STOCK
# ==========================================

class MovimentacaoStock(models.Model):
    """Modelo para registar movimentações de stock (entrada/saída)"""
    TIPO_CHOICES = [
        ('entrada', _('Entrada')),
        ('saida', _('Saída')),
    ]
    
    MOTIVO_CHOICES = [
        ('compra', _('Compra')),
        ('devolucao', _('Devolução')),
        ('ajuste', _('Ajuste de Inventário')),
        ('utilizacao', _('Utilização em Reparação')),
        ('transferencia', _('Transferência')),
        ('outro', _('Outro')),
    ]
    
    peca = models.ForeignKey(Peca, on_delete=models.CASCADE, 
                            verbose_name=_('Peça'), related_name='movimentacoes')
    tipo = models.CharField(_('Tipo'), max_length=10, choices=TIPO_CHOICES)
    quantidade = models.PositiveIntegerField(_('Quantidade'))
    motivo = models.CharField(_('Motivo'), max_length=20, choices=MOTIVO_CHOICES)
    pat = models.ForeignKey('assistencia.PedidoAssistencia', on_delete=models.SET_NULL, 
                           null=True, blank=True, verbose_name=_('PAT Relacionado'))
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.SET_NULL, 
                                  null=True, blank=True, verbose_name=_('Fornecedor'))
    fornecedor_peca = models.ForeignKey(FornecedorPeca, on_delete=models.SET_NULL,
                                      null=True, blank=True, verbose_name=_('Referência do Fornecedor'))
    num_fatura = models.CharField(_('Número da Fatura'), max_length=50, blank=True)
    preco_unitario = models.DecimalField(_('Preço Unitário'), max_digits=10, decimal_places=2, 
                                        null=True, blank=True)
    observacao = models.TextField(_('Observação'), blank=True)
    utilizador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                               null=True, verbose_name=_('Utilizador'))
    data_movimentacao = models.DateTimeField(_('Data da Movimentação'), auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = _('Movimentação de Stock')
        verbose_name_plural = _('Movimentações de Stock')
        ordering = ['-data_movimentacao']

    def __str__(self):
        return f"{self.get_tipo_display()} de {self.quantidade} unidades de {self.peca}"
    
    def clean(self):
        """Validações personalizadas para movimentações"""
        # Verificar se há stock suficiente para saídas
        if self.tipo == 'saida' and self.peca.stock_atual < self.quantidade:
            raise ValidationError(_('Stock insuficiente para realizar esta saída.'))
    
    def save(self, *args, **kwargs):
        # Atualizar o stock da peça
        peca = self.peca
        if self.tipo == 'entrada':
            peca.stock_atual += self.quantidade
        elif self.tipo == 'saida':
            peca.stock_atual -= self.quantidade
        
        peca.save()
        super().save(*args, **kwargs)


# ==========================================
# HISTÓRICO DE PREÇOS
# ==========================================

class HistoricoPrecoFornecedor(models.Model):
    """Registra o histórico de preços de peças por fornecedor"""
    fornecedor_peca = models.ForeignKey('FornecedorPeca', on_delete=models.CASCADE, 
                                       related_name='historico_precos')
    preco_unitario = models.DecimalField(_('Preço Unitário'), max_digits=10, decimal_places=2)
    data_registro = models.DateTimeField(_('Data de Registro'), auto_now_add=True)
    
    class Meta:
        ordering = ['-data_registro']
        verbose_name = _('Histórico de Preço')
        verbose_name_plural = _('Históricos de Preços')
    
    def __str__(self):
        return f"{self.fornecedor_peca} - {self.preco_unitario} ({self.data_registro.strftime('%d/%m/%Y')})"