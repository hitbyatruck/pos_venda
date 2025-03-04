# notas/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
from .models import Nota, Tarefa
from clientes.models import Cliente
from .forms import NotaForm, TarefaFormSet, TarefaIndependenteForm

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
                # Se a tarefa não tiver cliente (o getter pode gerar RelatedObjectDoesNotExist),
                # então atribuímos o cliente da nota.
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
    """
    Permite editar uma nota existente, juntamente com as tarefas associadas.
    """
    nota = get_object_or_404(Nota, id=nota_id)
    if request.method == "POST":
        form = NotaForm(request.POST, instance=nota)
        tarefa_formset = TarefaFormSet(request.POST, instance=nota)
        if form.is_valid() and tarefa_formset.is_valid():
            nota = form.save()
            tarefa_formset.save()
            return HttpResponseRedirect(reverse('detalhes_cliente', args=[nota.cliente.id]) + '#notas')
        else:
            print("Form errors:", form.errors)
            print("TarefaFormSet errors:", tarefa_formset.errors)
    else:
        form = NotaForm(instance=nota)
        tarefa_formset = TarefaFormSet(instance=nota)
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
            form.save()
            return redirect('notas:listar_tarefas_a_fazer')
    else:
        form = TarefaIndependenteForm()
    return render(request, 'notas/criar_tarefa.html', {'form': form})

def listar_tarefas_a_fazer(request):
    """
    Lista as tarefas cujo status é 'a_fazer' e também as tarefas 'concluídas'.
    """
    tarefas_a_fazer = Tarefa.objects.filter(status='a_fazer').order_by('-data_criacao')
    tarefas_concluidas = Tarefa.objects.filter(status='concluido').order_by('-data_criacao')
    return render(request, 'notas/listar_tarefas_a_fazer.html', {
         'tarefas_a_fazer': tarefas_a_fazer,
         'tarefas_concluidas': tarefas_concluidas,
    })

def fechar_tarefa(request, tarefa_id):
    """
    Marca uma tarefa como concluída.
    """
    tarefa = get_object_or_404(Tarefa, id=tarefa_id)
    tarefa.status = 'concluido'
    tarefa.save()
    messages.success(request, "Tarefa marcada como concluída com sucesso.")
    return redirect('notas:listar_tarefas_a_fazer')

def reabrir_tarefa(request, tarefa_id):
    from django.contrib import messages
    from django.shortcuts import redirect, get_object_or_404
    # Obtemos a tarefa pelo ID
    tarefa = get_object_or_404(Tarefa, id=tarefa_id)
    # Alteramos o status para 'a_fazer'
    tarefa.status = 'a_fazer'
    tarefa.save()
    messages.success(request, "Tarefa reaberta com sucesso.")
    # Redireciona para a listagem de tarefas a fazer
    return redirect('notas:listar_tarefas_a_fazer')


# View para exibir os detalhes de uma tarefa independente
def detalhes_tarefa(request, tarefa_id):
    tarefa = get_object_or_404(Tarefa, id=tarefa_id)
    return render(request, 'notas/detalhes_tarefa.html', {'tarefa': tarefa})

# View para editar uma tarefa independente
def editar_tarefa(request, tarefa_id):
    tarefa = get_object_or_404(Tarefa, id=tarefa_id)
    # Se a tarefa estiver associada a uma nota, esta view não deve ser usada
    if tarefa.nota:
        messages.error(request, "Esta tarefa está associada a uma Nota. Edite a Nota correspondente.")
        return redirect('notas:detalhes_nota', nota_id=tarefa.nota.id)
    if request.method == "POST":
        form = TarefaIndependenteForm(request.POST, instance=tarefa)
        if form.is_valid():
            form.save()
            messages.success(request, "Tarefa atualizada com sucesso.")
            return redirect('notas:detalhes_tarefa', tarefa_id=tarefa.id)
        else:
            messages.error(request, "Erro ao atualizar a tarefa. Verifique os dados.")
    else:
        form = TarefaIndependenteForm(instance=tarefa)
    return render(request, 'notas/editar_tarefa.html', {'form': form, 'tarefa': tarefa})

# View para excluir uma tarefa independente
def excluir_tarefa(request, tarefa_id):
    tarefa = get_object_or_404(Tarefa, id=tarefa_id)
    # Se a tarefa estiver associada a uma nota, redirecionamos para a nota
    if tarefa.nota:
        messages.error(request, "Esta tarefa está associada a uma Nota. Exclua a Nota correspondente se necessário.")
        return redirect('notas:detalhes_nota', nota_id=tarefa.nota.id)
    if request.method == "POST":
        tarefa.delete()
        messages.success(request, "Tarefa excluída com sucesso.")
        return redirect('notas:listar_tarefas_a_fazer')
    return render(request, 'notas/excluir_tarefa.html', {'tarefa': tarefa})