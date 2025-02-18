from django.contrib import admin
from .models import PedidoAssistencia, ItemPat

class ItemPatInline(admin.TabularInline):
    model = ItemPat
    extra = 0

@admin.register(PedidoAssistencia)
class PedidoAssistenciaAdmin(admin.ModelAdmin):
    list_display = ('pat_number', 'cliente', 'data_entrada', 'estado')
    inlines = [ItemPatInline]

admin.site.register(ItemPat)


