from django.db import models
from clientes.models import Cliente
from equipamentos.models import EquipamentoCliente

class PedidoAssistencia(models.Model):
    ESTADOS = [
        ('Recebida', 'Recebida'),
        ('Em Diagnóstico', 'Em Diagnóstico'),
        ('Em Curso', 'Em Curso'),
        ('Concluída', 'Concluída'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="pedidos_assistencia")
    numero_pedido = models.CharField(max_length=50, unique=True)
    equipamento = models.ForeignKey(EquipamentoCliente, on_delete=models.CASCADE, related_name="pedidos_assistencia")
    em_garantia = models.BooleanField(default=False)
    data_entrada = models.DateField()
    data_reparacao = models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Recebida')
    descricao_problema = models.TextField()

    def __str__(self):
        return f"Pedido {self.numero_pedido} - {self.cliente.nome} - {self.estado}"
