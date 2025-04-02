# configuracao/context_processors.py
from .models import ConfiguracaoSistema

def configuracao_sistema(request):
    """
    Adiciona as configurações do sistema ao contexto de todos os templates.
    """
    return {
        'configuracao': ConfiguracaoSistema.get_solo(),
    }