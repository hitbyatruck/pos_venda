from django.db import models
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from clientes.models import Cliente

class ResilienceModelMixin:
    """
    A mixin that makes models more resilient to missing database fields during development.
    This is especially useful when multiple developers are working on a shared codebase.
    """
    def __getattr__(self, name):
        # Handle missing fields gracefully in templates
        if name.startswith('_'):
            # Let Django handle its own private attributes
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

        # Return empty string for unknown fields to avoid template errors
        return ""

    class Meta:
        abstract = True

class CategoriaEquipamento(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    pai = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategorias')
    ativo = models.BooleanField(default=True)
    ordem = models.IntegerField(default=0)  # Add this line
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.pai:
            return f"{self.pai} > {self.nome}"
        return self.nome

    class Meta:
        ordering = ['nome']
        verbose_name = "Categoria de Equipamento"
        verbose_name_plural = "Categorias de Equipamento"

    @property
    def nivel(self):
        """Retorna o nível hierárquico da categoria"""
        level = 0
        parent = self.pai
        while parent:
            level += 1
            parent = parent.pai
        return level

    @property
    def tem_subcategorias(self):
        """Verifica se a categoria possui subcategorias"""
        return self.subcategorias.exists() if hasattr(self, 'subcategorias') else False

    @property
    def caminho_completo(self):
        """Retorna o caminho completo da categoria (ex: Eletrônicos > Áudio > Amplificadores)"""
        if not self.pai:
            return self.nome
        return f"{self.pai.caminho_completo} > {self.nome}"

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
        from assistencia.models import PedidoAssistencia

        # Extract and remove 'force' from kwargs before passing to super().delete()
        force = kwargs.pop('force', False)

        # Check for associations
        equipamentos_cliente = self.cliente_equipamentos.all()
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

class EquipamentoCliente(models.Model):
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.CASCADE, related_name='equipamentos_fabricados')
    equipamento_fabricado = models.ForeignKey(EquipamentoFabricado, on_delete=models.CASCADE, related_name='cliente_equipamentos')
    numero_serie = models.CharField(max_length=100, blank=True, null=True)
    data_aquisicao = models.DateField(blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.equipamento_fabricado.nome} - {self.numero_serie or 'S/N'}"

    def transfer_to_client(self, new_client, reason=None):
        """
        Transfer equipment to a new client and record the change in history
        """
        old_client = self.cliente
        self.cliente = new_client

        # Add change reason for better history tracking
        change_reason = f"Transferred from {old_client.nome} to {new_client.nome}"
        if reason:
            change_reason += f". Reason: {reason}"

        self._change_reason = change_reason
        self.save()

        # Create equipment transfer record
        EquipmentTransferRecord.objects.create(
            equipment=self,
            previous_client=old_client,
            new_client=new_client,
            transfer_date=timezone.now(),
            reason=reason
        )

        return True

class EquipmentTransferRecord(models.Model):
    """Model to track equipment transfers between clients"""
    equipment = models.ForeignKey(
        EquipamentoCliente,
        on_delete=models.CASCADE,
        related_name='transfer_history',
        verbose_name=_('Equipamento')
    )
    previous_client = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        related_name='previous_equipment',
        verbose_name=_('Cliente anterior')
    )
    new_client = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='new_equipment',
        verbose_name=_('Novo cliente')
    )
    transfer_date = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Data de transferência')
    )
    reason = models.TextField(
        blank=True, null=True,
        verbose_name=_('Motivo')
    )

    class Meta:
        verbose_name = _('Registro de transferência')
        verbose_name_plural = _('Registros de transferências')
        ordering = ['-transfer_date']

    def __str__(self):
        return f"{self.equipment} - {self.previous_client} → {self.new_client} ({self.transfer_date})"
