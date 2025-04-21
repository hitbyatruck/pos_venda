from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
from clientes.models import Cliente
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords
from equipamentos.models import EquipamentoFabricado, EquipamentoCliente
import datetime
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

class PedidoAssistencia(models.Model):
    STATUS_CHOICES = [
        ('aberto', _('Aberto')),
        ('em_diagnostico', _('Em Diagnóstico')),
        ('em_andamento', _('Em Andamento')),
        ('aguardando_peca', _('Aguardando Peça')),
        ('aguardando_cliente', _('Aguardando Cliente')),
        ('concluido', _('Concluído')),
        ('cancelado', _('Cancelado')),
    ]

    pat_number = models.CharField(_('Número PAT'), max_length=50, unique=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='pats')
    equipamento = models.ForeignKey(EquipamentoCliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='pats')
    numero_serie_equipamento = models.CharField(_('Número de Série do Equipamento'), max_length=100, blank=True, null=True)

    data_entrada = models.DateField(_('Data de Entrada'), default=timezone.now)
    data_criacao = models.DateTimeField(_('Data de Criação'), auto_now_add=True)
    data_atualizacao = models.DateTimeField(_('Data de Atualização'), auto_now=True)  # Add this field back
    data_conclusao = models.DateField(_('Data de Conclusão'), null=True, blank=True)

    estado = models.CharField(_('Estado'), max_length=50, choices=STATUS_CHOICES, default='aberto')
    tecnico = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='pats_atribuidas')

    descricao_problema = models.TextField(_('Descrição do Problema'))
    relatorio = models.TextField(_('Relatório Técnico'), blank=True, null=True)  # Make sure this is nullable

    # Add the history field
    history = HistoricalRecords()

    def __str__(self):
        return f"PAT #{self.pat_number}"

    def save(self, *args, **kwargs):
        # Auto-set conclusion date when status is set to 'concluido'
        if self.estado == 'concluido' and not self.data_conclusao:
            from django.utils import timezone
            self.data_conclusao = timezone.now().date()

        # Clear conclusion date when status is not 'concluido'
        if self.estado != 'concluido':
            self.data_conclusao = None

        # Debug logging for important saving actions
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Saving PAT {self.pat_number}: estado={self.estado}, cliente={self.cliente}, equipamento={self.equipamento}")

        # Check for missing required fields and handle gracefully
        if not self.pat_number:
            from datetime import datetime
            prefix = f"PAT-{datetime.now().strftime('%Y%m%d')}"
            count = PedidoAssistencia.objects.filter(pat_number__startswith=prefix).count()
            self.pat_number = f"{prefix}-{count+1:03d}"
            logger.warning(f"Auto-generating missing PAT number: {self.pat_number}")

        super().save(*args, **kwargs)

    # Add a method to record status changes with comments
    def change_status(self, new_status, observations=None):
        """
        Change status and record history with observations
        """
        self.estado = new_status
        if observations:
            self.observacoes_tecnico = f"{self.observacoes_tecnico or ''}\n\n[{timezone.now().strftime('%d/%m/%Y %H:%M')}] {observations}"

        # Add change reason for better history tracking
        self._change_reason = f"Status changed to {dict(self.STATUS_CHOICES).get(new_status)}"
        self.save()

        # Record in status history
        StatusHistory.objects.create(
            pat=self,
            estado=new_status,
            data_alteracao=timezone.now(),
            observacoes=observations
        )

        return True

    @property
    def total_items(self):
        """Calculate the total sum of all line items"""
        return sum(item.subtotal for item in self.itens.all())

    class Meta:
        verbose_name = _('Pedido de Assistência Técnica')
        verbose_name_plural = _('Pedidos de Assistência Técnica')
        ordering = ['-data_criacao']


class ItemPAT(models.Model):
    """
    Representa um item (peça ou serviço) associado a um pedido de assistência técnica.
    """
    TIPO_CHOICES = (
        ('peca', 'Peça'),
        ('servico', 'Serviço'),
        ('componente', 'Componente'),
        ('outro', 'Outro'),
    )

    pat = models.ForeignKey(PedidoAssistencia, on_delete=models.CASCADE, related_name='itens')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='peca')
    referencia = models.CharField(max_length=100, blank=True, null=True)
    designacao = models.CharField(max_length=255)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Item PAT"
        verbose_name_plural = "Itens PAT"

    def __str__(self):
        return f"{self.designacao} ({self.get_tipo_display()})"

    @property
    def subtotal(self):
        return self.quantidade * self.preco_unitario


class HistoricoPAT(models.Model):
    TIPO_CHOICES = [
        ('status', _('Mudança de Status')),
        ('note', _('Observação')),
        ('item', _('Item Adicionado/Removido')),
    ]

    pat = models.ForeignKey(PedidoAssistencia, on_delete=models.CASCADE, related_name='historico')
    tipo = models.CharField(_('Tipo'), max_length=20, choices=TIPO_CHOICES)
    descricao = models.TextField(_('Descrição'))
    data_registo = models.DateTimeField(_('Data de Registo'), auto_now_add=True)
    usuario = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.get_tipo_display()} em {self.data_registo.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        verbose_name = _('Histórico de PAT')
        verbose_name_plural = _('Históricos de PAT')
        ordering = ['-data_registo']


class StatusHistory(models.Model):
    """Model to track status changes for PATs"""
    pat = models.ForeignKey(
        PedidoAssistencia,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    estado = models.CharField(
        max_length=30,
        choices=PedidoAssistencia.STATUS_CHOICES,
        verbose_name=_('Estado')
    )
    data_alteracao = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Data de alteração')
    )
    observacoes = models.TextField(
        blank=True, null=True,
        verbose_name=_('Observações')
    )

    class Meta:
        verbose_name = _('Histórico de Status')
        verbose_name_plural = _('Históricos de Status')
        ordering = ['-data_alteracao']

    def __str__(self):
        return f"{self.pat.pat_number} - {self.get_estado_display()} ({self.data_alteracao})"

    def get_estado_display(self):
        return dict(PedidoAssistencia.STATUS_CHOICES).get(self.estado, self.estado)