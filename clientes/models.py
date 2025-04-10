from django.db import models
from django.urls import reverse
from django_countries.fields import CountryField
from simple_history.models import HistoricalRecords
from django.utils.translation import gettext_lazy as _

class TipoContacto(models.Model):
    """Tipos de contacto disponíveis"""
    nome = models.CharField(_("Nome"), max_length=50)
    icone = models.CharField(_("Ícone"), max_length=50, blank=True, null=True, 
                           help_text=_("Classe CSS para ícone (ex: fa-envelope)"))
    validador_regex = models.CharField(_("Validador RegEx"), max_length=255, blank=True, null=True,
                                      help_text=_("Expressão regular para validar o valor"))
    ativo = models.BooleanField(_("Ativo"), default=True)
    
    class Meta:
        verbose_name = _("Tipo de Contacto")
        verbose_name_plural = _("Tipos de Contacto")
    
    def __str__(self):
        return self.nome

class Setor(models.Model):
    """
    Modelo para representar setores/segmentos de mercado das empresas.
    """
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    ativo = models.BooleanField(_("Ativo"), default=True)
    data_criacao = models.DateTimeField(_("Data de Criação"), auto_now_add=True)
    data_atualizacao = models.DateTimeField(_("Última Atualização"), auto_now=True)
    
    class Meta:
        verbose_name = "Setor"
        verbose_name_plural = "Setores"
        ordering = ['nome']
    
    def __str__(self):
        return self.nome

class CategoriaCliente(models.Model):
    """Categories for customers (e.g., repair shop, distributor, end user)"""
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nome

class Cliente(models.Model):
    """
    Model for all clients (unified model, no empresa/individual distinction)
    """
    nome = models.CharField(max_length=200)
    imagem = models.ImageField(upload_to='clientes/imagens/', null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    email_principal = models.EmailField(null=True, blank=True)
    
    # Link to business sector
    setor = models.ForeignKey(
        'Setor', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Setor de Atividade"
    )
    
    # Fiscal information
    nif = models.CharField(max_length=20, null=True, blank=True, verbose_name='NIF/VAT')
    percentagem_iva = models.DecimalField(max_digits=5, decimal_places=2, default=23.0)
    desconto = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Desconto padrão em percentagem")
    
    # Fiscal address
    morada = models.CharField(max_length=255, null=True, blank=True)
    codigo_postal = models.CharField(max_length=20, null=True, blank=True)
    cidade = models.CharField(max_length=100, null=True, blank=True)
    pais = CountryField(blank=True, null=True, default='PT')
    
    # Shipping address
    usar_mesma_morada = models.BooleanField(default=True, help_text="Usar a mesma morada para entrega")
    morada_entrega = models.CharField(max_length=255, null=True, blank=True)
    codigo_postal_entrega = models.CharField(max_length=20, null=True, blank=True)
    cidade_entrega = models.CharField(max_length=100, null=True, blank=True)
    pais_entrega = CountryField(blank=True, null=True, default='PT')
    
    # Other fields
    observacoes = models.TextField(null=True, blank=True)
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    # History tracking
    history = HistoricalRecords()
    
    def get_absolute_url(self):
        return reverse('clientes:detalhes_cliente', kwargs={'cliente_id': self.id})
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nome']

class Contacto(models.Model):
    """Contactos associados a clientes"""
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="contactos", 
                               blank=True, null=True)  # Make nullable initially
    tipo = models.ForeignKey(TipoContacto, on_delete=models.CASCADE, verbose_name=_("Tipo"),
                           blank=True, null=True)  # Make nullable initially
    valor = models.CharField(_("Valor"), max_length=255, blank=True, null=True)  # Make nullable initially
    nome_contacto = models.CharField(_("Nome"), max_length=100, blank=True, null=True,
                                   help_text=_("Nome da pessoa de contacto (se aplicável)"))
    cargo = models.CharField(_("Cargo"), max_length=100, blank=True, null=True)
    principal = models.BooleanField(_("Principal"), default=False)
    observacoes = models.TextField(_("Observações"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("Contacto")
        verbose_name_plural = _("Contactos")
        ordering = ["-principal", "tipo", "valor"]
    
    def __str__(self):
        return f"{self.tipo}: {self.valor}"
    
    def save(self, *args, **kwargs):
        # Se este for o contacto principal, desmarcar outros do mesmo tipo
        if self.principal:
            Contacto.objects.filter(
                cliente=self.cliente,
                tipo=self.tipo,
                principal=True
            ).exclude(id=self.id).update(principal=False)
        super().save(*args, **kwargs)