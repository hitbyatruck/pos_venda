import logging
import unicodedata
from functools import wraps
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.shortcuts import redirect
from django.conf import settings
from django.utils.translation import gettext as _
from django.http import HttpResponseForbidden

logger = logging.getLogger(__name__)

def normalize_text(text):
    """
    Normalize text for search purposes:
    - Convert to string if not already
    - Convert to lowercase
    - Remove accents and diacritics
    - Remove multiple spaces
    """
    if not text:
        return ""
        
    # Convert to string if not already
    if not isinstance(text, str):
        text = str(text)
        
    # Lowercase
    text = text.lower()
    
    # Remove accents and diacritics
    normalized = unicodedata.normalize('NFKD', text)
    normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])
    
    # Remove extra spaces
    normalized = ' '.join(normalized.split())
    
    return normalized


def group_required(group_names):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            # Log informações para depuração
            logger.debug(f"Verificando permissões para {request.user} em {request.path}")
            
            if not request.user.is_authenticated:
                logger.warning(f"Usuário não autenticado tentando acessar {request.path}")
                return redirect(settings.LOGIN_URL)
            
            # Para administradores, sempre permitir acesso
            if request.user.is_superuser:
                logger.debug(f"Superuser {request.user} - acesso concedido")
                return view_func(request, *args, **kwargs)
                
            # Verificar grupos do usuário
            user_groups = [group.name for group in request.user.groups.all()]
            logger.debug(f"Grupos do usuário: {user_groups}")
            
            if any(group in group_names for group in user_groups):
                logger.debug(f"Acesso concedido para {request.user}")
                return view_func(request, *args, **kwargs)
            else:
                logger.warning(f"Acesso negado para {request.user} - grupos insuficientes")
                messages.error(request, 
                    f"Você não tem permissão para acessar esta página. Requer um dos grupos: {', '.join(group_names)}")
                return redirect('/')
                
        return _wrapped_view
    return decorator