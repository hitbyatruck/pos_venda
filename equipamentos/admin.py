from django.contrib import admin
from .models import EquipamentoFabricado
from clientes.models import EquipamentoCliente

admin.site.register(EquipamentoFabricado)
admin.site.register(EquipamentoCliente)