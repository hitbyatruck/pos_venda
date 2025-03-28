from django.db import models
from simple_history.models import HistoricalRecords

class Cliente(models.Model):
    nome = models.CharField(max_length=255)
    empresa = models.CharField(max_length=255, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(unique=True)
    endereco = models.TextField(blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.nome

class EquipamentoCliente(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="equipamentos")
    equipamento_fabricado = models.ForeignKey("equipamentos.EquipamentoFabricado", on_delete=models.CASCADE)
    numero_serie = models.CharField(max_length=100, unique=True, error_messages={
        'unique': "Este número de série já está associado a outro equipamento e/ou cliente."
    })
    data_aquisicao = models.DateField(null=True, blank=True)  # Campo opcional
    history = HistoricalRecords()
    def __str__(self):
        return f"{self.equipamento_fabricado} - {self.numero_serie}"

