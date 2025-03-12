from django.shortcuts import render
from django.db.models import Q
from clientes.models import Cliente, EquipamentoCliente
from notas.models import Nota, Tarefa
from assistencia.models import PedidoAssistencia

def search_view(request):
    query = request.GET.get('q', '').strip()
    context = {'query': query, 'results': {}}
    if query:
        # Buscar clientes
        clientes = Cliente.objects.filter(nome__icontains=query)
        
        # Buscar equipamentos (usando o nome do equipamento fabricado) e removendo duplicatas
        equipamentos_queryset = EquipamentoCliente.objects.filter(
            equipamento_fabricado__nome__icontains=query
        )
        equipamentos_unicos = {eq.id: eq for eq in equipamentos_queryset}.values()
        
        # Buscar PAT's: filtrando pelo número ou pelo nome do equipamento associado
        pats = PedidoAssistencia.objects.filter(
            Q(pat_number__icontains=query) | Q(equipamento__equipamento_fabricado__nome__icontains=query)
        ).distinct()
        
        # Buscar notas (título ou conteúdo)
        notas = Nota.objects.filter(Q(titulo__icontains=query) | Q(conteudo__icontains=query))
        
        # Buscar tarefas (descrição)
        tarefas = Tarefa.objects.filter(descricao__icontains=query)
        
        context['results'] = {
            'clientes': clientes,
            'equipamentos': equipamentos_unicos,
            'pats': pats,
            'notas': notas,
            'tarefas': tarefas,
        }
    return render(request, 'search/results.html', context)
