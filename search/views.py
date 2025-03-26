from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from core.utils import normalize_text
from django.urls import reverse

# Importar todos os modelos relevantes
from clientes.models import Cliente
from equipamentos.models import EquipamentoFabricado, EquipamentoCliente
from assistencia.models import PedidoAssistencia
from notas.models import Tarefa, Nota
from stock.models import Peca

def get_attribute_safely(obj, attr_name, default=""):
    """Obtém um atributo de forma segura, retornando um valor padrão se não existir."""
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
    """Gera um URL de forma segura, retornando uma string vazia se falhar."""
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

@login_required
def search_global(request):
    query = request.GET.get('q', '').strip()
    
    if not query:
        return render(request, 'search/results.html', {
            'query': '',
            'results': {},
            'total_results': 0
        })
    
    # Normalizar a busca
    normalized_query = normalize_text(query)
    
    # Resultados por categoria
    results = {
        'clientes': [],
        'equipamentos_fabricados': [],
        'equipamentos_cliente': [],
        'pats': [],
        'tarefas': [],
        'pecas': []
    }
    
    # IDs de entidades já incluídas para evitar duplicação
    included_ids = {
        'cliente': set(),
        'equipamento_fabricado': set(),
        'equipamento_cliente': set(),
        'pat': set(),
        'tarefa': set(),
        'peca': set()
    }
    
    # PASSO 1: Buscar clientes que correspondem diretamente ao termo
    clientes_encontrados = []
    clientes = Cliente.objects.all().prefetch_related('equipamentos', 'pats')
    
    for cliente in clientes:
        # Verificar campos principais
        match_found = False
        for field in ['nome', 'nif', 'email', 'telefone', 'empresa']:
            value = get_attribute_safely(cliente, field)
            if value and normalized_query in normalize_text(str(value)):
                match_found = True
                break
                
        if match_found and cliente.id not in included_ids['cliente']:
            included_ids['cliente'].add(cliente.id)
            
            # Construir lista de itens relacionados
            related_items = []
            
            # Adicionar equipamentos do cliente
            for equip in cliente.equipamentos.all():
                related_items.append({
                    'title': f"{get_attribute_safely(equip.equipamento_fabricado, 'nome')} ({equip.numero_serie})",
                    'url': get_url_safely('equipamentos:historico_equipamento_cliente', equipamento_id=equip.id),
                    'icon': 'bi-cpu'
                })
                
                # Incluir este equipamento nos resultados também
                if equip.id not in included_ids['equipamento_cliente']:
                    included_ids['equipamento_cliente'].add(equip.id)
                    results['equipamentos_cliente'].append({
                        'obj': equip,
                        'title': f"{get_attribute_safely(equip.equipamento_fabricado, 'nome')} - {equip.numero_serie}",
                        'subtitle': f"Cliente: {cliente.nome}",
                        'url': get_url_safely('equipamentos:historico_equipamento_cliente', equipamento_id=equip.id),
                        'icon': 'bi-cpu',
                        'related_items': [{
                            'title': f"Cliente: {cliente.nome}",
                            'url': get_url_safely('clientes:detalhes_cliente', cliente_id=cliente.id),
                            'icon': 'bi-person'
                        }]
                    })
            
            # Adicionar PATs do cliente
            for pat in cliente.pats.all():
                related_items.append({
                    'title': f"PAT #{pat.pat_number}",
                    'url': get_url_safely('assistencia:detalhes_pat', pat_id=pat.id),
                    'icon': 'bi-tools'
                })
                
                # Incluir esta PAT nos resultados também
                if pat.id not in included_ids['pat']:
                    included_ids['pat'].add(pat.id)
                    estado_display = getattr(pat, 'get_estado_display', lambda: 'N/A')
                    results['pats'].append({
                        'obj': pat,
                        'title': f"PAT #{pat.pat_number}",
                        'subtitle': f"Cliente: {cliente.nome} - {estado_display()}",
                        'url': get_url_safely('assistencia:detalhes_pat', pat_id=pat.id),
                        'icon': 'bi-tools',
                        'related_items': [{
                            'title': f"Cliente: {cliente.nome}",
                            'url': get_url_safely('clientes:detalhes_cliente', cliente_id=cliente.id),
                            'icon': 'bi-person'
                        }]
                    })
            
            # Adicionar cliente aos resultados
            results['clientes'].append({
                'obj': cliente,
                'title': cliente.nome,
                'subtitle': cliente.empresa or 'Cliente Individual',
                'url': get_url_safely('clientes:detalhes_cliente', cliente_id=cliente.id),
                'icon': 'bi-person',
                'related_items': related_items
            })
            
            # Manter na lista para uso posterior
            clientes_encontrados.append(cliente)
    
    # PASSO 2: Buscar equipamentos fabricados diretamente
    equipamentos = EquipamentoFabricado.objects.all().select_related('categoria')    
    
    for equip in equipamentos:
        # Verificar campos principais
        match_found = False
        for field in ['nome', 'referencia_interna', 'descricao', 'especificacoes']:
            value = get_attribute_safely(equip, field)
            if value and normalized_query in normalize_text(str(value)):
                match_found = True
                break
                
        if match_found and equip.id not in included_ids['equipamento_fabricado']:
            included_ids['equipamento_fabricado'].add(equip.id)
            
            # Construir lista de itens relacionados
            related_items = []
            
            # Adicionar instâncias deste equipamento (equipamentos de clientes)
            for eq_cliente in equip.equipamentocliente_set.all().select_related('cliente'):
                if eq_cliente.id not in included_ids['equipamento_cliente']:
                    included_ids['equipamento_cliente'].add(eq_cliente.id)
                    
                    # Adicionar aos relacionamentos
                    related_items.append({
                        'title': f"Nº série: {eq_cliente.numero_serie} ({get_attribute_safely(eq_cliente.cliente, 'nome')})",
                        'url': f'/equipamentos/cliente/detalhe/{eq_cliente.id}/',
                        'icon': 'bi-cpu'
                    })
                    
                    # Adicionar aos resultados
                    results['equipamentos_cliente'].append({
                        'obj': eq_cliente,
                        'title': f"{equip.nome} - {eq_cliente.numero_serie}",
                        'subtitle': f"Cliente: {get_attribute_safely(eq_cliente.cliente, 'nome')}",
                        'url': f'/equipamentos/cliente/detalhe/{eq_cliente.id}/',
                        'icon': 'bi-cpu',
                        'related_items': [{
                            'title': f"Modelo: {equip.nome}",
                            'url': get_url_safely('equipamentos:detalhes_equipamento', equipamento_id=equip.id),
                            'icon': 'bi-motherboard'
                        }]
                    })
            
            # Adicionar equipamento aos resultados
            categoria_nome = get_attribute_safely(equip.categoria, 'nome', 'N/A')
            results['equipamentos_fabricados'].append({
                'obj': equip,
                'title': equip.nome,
                'subtitle': f"Categoria: {categoria_nome} | Ref: {equip.referencia_interna or 'N/A'}",
                'url': get_url_safely('equipamentos:detalhes_equipamento', equipamento_id=equip.id),
                'icon': 'bi-motherboard',
                'related_items': related_items
            })
    
    # PASSO 3: Buscar números de série de equipamentos
    equip_clientes = EquipamentoCliente.objects.select_related(
        'cliente', 'equipamento_fabricado'
    ).all()
    
    for equip in equip_clientes:
        # Verificar número de série - campo observacoes removido pois não existe
        if (equip.numero_serie and normalized_query in normalize_text(equip.numero_serie)) and \
           equip.id not in included_ids['equipamento_cliente']:
            
            included_ids['equipamento_cliente'].add(equip.id)
            
            # Construir lista de itens relacionados
            related_items = []
            
            # Adicionar cliente relacionado
            cliente = equip.cliente
            if cliente and cliente.id not in included_ids['cliente']:
                included_ids['cliente'].add(cliente.id)
                
                # Adicionar aos relacionamentos
                related_items.append({
                    'title': f"Cliente: {cliente.nome}",
                    'url': get_url_safely('clientes:detalhes_cliente', cliente_id=cliente.id),
                    'icon': 'bi-person'
                })
                
                # Adicionar aos resultados
                cliente_related_items = [{
                    'title': f"{get_attribute_safely(equip.equipamento_fabricado, 'nome')} ({equip.numero_serie})",
                    'url': get_url_safely('equipamentos:historico_equipamento_cliente', equipamento_id=equip.id),
                    'icon': 'bi-cpu'
                }]
                
                results['clientes'].append({
                    'obj': cliente,
                    'title': cliente.nome,
                    'subtitle': cliente.empresa or 'Cliente Individual',
                    'url': get_url_safely('clientes:detalhes_cliente', cliente_id=cliente.id),
                    'icon': 'bi-person',
                    'related_items': cliente_related_items
                })
            
            # Adicionar modelo relacionado
            modelo = equip.equipamento_fabricado
            if modelo and modelo.id not in included_ids['equipamento_fabricado']:
                included_ids['equipamento_fabricado'].add(modelo.id)
                
                # Adicionar aos relacionamentos
                related_items.append({
                    'title': f"Modelo: {modelo.nome}",
                    'url': get_url_safely('equipamentos:detalhes_equipamento', equipamento_id=modelo.id),
                    'icon': 'bi-motherboard'
                })
                
                # Adicionar aos resultados
                categoria_nome = get_attribute_safely(modelo.categoria, 'nome', 'N/A')
                modelo_related_items = [{
                    'title': f"Nº série: {equip.numero_serie} ({get_attribute_safely(equip.cliente, 'nome')})",
                    'url': get_url_safely('equipamentos:historico_equipamento_cliente', equipamento_id=equip.id),
                    'icon': 'bi-cpu'
                }]
                
                results['equipamentos_fabricados'].append({
                    'obj': modelo,
                    'title': modelo.nome,
                    'subtitle': f"Categoria: {categoria_nome} | Ref: {modelo.referencia_interna or 'N/A'}",
                    'url': get_url_safely('equipamentos:detalhes_equipamento', equipamento_id=modelo.id),
                    'icon': 'bi-motherboard',
                    'related_items': modelo_related_items
                })
            
            # Buscar PATs relacionadas a este equipamento
            try:
                pats_relacionadas = PedidoAssistencia.objects.filter(equipamento=equip)
                for pat in pats_relacionadas:
                    if pat.id not in included_ids['pat']:
                        included_ids['pat'].add(pat.id)
                        
                        # Adicionar aos relacionamentos
                        related_items.append({
                            'title': f"PAT #{pat.pat_number}",
                            'url': get_url_safely('assistencia:detalhes_pat', pat_id=pat.id),
                            'icon': 'bi-tools'
                        })
                        
                        # Adicionar aos resultados
                        estado_display = getattr(pat, 'get_estado_display', lambda: 'N/A')
                        pat_related_items = [{
                            'title': f"{get_attribute_safely(equip.equipamento_fabricado, 'nome')} ({equip.numero_serie})",
                            'url': get_url_safely('equipamentos:historico_equipamento_cliente', equipamento_id=equip.id),
                            'icon': 'bi-cpu'
                        }]
                        
                        results['pats'].append({
                            'obj': pat,
                            'title': f"PAT #{pat.pat_number}",
                            'subtitle': f"Cliente: {get_attribute_safely(pat.cliente, 'nome')} - {estado_display()}",
                            'url': get_url_safely('assistencia:detalhes_pat', pat_id=pat.id),
                            'icon': 'bi-tools',
                            'related_items': pat_related_items
                        })
            except Exception as e:
                # Melhor tratamento de exceção para debugging
                print(f"Erro ao buscar PATs para equipamento {equip.id}: {str(e)}")
                pass
            
            # Adicionar equipamento aos resultados
            results['equipamentos_cliente'].append({
                'obj': equip,
                'title': f"{get_attribute_safely(equip.equipamento_fabricado, 'nome')} - {equip.numero_serie}",
                'subtitle': f"Cliente: {get_attribute_safely(equip.cliente, 'nome')}",
                'url': get_url_safely('equipamentos:historico_equipamento_cliente', equipamento_id=equip.id),
                'icon': 'bi-cpu',
                'related_items': related_items
            })
    
    # PASSO 4: Buscar PATs
    pats = PedidoAssistencia.objects.select_related('cliente', 'equipamento').all()
    
    for pat in pats:
        # Verificar número PAT ou relatorio
        if ((pat.pat_number and normalized_query in normalize_text(pat.pat_number)) or
           (pat.relatorio and normalized_query in normalize_text(pat.relatorio))) and \
           pat.id not in included_ids['pat']:
            
            included_ids['pat'].add(pat.id)
            
            # Construir lista de itens relacionados
            related_items = []
            
            # Adicionar cliente relacionado
            cliente = pat.cliente
            if cliente and cliente.id not in included_ids['cliente']:
                included_ids['cliente'].add(cliente.id)
                
                # Adicionar aos relacionamentos
                related_items.append({
                    'title': f"Cliente: {cliente.nome}",
                    'url': get_url_safely('clientes:detalhes_cliente', cliente_id=cliente.id),
                    'icon': 'bi-person'
                })
                
                # Adicionar aos resultados
                cliente_related_items = [{
                    'title': f"PAT #{pat.pat_number}",
                    'url': get_url_safely('assistencia:detalhes_pat', pat_id=pat.id),
                    'icon': 'bi-tools'
                }]
                
                results['clientes'].append({
                    'obj': cliente,
                    'title': cliente.nome,
                    'subtitle': cliente.empresa or 'Cliente Individual',
                    'url': get_url_safely('clientes:detalhes_cliente', cliente_id=cliente.id),
                    'icon': 'bi-person',
                    'related_items': cliente_related_items
                })
            
            # Adicionar equipamento relacionado
            equip = pat.equipamento
            if equip and equip.id not in included_ids['equipamento_cliente']:
                included_ids['equipamento_cliente'].add(equip.id)
                
                # Adicionar aos relacionamentos
                related_items.append({
                    'title': f"{get_attribute_safely(equip.equipamento_fabricado, 'nome')} ({equip.numero_serie})",
                    'url': get_url_safely('equipamentos:historico_equipamento_cliente', equipamento_id=equip.id),
                    'icon': 'bi-cpu'
                })
                
                # Adicionar aos resultados
                equip_related_items = [{
                    'title': f"PAT #{pat.pat_number}",
                    'url': get_url_safely('assistencia:detalhes_pat', pat_id=pat.id),
                    'icon': 'bi-tools'
                }]
                
                results['equipamentos_cliente'].append({
                    'obj': equip,
                    'title': f"{get_attribute_safely(equip.equipamento_fabricado, 'nome')} - {equip.numero_serie}",
                    'subtitle': f"Cliente: {get_attribute_safely(equip.cliente, 'nome')}",
                    'url': get_url_safely('equipamentos:historico_equipamento_cliente', equipamento_id=equip.id),
                    'icon': 'bi-cpu',
                    'related_items': equip_related_items
                })
            
            # Adicionar PAT aos resultados
            estado_display = getattr(pat, 'get_estado_display', lambda: 'N/A')
            results['pats'].append({
                'obj': pat,
                'title': f"PAT #{pat.pat_number}",
                'subtitle': f"Cliente: {get_attribute_safely(pat.cliente, 'nome')} - {estado_display()}",
                'url': get_url_safely('assistencia:detalhes_pat', pat_id=pat.id),
                'icon': 'bi-tools',
                'related_items': related_items
            })
    
    # PASSO 5: Buscar peças
    pecas = Peca.objects.all()
    
    for peca in pecas:
        # Verificar campos da peça
        match_found = False
        for field in ['nome', 'referencia', 'descricao']:
            value = get_attribute_safely(peca, field)
            if value and normalized_query in normalize_text(str(value)):
                match_found = True
                break
                
        if match_found and peca.id not in included_ids['peca']:
            included_ids['peca'].add(peca.id)
            
            # Adicionar peça aos resultados
            results['pecas'].append({
                'obj': peca,
                'title': peca.nome,
                'subtitle': f"Ref: {get_attribute_safely(peca, 'referencia', 'N/A')}",
                'url': get_url_safely('stock:detalhes_peca', peca_id=peca.id),
                'icon': 'bi-gear'
            })
    
    # Contar total de resultados
    total_results = sum(len(items) for items in results.values())
    
    return render(request, 'search/results.html', {
        'query': query,
        'results': results,
        'total_results': total_results
    })

