"""
Funções utilitárias para o módulo de Gestão de Stock
"""
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _


def group_required(group_names):
    """
    Decorador que verifica se um utilizador pertence a pelo menos um dos grupos especificados.
    
    Argumentos:
        group_names: Uma lista de nomes de grupos ou um único nome de grupo
    
    Exemplo de uso:
        @group_required(['Administradores', 'Gestores de Stock'])
        def vista_protegida(request):
            # Código da vista aqui
    """
    if isinstance(group_names, str):
        group_names = [group_names]
    
    def check_perms(user):
        if user.is_superuser:
            return True
        
        if not user.is_authenticated:
            return False
            
        # Verificar se o utilizador pertence a pelo menos um dos grupos
        return any(user.groups.filter(name=group_name).exists() for group_name in group_names)
    
    # Personalizar mensagem de erro para quando o acesso é negado
    def permission_denied_message(function):
        def wrapper(request, *args, **kwargs):
            if not check_perms(request.user):
                raise PermissionDenied(_('Não tem permissão para aceder a esta página.'))
            return function(request, *args, **kwargs)
        return wrapper
    
    # Aplicar o decorador
    decorated_view = user_passes_test(check_perms)(permission_denied_message)
    
    return decorated_view


def formato_moeda(valor):
    """
    Formata um valor numérico como moeda (EUR).
    
    Exemplo: 10.5 -> '10,50 €'
    """
    if valor is None:
        return '0,00 €'
    return '{:.2f} €'.format(valor).replace('.', ',')


def incrementar_numero_pedido():
    """
    Gera um número de pedido sequencial para encomendas.
    
    Formato: 'PED-YYYYMMDD-NNN' onde NNN é um contador diário.
    """
    from datetime import datetime
    from .models import EncomendaPeca
    
    hoje = datetime.now().strftime('%Y%m%d')
    prefix = f'PED-{hoje}-'
    
    # Encontrar último número de pedido com este prefixo
    ultimo_pedido = EncomendaPeca.objects.filter(
        numero_pedido__startswith=prefix
    ).order_by('-numero_pedido').first()
    
    if ultimo_pedido:
        try:
            # Obter o número sequencial e incrementar
            ultimo_numero = int(ultimo_pedido.numero_pedido.split('-')[-1])
            return f'{prefix}{(ultimo_numero + 1):03d}'
        except (ValueError, IndexError):
            # Falha ao extrair número, começar novo
            return f'{prefix}001'
    else:
        # Primeiro pedido do dia
        return f'{prefix}001'