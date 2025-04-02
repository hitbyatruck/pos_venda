from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from simple_history.models import HistoricalRecords

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

class Cliente(models.Model):
    """Modelo base para todos os clientes (empresas e individuais)"""
    TIPO_CHOICES = (
        ('empresa', _('Empresa')),
        ('individual', _('Individual')),
    )
    
    REGIME_IVA_CHOICES = (
        ('normal', _('Normal')),
        ('isento', _('Isento')),
        ('reduzido', _('Reduzido')),
    )
    
    # Tipo de cliente
    tipo = models.CharField(_("Tipo"), max_length=20, choices=TIPO_CHOICES)
    
    # Informações básicas
    nome = models.CharField(_("Nome"), max_length=200)
    website = models.URLField(_("Website"), blank=True, null=True)
    setor = models.ForeignKey(Setor, on_delete=models.SET_NULL, blank=True, null=True, 
                             verbose_name=_("Setor de Atividade"))
    
    # Archivos (Logo ou Foto)
    imagem = models.ImageField(_("Imagem"), upload_to="clientes/", blank=True, null=True,
                             help_text=_("Logo para empresas ou foto para individuais"))
    
    # Informações fiscais
    nif = models.CharField(_("NIF"), max_length=20, blank=True, null=True)
    regime_iva = models.CharField(_("Regime de IVA"), max_length=20, 
                                 choices=REGIME_IVA_CHOICES, default='normal')
    desconto_padrao = models.DecimalField(_("Desconto Padrão (%)"), 
                                        max_digits=5, decimal_places=2, default=0)
    
    # Endereço
    morada = models.CharField(_("Morada"), max_length=255, blank=True, null=True)
    codigo_postal = models.CharField(_("Código Postal"), max_length=20, blank=True, null=True)
    cidade = models.CharField(_("Cidade"), max_length=100, blank=True, null=True)
    pais = CountryField(_("País"), blank=True, null=True)
    
    # Contacto
    email = models.EmailField(_("Email"), blank=True, null=True)
    telefone = models.CharField(_("Telefone"), max_length=20, blank=True, null=True)
    endereco = models.TextField(_("Endereço"), blank=True, null=True)
    
    # Observações
    observacoes = models.TextField(_("Observações"), blank=True, null=True)
    
    # Metadados
    ativo = models.BooleanField(_("Ativo"), default=True)
    data_criacao = models.DateTimeField(_("Data de Criação"), auto_now_add=True)
    data_atualizacao = models.DateTimeField(_("Última Atualização"), auto_now=True)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _("Cliente")
        verbose_name_plural = _("Clientes")
        ordering = ["nome"]
    
    def __str__(self):
        return self.nome
    
    @property
    def is_empresa(self):
        return self.tipo == 'empresa'
    
    @property
    def is_individual(self):
        return self.tipo == 'individual'

class Empresa(Cliente):
    """Modelo específico para empresas"""
    # Campos específicos de empresas
    nome_comercial = models.CharField(_("Nome Comercial"), max_length=200, blank=True, null=True)
    
    class Meta:
        verbose_name = _("Empresa")
        verbose_name_plural = _("Empresas")

class Individual(Cliente):
    """Modelo específico para clientes individuais"""
    # Campos específicos de indivíduos
    empresa_associada = models.ForeignKey(Empresa, on_delete=models.SET_NULL, blank=True, null=True, 
                                        related_name="colaboradores",
                                        verbose_name=_("Empresa"))
    cargo = models.CharField(_("Cargo"), max_length=100, blank=True, null=True)
    
    class Meta:
        verbose_name = _("Individual")
        verbose_name_plural = _("Individuais")

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

class EquipamentoCliente(models.Model):
    """Associação entre clientes e equipamentos"""
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="equipamentos")
    equipamento_fabricado = models.ForeignKey('equipamentos.EquipamentoFabricado', on_delete=models.CASCADE, 
                                            related_name="clientes_equipamentos")
    numero_serie = models.CharField(_("Número de Série"), max_length=100, blank=True, null=True)
    data_aquisicao = models.DateField(_("Data de Aquisição"), blank=True, null=True)
    data_instalacao = models.DateField(_("Data de Instalação"), blank=True, null=True)
    observacoes = models.TextField(_("Observações"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("Equipamento de Cliente")
        verbose_name_plural = _("Equipamentos de Clientes")
        unique_together = [['cliente', 'equipamento_fabricado', 'numero_serie']]
    
    def __str__(self):
        return f"{self.equipamento_fabricado.nome} - {self.numero_serie or 'S/N'}"

class InteracaoCliente(models.Model):
    """Registra interações com clientes como ligações, emails, reuniões, etc."""
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="interacoes",
                             blank=True, null=True)  # Make nullable initially
    tipo = models.CharField(_("Tipo"), max_length=50, choices=(
        ('ligacao', _('Ligação')),
        ('email', _('Email')),
        ('reuniao', _('Reunião')),
        ('visita', _('Visita')),
        ('outro', _('Outro')),
    ), blank=True, null=True)  # Make nullable initially
    data = models.DateTimeField(_("Data"), auto_now_add=True)
    assunto = models.CharField(_("Assunto"), max_length=200, blank=True, null=True)  # Make nullable initially
    descricao = models.TextField(_("Descrição"), blank=True, null=True)  # Make nullable initially
    responsavel = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, 
                                 related_name="interacoes_cliente", verbose_name=_("Responsável"))
    
    class Meta:
        verbose_name = _("Interação com Cliente")
        verbose_name_plural = _("Interações com Clientes")
        ordering = ["-data"]
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.cliente.nome} ({self.data.strftime('%d/%m/%Y')})"

class TarefaCliente(models.Model):
    """Tarefas associadas a clientes"""
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="tarefas_clientes",
                             blank=True, null=True)  # Make nullable initially
    titulo = models.CharField(_("Título"), max_length=200, blank=True, null=True)  # Make nullable initially
    descricao = models.TextField(_("Descrição"), blank=True, null=True)
    data_criacao = models.DateTimeField(_("Data de Criação"), auto_now_add=True)
    data_limite = models.DateTimeField(_("Data Limite"), blank=True, null=True)
    prioridade = models.CharField(_("Prioridade"), max_length=20, choices=(
        ('baixa', _('Baixa')),
        ('media', _('Média')),
        ('alta', _('Alta')),
        ('urgente', _('Urgente')),
    ), default='media')
    concluida = models.BooleanField(_("Concluída"), default=False)
    responsavel = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, 
                                 related_name="tarefas_cliente", verbose_name=_("Responsável"))
    
    class Meta:
        verbose_name = _("Tarefa de Cliente")
        verbose_name_plural = _("Tarefas de Clientes")
        ordering = ["concluida", "data_limite"]
    
    def __str__(self):
        return f"{self.titulo} - {self.cliente.nome}"