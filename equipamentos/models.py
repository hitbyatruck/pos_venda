from django.db import models
from django.core.exceptions import ValidationError
from clientes.models import EquipamentoCliente
from simple_history.models import HistoricalRecords

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
    history = HistoricalRecords()
    
    def __str__(self):
        return self.nome

    def delete(self, *args, **kwargs):
        """Deletes equipment and all its associations"""
        from clientes.models import EquipamentoCliente
        from assistencia.models import PedidoAssistencia
        
        # Extract and remove 'force' from kwargs before passing to super().delete()
        force = kwargs.pop('force', False)
        
        # Check for associations
        equipamentos_cliente = EquipamentoCliente.objects.filter(equipamento_fabricado=self)
        pats = PedidoAssistencia.objects.filter(equipamento__equipamento_fabricado=self)
        
        if equipamentos_cliente.exists() or pats.exists():
            # Count associations
            num_clientes = equipamentos_cliente.count()
            num_pats = pats.count()
            
            if force:
                # Delete all associations and the equipment
                pats.delete()
                equipamentos_cliente.delete()
                return super().delete(*args, **kwargs)
            else:
                message = (
                    f"Este equipamento possui {num_clientes} associação(ões) com cliente(s) "
                    f"e {num_pats} PAT(s). A exclusão removerá todas estas associações "
                    "e seus respectivos PATs. Esta ação é irreversível."
                )
                raise ValidationError(message)
        else:
            return super().delete(*args, **kwargs)

    def clean(self):
        super().clean()
        
        # Validar nome único (ignorando maiúsculas/minúsculas)
        if self.nome:
            nome_duplicado = EquipamentoFabricado.objects.filter(nome__iexact=self.nome)
            if self.pk:
                nome_duplicado = nome_duplicado.exclude(pk=self.pk)
            if nome_duplicado.exists():
                raise ValidationError({'nome': 'Já existe um equipamento com este nome.'})
        
        # Validar referência única (ignorando maiúsculas/minúsculas)
        if self.referencia_interna:  # Corrigido de referencia para referencia_interna
            ref_duplicada = EquipamentoFabricado.objects.filter(referencia_interna__iexact=self.referencia_interna)
            if self.pk:
                ref_duplicada = ref_duplicada.exclude(pk=self.pk)
            if ref_duplicada.exists():
                raise ValidationError({'referencia_interna': 'Já existe um equipamento com esta referência.'})   

class DocumentoEquipamento(models.Model):
    equipamento = models.ForeignKey(EquipamentoFabricado, on_delete=models.CASCADE, related_name='documentos')
    arquivo = models.FileField(upload_to='equipamentos_documentos/')

    def __str__(self):
        return f"Documento: {self.arquivo.name}"
