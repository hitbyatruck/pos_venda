from django.contrib import admin
from .models import EquipamentoFabricado, CategoriaEquipamento, DocumentoEquipamento

@admin.register(CategoriaEquipamento)
class CategoriaEquipamentoAdmin(admin.ModelAdmin):
    list_display = ['nome']
    search_fields = ['nome']



@admin.register(DocumentoEquipamento)
class DocumentoEquipamentoAdmin(admin.ModelAdmin):
    list_display = ['equipamento', 'arquivo']
    list_filter = ['equipamento']

@admin.register(EquipamentoFabricado)
class EquipamentoFabricadoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'referencia_interna', 'categoria']
    search_fields = ['nome', 'referencia_interna']
    list_filter = ['categoria']
    
    # Add inline for documents
    class DocumentoEquipamentoInline(admin.TabularInline):
        model = DocumentoEquipamento
        extra = 1

    inlines = [DocumentoEquipamentoInline]