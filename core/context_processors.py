# Conteúdo completo para o arquivo core/context_processors.py
from django.urls import reverse
from django.utils.translation import gettext as _

def navigation(request):
    """Fornece dados de navegação para todos os templates."""
    app_name = ""
    url_name = ""
    
    if hasattr(request, 'resolver_match') and request.resolver_match:
        app_name = request.resolver_match.app_name
        url_name = request.resolver_match.url_name
    
    nav_items = []
    
    # Definir itens de navegação para cada aplicação
    if app_name == 'clientes':
        # Se estamos na página de detalhes de um cliente e temos um cliente_id na URL
        if url_name == 'detalhes_cliente' and hasattr(request, 'resolver_match') and request.resolver_match.kwargs.get('cliente_id'):
            cliente_id = request.resolver_match.kwargs.get('cliente_id')
            nav_items = [
                {'title': _('Detalhes'), 'url_name': 'detalhes_cliente', 'url': reverse('clientes:detalhes_cliente', args=[cliente_id]), 'icon': 'info-circle'},
                {'title': _('Contactos'), 'url_name': 'cliente_contactos', 'url': '#contactos-tab', 'icon': 'address-book'},
                {'title': _('Equipamentos'), 'url_name': 'cliente_equipamentos', 'url': '#equipamentos-tab', 'icon': 'tools'},
                {'title': _('Assistências'), 'url_name': 'cliente_assistencias', 'url': '#assistencias-tab', 'icon': 'headset'},
                {'title': _('Notas'), 'url_name': 'cliente_notas', 'url': '#notas-tab', 'icon': 'sticky-note'},
            ]
        else:
            # Em outras páginas de clientes
            nav_items = [
                {'title': _('Listar Clientes'), 'url_name': 'listar_clientes', 'url': reverse('clientes:listar_clientes'), 'icon': 'users'},
                {'title': _('Adicionar Cliente'), 'url_name': 'adicionar_cliente', 'url': reverse('clientes:adicionar_cliente'), 'icon': 'user-plus'},
            ]
        
        return {
            'current_app': app_name,
            'current_url_name': url_name,
            'nav_items': nav_items
        }