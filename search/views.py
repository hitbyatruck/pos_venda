from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from core.utils import normalize_text
from django.urls import reverse
from django.db.models import Q, Value as V
from django.db.models.functions import Replace, Lower, Collate
import unicodedata

# Importar todos os modelos relevantes
from clientes.models import Cliente
from equipamentos.models import EquipamentoFabricado, EquipamentoCliente
from assistencia.models import PedidoAssistencia
from notas.models import Tarefa, Nota
from stock.models import Peca

# Import normalize_text function for consistency
def normalize_text(text):
    """
    Normalize text by removing accents and converting to lowercase.
    """
    if not text:
        return ""
    # Normalize unicode characters (remove accents)
    normalized = unicodedata.normalize('NFKD', str(text))
    normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])
    # Convert to lowercase and strip extra spaces
    return normalized.lower().strip()

# These functions are actually used by other apps through imports, so we'll keep and document them
def get_attribute_safely(obj, attr_name, default=""):
    """
    Obtém um atributo de forma segura, retornando um valor padrão se não existir.
    Used by template rendering when accessing potentially missing attributes.
    """
    try:
        value = getattr(obj, attr_name)
        if value is None:
            return default
        if callable(value):
            return value()
        # Se for um objeto relacionado (ForeignKey), tenta obter o nome
        if hasattr(value, 'nome'):
            return value.nome
        return value
    except (AttributeError, TypeError):
        return default

def get_url_safely(view_name, *args, **kwargs):
    """
    Gera um URL de forma segura, retornando uma string vazia se falhar.
    Used in templates and ajax responses when constructing URLs.
    """
    try:
        return reverse(view_name, args=args, kwargs=kwargs)
    except Exception:
        # Fallback para URLs codificados diretamente
        if view_name == 'clientes:detalhes_cliente':
            return f'/clientes/detalhes/{kwargs.get("cliente_id", args[0] if args else "")}'
        elif view_name == 'equipamentos:detalhes_equipamento':
            return f'/equipamentos/{kwargs.get("equipamento_id", args[0] if args else "")}'
        elif view_name == 'equipamentos:historico_equipamento_cliente':
            return f'/equipamentos/cliente/historico/{kwargs.get("equipamento_id", args[0] if args else "")}'
        elif view_name == 'assistencia:detalhes_pat':
            return f'/assistencia/{kwargs.get("pat_id", args[0] if args else "")}'
        elif view_name == 'stock:detalhes_peca':
            return f'/stock/pecas/{kwargs.get("peca_id", args[0] if args else "")}'
        return '#'

def perform_search(query):
    """
    Core search function that can be imported by other apps
    This function is used by both the search view and imported by other apps
    """
    if not query:
        return {}, 0

    normalized_query = normalize_text(query)

    # Results by category
    results = {
        'clientes': [],
        'contactos': [],
        'equipamentos': [],
        'assistencias': [],
        'notas': []
    }

    try:
        # Import models - move inside try block to handle possible import errors
        from clientes.models import Cliente, Contacto
        from equipamentos.models import EquipamentoCliente
        from assistencia.models import PedidoAssistencia
        from notas.models import Nota

        # Search clients
        clientes_results = list(Cliente.objects.filter(nome__icontains=query))

        # Manual accent-insensitive search if needed
        if not clientes_results and normalized_query:
            for cliente in Cliente.objects.all():
                if normalized_query in normalize_text(cliente.nome):
                    clientes_results.append(cliente)

        # Search contacts
        contact_results = list(Contacto.objects.select_related('cliente', 'tipo').filter(
            Q(valor__icontains=query) |
            Q(nome_contacto__icontains=query)
        ))

        # Add clients from contacts
        for contact in contact_results:
            if contact.cliente and contact.cliente not in clientes_results:
                clientes_results.append(contact.cliente)

        results['clientes'] = clientes_results
        results['contactos'] = contact_results

        # Search equipment
        try:
            results['equipamentos'] = list(EquipamentoCliente.objects.select_related('cliente', 'equipamento_fabricado').filter(
                Q(numero_serie__icontains=query)
            ))
        except Exception:
            # Handle possible field errors
            results['equipamentos'] = []

        # Search PATs
        try:
            results['assistencias'] = list(PedidoAssistencia.objects.select_related('cliente').filter(
                Q(pat_number__icontains=query)
            ))
        except Exception:
            results['assistencias'] = []

        # Search notes
        try:
            results['notas'] = list(Nota.objects.select_related('cliente').filter(
                Q(titulo__icontains=query) |
                Q(conteudo__icontains=query)
            ))
        except Exception:
            results['notas'] = []

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Search error: {str(e)}")

    # Calculate total count
    total_count = sum(len(results[key]) for key in results.keys())

    return results, total_count

@login_required
def search_global(request):
    """
    Main search view that renders search results
    This function is the main entry point for the search view
    """
    query = request.GET.get('q', '').strip()

    results = {}
    total_count = 0

    if query:
        results, total_count = perform_search(query)

    # Print debugging for template context
    print(f"Search query: '{query}'")
    print(f"Total count: {total_count}")
    print(f"Clientes: {len(results.get('clientes', []))}")
    print(f"Contactos: {len(results.get('contactos', []))}")

    context = {
        'search_query': query,
        'results': results,
        'total_count': total_count,
        'normalized_query': normalize_text(query) if query else '',
    }

    # Try using the simpler template to troubleshoot the rendering issues
    return render(request, 'search/simple_results.html', context)



