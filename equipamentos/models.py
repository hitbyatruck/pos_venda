from django.db import models
from django.core.exceptions import ValidationError
from clientes.models import EquipamentoCliente

class CategoriaEquipamento(models.Model):
    nome = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.nome

class EquipamentoFabricado(models.Model):
    nome = models.CharField(max_length=255)
    referencia_interna = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    especificacoes = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(CategoriaEquipamento, on_delete=models.SET_NULL, null=True, blank=True)
    fotografia = models.ImageField(upload_to='equipamentos_fotos/', blank=True, null=True)

    def __str__(self):
        return self.nome

    def delete(self, *args, **kwargs):
        """ Impede a exclusão se houver relações com clientes ou pedidos de assistência """
        from clientes.models import EquipamentoCliente  # Se necessário, faça a importação local
        if EquipamentoCliente.objects.filter(equipamento_fabricado=self).exists():
            raise ValidationError("Não é possível excluir o equipamento porque está associado a um cliente.")
        super().delete(*args, **kwargs)


class DocumentoEquipamento(models.Model):
    equipamento = models.ForeignKey(EquipamentoFabricado, on_delete=models.CASCADE, related_name='documentos')
    arquivo = models.FileField(upload_to='equipamentos_documentos/')


    def __str__(self):
        return f"Documento: {self.arquivo.name}"


