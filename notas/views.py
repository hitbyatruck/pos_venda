# notas/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.urls import reverse
from .models import Nota, Tarefa, PedidoAssistencia, EquipamentoCliente
from clientes.models import Cliente
from .forms import NotaForm, TarefaFormSet, TarefaIndependenteForm, EditTarefaFormSet

def listar_notas(request):
    """
    Lista todas as notas de conversa em ordem decrescente por ID.
    """
    notas = Nota.objects.all().order_by('-id')
    return render(request, 'notas/listar_notas.html', {'notas': notas})

def criar_nota(request):
    """
    Cria uma nova Nota de Conversa, possivelmente com tarefas associadas.
    Se a URL tiver ?cliente=<id>, preenche o campo cliente automaticamente.
    """
    if request.method == "POST":
        form = NotaForm(request.POST)
        tarefa_formset = TarefaFormSet(request.POST)
        if form.is_valid() and tarefa_formset.is_valid():
            # Salva a nota sem commit para poder ajustar os campos se necessário
            nota = form.save(commit=False)
            # Se a nota não tiver cliente, tenta obter do parâmetro GET 'cliente'
            if not nota.cliente:
                cliente_id = request.GET.get('cliente')
                if cliente_id:
                    try:
                        nota.cliente = Cliente.objects.get(id=cliente_id)
                    except Cliente.DoesNotExist:
                        messages.error(request, "Cliente não encontrado.")
                        return render(request, 'notas/criar_nota.html', {'form': form, 'tarefa_formset': tarefa_formset})
            nota.save()  # Agora a nota tem um ID
            # Associa o formset de tarefas à nota
            tarefa_formset.instance = nota
            # Salva as tarefas sem commit para poder ajustar o campo cliente
            for tarefa in tarefa_formset.save(commit=False):
                if not tarefa.descricao.strip():
                    continue  # Pula tarefas sem descrição
                if not getattr(tarefa, 'cliente_id', None):
                    tarefa.cliente = nota.cliente
                    tarefa.save()
            tarefa_formset.save_m2m()
            messages.success(request, "Nota criada com sucesso.")
            return HttpResponseRedirect(reverse('detalhes_cliente', args=[nota.cliente.id]) + '#notas')
        else:
            print("NotaForm errors:", form.errors)
            print("TarefaFormSet errors:", tarefa_formset.errors)
            messages.error(request, "Erro na criação da nota. Verifique os campos.")
    else:
        # Se houver ?cliente=<id> na URL, pré-preenche o campo 'cliente'
        initial_data = {}
        cliente_id = request.GET.get('cliente')
        if cliente_id:
            initial_data['cliente'] = cliente_id
        form = NotaForm(initial=initial_data)
        tarefa_formset = TarefaFormSet()
    return render(request, 'notas/criar_nota.html', {'form': form, 'tarefa_formset': tarefa_formset})

def detalhes_nota(request, nota_id):
    """
    Exibe os detalhes de uma nota de conversa.
    """
    nota = get_object_or_404(Nota, id=nota_id)
    return render(request, 'notas/detalhes_nota.html', {'nota': nota})

def editar_nota(request, nota_id):
    nota = get_object_or_404(Nota, id=nota_id)
    if request.method == "POST":
        form = NotaForm(request.POST, instance=nota)
        # Usa o formset específico para edição (sem extra)
        tarefa_formset = EditTarefaFormSet(request.POST, instance=nota)
        if form.is_valid() and tarefa_formset.is_valid():
            nota = form.save()
            tarefa_formset.save()
            return redirect('notas:detalhes_nota', nota_id=nota.id)
        else:
            print("Form errors:", form.errors)
            print("Tarefa formset errors:", tarefa_formset.errors)
    else:
        form = NotaForm(instance=nota)
        # Na edição, usamos o formset sem extra
        tarefa_formset = EditTarefaFormSet(instance=nota)
    return render(request, 'notas/editar_nota.html', {'form': form, 'tarefa_formset': tarefa_formset, 'nota': nota})



def excluir_nota(request, nota_id):
    """
    Exclui uma nota de conversa.
    Se a nota estiver associada a um cliente, redireciona para os detalhes do cliente com a aba de Notas ativa.
    """
    try:
        nota = Nota.objects.get(id=nota_id)
    except Nota.DoesNotExist:
        cliente_id = request.GET.get('cliente')
        if cliente_id:
            url = reverse('detalhes_cliente', args=[cliente_id]) + '#notas'
            return HttpResponseRedirect(url)
        else:
            return redirect('notas:listar_notas')
    
    if request.method == "POST":
        cliente_id = nota.cliente.id if nota.cliente else None
        nota.delete()
        if cliente_id:
            url = reverse('detalhes_cliente', args=[cliente_id]) + '#notas'
            return HttpResponseRedirect(url)
        else:
            return redirect('notas:listar_notas')
    else:
        return render(request, 'notas/excluir_nota.html', {'nota': nota})

def criar_tarefa(request):
    """
    Cria uma tarefa independente (fora de uma nota).
    """
    if request.method == 'POST':
        form = TarefaIndependenteForm(request.POST)
        if form.is_valid():
            tarefa = form.save(commit=False)

            # 🚀 Garante que o cliente está preenchido antes de salvar
            if not tarefa.cliente and tarefa.pat:
                tarefa.cliente = tarefa.pat.cliente  # Se tem PAT, pega o cliente dela

            if not tarefa.cliente:  # Se ainda não tem cliente, exibe erro
                messages.error(request, "Erro: Cliente é obrigatório para criar uma tarefa.")
                return render(request, 'notas/criar_tarefa.html', {'form': form})

            tarefa.save()
            return redirect('notas:listar_tarefas_a_fazer')
        else:
            messages.error(request, "Erro no formulário. Verifique os campos.")
    else:
        form = TarefaIndependenteForm()
    
    return render(request, 'notas/criar_tarefa.html', {'form': form})


def listar_tarefas_a_fazer(request):
    """
    Lista as tarefas com status 'a_fazer' e também as tarefas concluídas, para que
    possamos exibir em abas separadas.
    """
    tarefas_a_fazer = Tarefa.objects.filter(status='a_fazer').order_by('-data_criacao')
    tarefas_concluidas = Tarefa.objects.filter(status='concluido').order_by('-data_criacao')
    return render(request, 'notas/listar_tarefas_a_fazer.html', {
        'tarefas_a_fazer': tarefas_a_fazer,
        'tarefas_concluidas': tarefas_concluidas,
    })

def fechar_tarefa(request, tarefa_id):
    """Marca uma tarefa como concluída."""
    tarefa = get_object_or_404(Tarefa, id=tarefa_id)
    tarefa.status = 'concluido'
    tarefa.save()
    messages.success(request, "Tarefa marcada como concluída.")
    return redirect('notas:listar_tarefas_a_fazer')

def reabrir_tarefa(request, tarefa_id):
    """Reabre uma tarefa concluída, alterando o status para 'a_fazer'."""
    tarefa = get_object_or_404(Tarefa, id=tarefa_id)
    tarefa.status = 'a_fazer'
    tarefa.save()
    messages.success(request, "Tarefa reaberta com sucesso.")
    return redirect('notas:listar_tarefas_a_fazer')


# View para exibir os detalhes de uma tarefa independente
def detalhes_tarefa(request, tarefa_id):
    """Exibe os detalhes de uma tarefa independente."""
    tarefa = get_object_or_404(Tarefa, id=tarefa_id)
    return render(request, 'notas/detalhes_tarefa.html', {'tarefa': tarefa})

# View para editar uma tarefa independente
def editar_tarefa(request, tarefa_id):
    from .forms import TarefaIndependenteForm
    tarefa = get_object_or_404(Tarefa, id=tarefa_id)
    if request.method == "POST":
        form = TarefaIndependenteForm(request.POST, instance=tarefa)
        if form.is_valid():
            form.save()
            messages.success(request, "Tarefa atualizada com sucesso.")
            return redirect('notas:detalhes_tarefa', tarefa_id=tarefa.id)
        else:
            print("Editar Tarefa - erros:", form.errors)
    else:
        form = TarefaIndependenteForm(instance=tarefa)
    return render(request, 'notas/editar_tarefa.html', {'form': form, 'tarefa': tarefa})


# View para excluir uma tarefa independente
def excluir_tarefa(request, tarefa_id):
    """Exclui uma tarefa independente."""
    tarefa = get_object_or_404(Tarefa, id=tarefa_id)
    if request.method == "POST":
        tarefa.delete()
        messages.success(request, "Tarefa excluída com sucesso.")
        return redirect('notas:listar_tarefas_a_fazer')
    return render(request, 'notas/excluir_tarefa.html', {'tarefa': tarefa})


def api_pats(request):
    """
    Retorna as PATs associadas a um cliente ou a um equipamento específico.
    """
    cliente_id = request.GET.get('cliente')
    equipamento_id = request.GET.get('equipamento')

    pats = PedidoAssistencia.objects.all()
    
    if cliente_id:
        pats = pats.filter(cliente_id=cliente_id)

    if equipamento_id:
        pats = pats.filter(equipamento_id=equipamento_id)

    data = [{"id": pat.id, "numero": pat.pat_number} for pat in pats]
    return JsonResponse(data, safe=False)


def api_equipamentos(request):
    cliente_id = request.GET.get('cliente')
    pat_id = request.GET.get('pat')

    equipamentos = EquipamentoCliente.objects.all()
    
    if cliente_id:
        equipamentos = equipamentos.filter(cliente_id=cliente_id)
    
    if pat_id:
        # Corrigindo: agora filtramos pelo relacionamento correto entre PAT e EquipamentoCliente
        equipamentos = equipamentos.filter(pats__id=pat_id)

    data = [{"id": eq.id, "nome": str(eq.equipamento_fabricado)} for eq in equipamentos]
    return JsonResponse(data, safe=False)




def api_clientes(request):
    """
    Retorna os clientes que possuem um determinado equipamento.
    """
    equipamento_id = request.GET.get('equipamento')
    if equipamento_id:
        clientes = Cliente.objects.filter(equipamentocliente__id=equipamento_id).distinct()
    else:
        clientes = Cliente.objects.all()

    data = [{"id": cliente.id, "nome": cliente.nome} for cliente in clientes]
    return JsonResponse(data, safe=False)