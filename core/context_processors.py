# Conteúdo completo para o arquivo core/context_processors.py
from django.urls import reverse
from django.utils.translation import gettext as _

def navigation(request):
    """
    Context processor para adicionar itens de navegação a todas as páginas.
    """
    # Valores padrão caso nada seja definido nos blocos condicionais
    nav_items = []
    url_name = ""
    app_name = ""
    
    # Obtendo o nome da URL e da aplicação atual
    if hasattr(request, 'resolver_match') and request.resolver_match:
        url_name = request.resolver_match.url_name or ""
        app_name = request.resolver_match.app_name or ""
    
    # Definindo a navegação com base na aplicação e URL
    try:
        from django.urls import reverse
        from django.utils.translation import gettext as _
        
        # Menu para aplicação de clientes
        if app_name == 'clientes':
            if url_name in ['detalhes_cliente', 'cliente_contactos', 'cliente_equipamentos', 'cliente_assistencias', 'cliente_notas']:
                # Se estamos em uma página de detalhes de cliente
                if hasattr(request, 'resolver_match') and 'cliente_id' in request.resolver_match.kwargs:
                    cliente_id = request.resolver_match.kwargs['cliente_id']
                    nav_items = [
                        {'title': _('Informações'), 'url_name': 'detalhes_cliente', 'url': reverse('clientes:detalhes_cliente', args=[cliente_id]), 'icon': 'info-circle'},
                        {'title': _('Contactos'), 'url_name': 'cliente_contactos', 'url': reverse('clientes:cliente_contactos', args=[cliente_id]), 'icon': 'address-book'},
                        {'title': _('Equipamentos'), 'url_name': 'cliente_equipamentos', 'url': reverse('clientes:cliente_equipamentos', args=[cliente_id]), 'icon': 'tools'},
                        {'title': _('Assistências'), 'url_name': 'cliente_assistencias', 'url': reverse('clientes:cliente_assistencias', args=[cliente_id]), 'icon': 'headset'},
                        {'title': _('Notas'), 'url_name': 'cliente_notas', 'url': reverse('clientes:cliente_notas', args=[cliente_id]), 'icon': 'sticky-note'},
                    ]
            else:
                # Em outras páginas de clientes
                nav_items = [
                    {'title': _('Listar Clientes'), 'url_name': 'listar_clientes', 'url': reverse('clientes:listar_clientes'), 'icon': 'users'},
                    {'title': _('Adicionar Cliente'), 'url_name': 'adicionar_cliente', 'url': reverse('clientes:adicionar_cliente'), 'icon': 'user-plus'},
                ]
                
        # Menu para aplicação de equipamentos    
        elif app_name == 'equipamentos':
            if url_name == 'detalhes_equipamento':
                if hasattr(request, 'resolver_match') and 'equipamento_id' in request.resolver_match.kwargs:
                    equipamento_id = request.resolver_match.kwargs['equipamento_id']
                    nav_items = [
                        {'title': _('Detalhes'), 'url_name': 'detalhes_equipamento', 'url': reverse('equipamentos:detalhes_equipamento', args=[equipamento_id]), 'icon': 'info-circle'},
                        {'title': _('Editar'), 'url_name': 'editar_equipamento_fabricado', 'url': reverse('equipamentos:editar_equipamento_fabricado', args=[equipamento_id]), 'icon': 'edit'},
                    ]
            else:
                nav_items = [
                    {'title': _('Listar Equipamentos'), 'url_name': 'listar_equipamentos_fabricados', 'url': reverse('equipamentos:listar_equipamentos_fabricados'), 'icon': 'list'},
                    {'title': _('Adicionar Equipamento'), 'url_name': 'adicionar_equipamento_fabricado', 'url': reverse('equipamentos:adicionar_equipamento_fabricado'), 'icon': 'plus-circle'},
                    {'title': _('Listar Categorias'), 'url_name': 'listar_categorias', 'url': reverse('equipamentos:listar_categorias'), 'icon': 'tags'},
                ]
                
        # Menu para aplicação de assistência
        elif app_name == 'assistencia':
            if url_name == 'detalhes_pat':
                if hasattr(request, 'resolver_match') and 'pat_id' in request.resolver_match.kwargs:
                    pat_id = request.resolver_match.kwargs['pat_id']
                    nav_items = [
                        {'title': _('Detalhes'), 'url_name': 'detalhes_pat', 'url': reverse('assistencia:detalhes_pat', args=[pat_id]), 'icon': 'info-circle'},
                        {'title': _('Editar'), 'url_name': 'editar_pat', 'url': reverse('assistencia:editar_pat', args=[pat_id]), 'icon': 'edit'},
                    ]
            else:
                nav_items = [
                    {'title': _('Listar PATs'), 'url_name': 'listar_pats', 'url': reverse('assistencia:listar_pats'), 'icon': 'list'},
                    {'title': _('Criar PAT'), 'url_name': 'criar_pat', 'url': reverse('assistencia:criar_pat'), 'icon': 'plus-circle'},
                ]
                
        # Menu para aplicação de notas
        elif app_name == 'notas':
            nav_items = [
                {'title': _('Listar Notas'), 'url_name': 'listar_notas', 'url': reverse('notas:listar_notas'), 'icon': 'list'},
                {'title': _('Criar Nota'), 'url_name': 'criar_nota', 'url': reverse('notas:criar_nota'), 'icon': 'plus-circle'},
                {'title': _('Tarefas'), 'url_name': 'listar_tarefas', 'url': reverse('notas:listar_tarefas_a_fazer'), 'icon': 'tasks'},
            ]
            
    except Exception as e:
        # Em caso de erro, garantir que temos valores padrão
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro no context processor de navegação: {e}")
        nav_items = []
    
    # Sempre retornar um dicionário, mesmo se ocorrer um erro
    return {
        'nav_items': nav_items,
        'current_url_name': url_name
    }