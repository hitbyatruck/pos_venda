from django.shortcuts import render
from django.db.models import Q, Func, Value, F, TextField
from django.db.models.functions import Lower
from clientes.models import Cliente, EquipamentoCliente
from assistencia.models import PedidoAssistencia
from notas.models import Tarefa, Nota
from core.utils import group_required


class RemoveAccents(Func):
    function = 'remove_accents'
    template = '%(function)s(%(expressions)s)'
    output_field = TextField()

def search(request):
    query = request.GET.get('q', '').lower()
    selected_type = request.GET.get('type', '')
    show_all = not selected_type

    context = {
        'query': query,
        'selected_type': selected_type,
        'show_all': show_all,
        'clientes': [],
        'equipamentos': [],
        'pats': [],
        'tarefas': []
    }

    if query:
        # Cliente search
        if show_all or selected_type == 'clientes':
            cliente_query = Q(
                Q(nome__iregex=query.replace('e', '[eéèê]')
                               .replace('a', '[aáàâã]')
                               .replace('i', '[iíìî]')
                               .replace('o', '[oóòôõ]')
                               .replace('u', '[uúùû]')) |
                Q(email__icontains=query) |
                Q(telefone__icontains=query)
            )
            context['clientes'] = Cliente.objects.filter(cliente_query).order_by('nome')

        # Equipamento search
        if show_all or selected_type == 'equipamentos':
            equipamento_query = Q(
                Q(numero_serie__icontains=query) |
                Q(equipamento_fabricado__nome__iregex=query.replace('e', '[eéèê]')
                                                      .replace('a', '[aáàâã]')
                                                      .replace('i', '[iíìî]')
                                                      .replace('o', '[oóòôõ]')
                                                      .replace('u', '[uúùû]')) |
                Q(cliente__nome__iregex=query.replace('e', '[eéèê]')
                                           .replace('a', '[aáàâã]')
                                           .replace('i', '[iíìî]')
                                           .replace('o', '[oóòôõ]')
                                           .replace('u', '[uúùû]'))
            )
            context['equipamentos'] = (
                EquipamentoCliente.objects
                .filter(equipamento_query)
                .select_related('equipamento_fabricado', 'cliente')
                .order_by('numero_serie')
            )

        # PAT search
        if show_all or selected_type == 'pats':
            pat_query = Q(
                Q(pat_number__icontains=query) |
                Q(cliente__nome__iregex=query.replace('e', '[eéèê]')
                                           .replace('a', '[aáàâã]')
                                           .replace('i', '[iíìî]')
                                           .replace('o', '[oóòôõ]')
                                           .replace('u', '[uúùû]')) |
                Q(equipamento__numero_serie__icontains=query)
            )
            context['pats'] = (
                PedidoAssistencia.objects
                .filter(pat_query)
                .select_related(
                    'cliente',
                    'equipamento',
                    'equipamento__equipamento_fabricado'
                )
                .order_by('-pat_number')
            )

        # Tarefas search
        if show_all or selected_type == 'tarefas':
            tarefa_query = Q(
                Q(descricao__iregex=query.replace('e', '[eéèê]')
                                       .replace('a', '[aáàâã]')
                                       .replace('i', '[iíìî]')
                                       .replace('o', '[oóòôõ]')
                                       .replace('u', '[uúùû]')) |
                Q(cliente__nome__iregex=query.replace('e', '[eéèê]')
                                           .replace('a', '[aáàâã]')
                                           .replace('i', '[iíìî]')
                                           .replace('o', '[oóòôõ]')
                                           .replace('u', '[uúùû]')) |
                Q(pat__pat_number__icontains=query)
            )

            nota_query = Q(
                Q(nota__titulo__iregex=query.replace('e', '[eéèê]')
                                          .replace('a', '[aáàâã]')
                                          .replace('i', '[iíìî]')
                                          .replace('o', '[oóòôõ]')
                                          .replace('u', '[uúùû]')) |
                Q(nota__conteudo__iregex=query.replace('e', '[eéèê]')
                                            .replace('a', '[aáàâã]')
                                            .replace('i', '[iíìî]')
                                            .replace('o', '[oóòôõ]')
                                            .replace('u', '[uúùû]'))
            )

            context['tarefas'] = (
                Tarefa.objects
                .filter(tarefa_query | nota_query)
                .select_related('cliente', 'pat', 'nota')
                .order_by('-data_criacao')
                .distinct()
            )

    return render(request, 'search/search_results.html', context)