from django.db import models
from clientes.models import Cliente

class EquipamentoFabricado(models.Model):
    nome = models.CharField(max_length=255)
    referencia_interna = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    especificacoes = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey('CategoriaEquipamento', on_delete=models.SET_NULL, null=True, blank=True)
    fotografia = models.ImageField(upload_to='equipamentos_fotos/', blank=True, null=True)

    def __str__(self):
        return self.nome

class DocumentoEquipamento(models.Model):
    equipamento = models.ForeignKey(EquipamentoFabricado, on_delete=models.CASCADE, related_name='documentos')
    arquivo = models.FileField(upload_to='equipamentos_documentos/')

    def __str__(self):
        return f"Documento: {self.arquivo.name}"
    
class CategoriaEquipamento(models.Model):
    nome = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.nome