from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group

# Desregistrar modelos padrão antes de registrá-los novamente
admin.site.unregister(Group)  # Adicione esta linha para desregistrar Group primeiro
admin.site.register(Group)    # Agora podemos registrá-lo

# Personalizar a exibição de usuários
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'display_groups')
    list_filter = ('is_staff', 'is_superuser', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    def display_groups(self, obj):
        return ", ".join([group.name for group in obj.groups.all()])
    display_groups.short_description = 'Grupos'

# Desregistrar o admin padrão e registrar o personalizado
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)