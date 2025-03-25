from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
from clientes.models import Cliente, EquipamentoCliente
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords
from equipamentos.models import EquipamentoFabricado
import datetime

class PedidoAssistencia(models.Model):
    ESTADO_CHOICES = [
        ('aberto', 'Aberto'),
        ('em_curso', 'Em Curso'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
        ('em_diagnostico', 'Em Diagnóstico'),
    ]

    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.CASCADE, 
        related_name="pats",
        verbose_name="Cliente"
    )
    pat_number = models.CharField(
        max_length=10, 
        unique=True, 
        verbose_name="Número da PAT"
    )
    data_entrada = models.DateField(
        verbose_name="Data de Entrada",
        default=timezone.now
    )
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='aberto',
        verbose_name="Estado da PAT",
        db_index=True  # Indexar para melhor performance em filtros
    )
    equipamento = models.ForeignKey(
        EquipamentoCliente, 
        on_delete=models.CASCADE, 
        related_name="pats",
        verbose_name="Equipamento"
    )
    relatorio = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Relatório"
    )
    garantia = models.BooleanField(
        default=False,
        verbose_name="Em Garantia",
        help_text="Marque se o equipamento estiver em garantia."
    )
    data_reparacao = models.DateField(
        blank=True, 
        null=True, 
        verbose_name="Data de Reparação"
    )
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Atualização"
    )
    history = HistoricalRecords()
    class Meta:
        verbose_name = "Pedido de Assistência Técnica"
        verbose_name_plural = "Pedidos de Assistência Técnica"
        ordering = ['-data_entrada', 'estado']
        indexes = [
            models.Index(fields=['estado', 'data_entrada']),
            models.Index(fields=['cliente', 'estado']),
        ]

    def __str__(self):
        return f"PAT {self.pat_number or '---'} - {self.cliente.nome}"

    def save(self, *args, **kwargs):
        if not self.pat_number:
            self.pat_number = self._generate_pat_number()
        super().save(*args, **kwargs)

    def get_estado_class(self):
        """Retorna a classe Bootstrap adequada para o estado"""
        estado_classes = {
            'aberto': 'warning',
            'em_andamento': 'info',
            'concluido': 'success',
            'cancelado': 'danger'
        }
        return estado_classes.get(self.estado, 'secondary')

    def _generate_pat_number(self):
        """Gera um número único para a PAT no formato YYYYMMXXXX"""
        today = datetime.date.today()
        year = today.year
        month = today.month
        
        # Encontra o último número usado este mês
        last_pat = PedidoAssistencia.objects.filter(
            pat_number__startswith=f"{year}{month:02d}"
        ).order_by('-pat_number').first()

        if last_pat:
            last_number = int(last_pat.pat_number[-4:])
            new_number = last_number + 1
        else:
            new_number = 1

        return f"{year}{month:02d}{new_number:04d}"

    def clean(self):
        """Validações personalizadas"""
        
        if self.pat_number:
            # Verificar se já existe um número PAT igual na base de dados
            # excluindo o atual objeto sendo editado
            existing = PedidoAssistencia.objects.filter(
                pat_number=self.pat_number
            ).exclude(pk=self.pk).exists()
            
            if existing:
                raise ValidationError({
                    'pat_number': ('Este número de PAT já existe. Por favor, escolha outro número.')
                })

        if self.estado == 'concluido' and not self.data_reparacao:
            raise ValidationError({
                'data_reparacao': 'Data de reparação é obrigatória para PATs concluídas.'
            })
        
        if self.data_reparacao and self.data_reparacao < self.data_entrada:
            raise ValidationError({
                'data_reparacao': 'Data de reparação não pode ser anterior à data de entrada.'
            })
        super().clean()

    @property
    def dias_em_aberto(self):
        """Retorna o número de dias que a PAT está em aberto"""
        if self.estado in ['concluido', 'cancelado']:
            return (self.data_reparacao - self.data_entrada).days
        return (timezone.now().date() - self.data_entrada).days

    @property
    def total(self):
        """Retorna o valor total da PAT"""
        return sum(item.total for item in self.itens.all())
    
class ItemPat(models.Model):
    TIPO_CHOICES = [
        ('servico', 'Serviço'),
        ('componente', 'Componente'),
    ]
    
    pat = models.ForeignKey(
        'PedidoAssistencia', 
        on_delete=models.CASCADE, 
        related_name="itens",
        verbose_name="PAT"
    )
    tipo = models.CharField(
        max_length=20, 
        choices=TIPO_CHOICES,
        verbose_name="Tipo",
        db_index=True
    )
    referencia = models.CharField(
        max_length=100, 
        verbose_name="Referência",
        help_text="Código de referência do serviço ou componente"
    )
    designacao = models.CharField(
        max_length=255, 
        verbose_name="Designação",
        help_text="Descrição do serviço ou componente"
    )
    quantidade = models.PositiveIntegerField(
        default=1, 
        verbose_name="Quantidade",
        validators=[MinValueValidator(1)],
        help_text="Quantidade mínima é 1"
    )
    preco = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Preço",
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Preço unitário em euros"
    )
    data_entrada = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Atualização"
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Item de PAT"
        verbose_name_plural = "Itens de PAT"
        ordering = ['tipo', 'designacao']
        indexes = [
            models.Index(fields=['pat', 'tipo']),
            models.Index(fields=['referencia']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantidade__gt=0),
                name='quantidade_positiva'
            ),
            models.CheckConstraint(
                check=models.Q(preco__gte=0),
                name='preco_nao_negativo'
            )
        ]
        

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.designacao} ({self.referencia})"

    def clean(self):
        # For completely empty rows, return without validation
        if self.tipo is None and not self.referencia and not self.designacao:
            # Set defaults for numeric fields to avoid comparison errors
            if self.quantidade is None:
                self.quantidade = 1
            if self.preco is None:
                self.preco = 0
            return
        
        # Otherwise validate normally    
        if self.preco is not None and self.preco < 0:
            raise ValidationError("O preço não pode ser negativo.")
            
        if self.quantidade is not None and self.quantidade <= 0:
            raise ValidationError("A quantidade deve ser maior que zero.")

    @property
    def total(self):
        if self.quantidade is None or self.preco is None:
            return Decimal('0.00')
        return Decimal(str(self.quantidade)) * self.preco

    @property
    def is_servico(self):
        """Verifica se o item é um serviço"""
        return self.tipo == 'servico'

    @property
    def is_componente(self):
        """Verifica se o item é um componente"""
        return self.tipo == 'componente'

class HistoricoPAT(models.Model):
    pat = models.ForeignKey('PedidoAssistencia', on_delete=models.CASCADE, related_name='historico')
    data_registo = models.DateTimeField(auto_now_add=True, verbose_name="Data de Registo")
    utilizador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    estado_anterior = models.CharField(max_length=50, blank=True, null=True, verbose_name="Estado Anterior")
    estado_novo = models.CharField(max_length=50, verbose_name="Estado Novo")
    comentario = models.TextField(blank=True, null=True, verbose_name="Comentário")

    def __str__(self):
        return f"Alteração em PAT #{self.pat.numero} - {self.data_registo.strftime('%d/%m/%Y %H:%M')}"
    
    class Meta:
        verbose_name = "Histórico de PAT"
        verbose_name_plural = "Históricos de PAT"