from django.contrib import admin
from .models import PedidoAssistencia, ItemPAT  # Changed ItemPat to ItemPAT

class ItemPatInline(admin.TabularInline):
    model = ItemPAT  # Changed ItemPat to ItemPAT
    extra = 0

# Register the PedidoAssistencia model
@admin.register(PedidoAssistencia)
class PedidoAssistenciaAdmin(admin.ModelAdmin):
    list_display = ['pat_number', 'cliente', 'estado', 'data_entrada', 'tecnico']
    list_filter = ['estado', 'data_entrada', 'tecnico']
    search_fields = ['pat_number', 'cliente__nome', 'numero_serie_equipamento']
    date_hierarchy = 'data_entrada'

# Register the ItemPAT model
@admin.register(ItemPAT)  # Changed ItemPat to ItemPAT
class ItemPATAdmin(admin.ModelAdmin):  # Changed ItemPatAdmin to ItemPATAdmin for consistency
    list_display = ['pat', 'tipo', 'designacao', 'quantidade', 'preco_unitario', 'subtotal']
    list_filter = ['tipo']
    search_fields = ['designacao', 'referencia', 'pat__pat_number']


