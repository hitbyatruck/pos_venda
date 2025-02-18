from django.db import models
from clientes.models import Cliente, EquipamentoCliente

class PedidoAssistencia(models.Model):
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.CASCADE, 
        related_name="pats",
        verbose_name="Cliente"
    )
    pat_number = models.CharField(
        max_length=100, 
        unique=True, 
        null=True,  # Permite migração; no formulário, será obrigatório
        blank=True,
        verbose_name="Número da PAT"
    )
    data_entrada = models.DateField(verbose_name="Data de Entrada")
    ESTADO_CHOICES = [
        ('aberto', 'Aberto'),
        ('em_curso', 'Em Curso'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
        ('em_diagnostico', 'Em Diagnóstico'),
    ]
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='aberto',
        verbose_name="Estado da PAT"
    )
    equipamento = models.ForeignKey(
        EquipamentoCliente, 
        on_delete=models.CASCADE, 
        related_name="pats",
        verbose_name="Equipamento"
    )
    relatorio = models.TextField(blank=True, null=True, verbose_name="Relatório")
    garantia = models.BooleanField(
        default=False,
        verbose_name="Em Garantia",
        help_text="Marque se o equipamento estiver em garantia."
    )
    data_reparacao = models.DateField(blank=True, null=True, verbose_name="Data de Reparação")
  

    def __str__(self):
        return f"PAT {self.pat_number or '---'} - {self.cliente.nome}"

class ItemPat(models.Model):
    TIPO_CHOICES = [
        ('servico', 'Serviço'),
        ('componente', 'Componente'),
    ]
    pat = models.ForeignKey(
        PedidoAssistencia, 
        on_delete=models.CASCADE, 
        related_name="itens",
        verbose_name="PAT"
    )
    tipo = models.CharField(
        max_length=20, 
        choices=TIPO_CHOICES,
        verbose_name="Tipo"
    )
    referencia = models.CharField(max_length=100, verbose_name="Referência")
    designacao = models.CharField(max_length=255, verbose_name="Designação")
    preco = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço")

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.designacao} ({self.referencia})"
