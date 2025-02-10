from django.db import models
from clientes.models import Cliente

class EquipamentoFabricado(models.Model):
    nome = models.CharField(max_length=255)
    referencia_interna = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    especificacoes = models.TextField(blank=True, null=True)
    foto = models.ImageField(upload_to='equipamentos/fotos/', blank=True, null=True)
    categoria = models.ForeignKey(
        'CategoriaEquipamento', 
        on_delete=models.SET_NULL, 
        related_name="equipamentos", 
        null=True, 
        blank=True
    )
    def __str__(self):
        return self.nome

class DocumentoEquipamento(models.Model):
    equipamento = models.ForeignKey(
        EquipamentoFabricado, 
        on_delete=models.CASCADE, 
        related_name="documentos"
    )
    arquivo = models.FileField(upload_to='documentos_equipamento/')

    def __str__(self):
        return self.arquivo.name

class EquipamentoCliente(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='equipamentos')
    equipamento_fabricado = models.ForeignKey(EquipamentoFabricado, on_delete=models.PROTECT)
    numero_serie = models.CharField(max_length=100, unique=True)
    data_aquisicao = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.equipamento_fabricado.nome} - {self.numero_serie} ({self.cliente.nome})"


class CategoriaEquipamento(models.Model):
    nome = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = "Categoria de Equipamento"
        verbose_name_plural = "Categorias de Equipamentos"

    def __str__(self):
        return self.nome