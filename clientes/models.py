from django.db import models

# MODELO BASE DE DADOS DO CLIENTE
class Cliente(models.Model):
    nome = models.CharField(max_length=255)
    empresa = models.CharField(max_length=255, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(unique=True)
    endereco = models.TextField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

