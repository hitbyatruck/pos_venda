from django.db import models

class ConfiguracaoSistema(models.Model):
    nome_empresa = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='config/logos/', null=True, blank=True)
    cor_primaria = models.CharField(max_length=7, default='#4e73df', help_text='Código de cor hexadecimal')
    cor_secundaria = models.CharField(max_length=7, default='#1cc88a', help_text='Código de cor hexadecimal')
    tema = models.CharField(max_length=20, default='default', choices=[
        ('default', 'Padrão'),
        ('dark', 'Escuro'),
        ('light', 'Claro'),
    ])
    
    # Configurações específicas do módulo de clientes
    clientes_por_pagina = models.PositiveIntegerField(default=25)
    permitir_cadastro_duplicado = models.BooleanField(default=False)
    
    # Método para garantir que exista apenas uma instância (singleton)
    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    
    def __str__(self):
        return f"Configurações do Sistema: {self.nome_empresa}"
    
    class Meta:
        verbose_name = 'Configuração do Sistema'
        verbose_name_plural = 'Configurações do Sistema'