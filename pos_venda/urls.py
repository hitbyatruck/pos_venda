from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.conf.urls.i18n import i18n_patterns
from core.views import dashboard 

# URLs sem prefixo de idioma
urlpatterns = [
    # Adicione as URLs de autenticação aqui!
    path('accounts/', include('django.contrib.auth.urls')),
    
    # URL para mudar idioma
    path('i18n/', include('django.conf.urls.i18n')),
    
    # Rosetta para traduções
    path('rosetta/', include('rosetta.urls')),
    
    path('', dashboard, name='dashboard'),
    # Redirecionamento da página inicial
   
    
    # Outras URLs existentes
    path('notas/', include(('notas.urls', 'notas'), namespace='notas')),
    path('search/', include('search.urls')),
]

# URLs com prefixo de idioma (ex: /en/admin/, /pt/clientes/)
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('clientes/', include('clientes.urls')),
    path('equipamentos/', include('equipamentos.urls')),
    path('assistencia/', include('assistencia.urls')),
    path('stock/', include('stock.urls')),
    prefix_default_language=False,  # Não adicionar prefixo para o idioma padrão
)

# Arquivos de mídia em modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)