# notas/models.py
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from clientes.models import Cliente, EquipamentoCliente
from assistencia.models import PedidoAssistencia


STATUS_TAREFA = [
    ('a_fazer', 'A Fazer'),
    ('concluido', 'Concluído'),
]

class Tarefa(models.Model):
    # A tarefa pode ser criada de forma independente ou associada a uma nota.
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='tarefas',
        verbose_name="Cliente"
    )
    pat = models.ForeignKey(
        PedidoAssistencia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tarefas',
        verbose_name="PAT"
    )
    # Se a tarefa for parte de uma nota, este campo será preenchido;
    # para tarefas independentes, ficará em branco.
    nota = models.ForeignKey(
        'Nota',
        on_delete=models.CASCADE,
        related_name='tarefas',
        null=True,
        blank=True,
        verbose_name="Nota"
    )
    descricao = models.TextField(verbose_name="Descrição")
    status = models.CharField(
        max_length=10,
        choices=STATUS_TAREFA,
        default='a_fazer',
        verbose_name="Status"
    )
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")

    def __str__(self):
        return f"Tarefa: {self.descricao[:50]}..."

class Nota(models.Model):
    titulo = models.CharField(max_length=200, verbose_name="Título")
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="notas",
        verbose_name="Cliente"
    )
    pat = models.ForeignKey(
        PedidoAssistencia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notas",
        verbose_name="PAT"
    )
    equipamento = models.ForeignKey(
        EquipamentoCliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notas",
        verbose_name="Equipamento"
    )
    conteudo = models.TextField(verbose_name="Conteúdo")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")

    

    def __str__(self):
        return self.titulo

@receiver(post_save, sender=Nota)
def update_titulo(sender, instance, created, **kwargs):
    if created and (not instance.titulo or instance.titulo.strip() == "Nota de Conversa"):
        instance.titulo = f"Nota de Conversa {instance.id}"
        instance.save(update_fields=["titulo"])
