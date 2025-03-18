from django.contrib import admin
from .models import Nota

@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'cliente', 'data_criacao')
    search_fields = ('titulo', 'conteudo')

from .models import Tarefa

@admin.register(Tarefa)
class TarefaAdmin(admin.ModelAdmin):
    list_display = ('id', 'descricao', 'status', 'cliente', 'nota', 'data_criacao')
    list_filter = ('status', 'cliente')
    search_fields = ('descricao',)