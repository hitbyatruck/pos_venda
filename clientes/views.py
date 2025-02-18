from django.shortcuts import render, get_object_or_404, redirect
from .models import Cliente
from .forms import EquipamentoClienteForm, ClienteForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


# LISTAGEM DE FUNÇÕES DE CLIENTES

def adicionar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_clientes')
    else:
        form = ClienteForm()
    return render(request, 'clientes/adicionar_cliente.html', {'form': form})

def listar_clientes(request):
    order_by = request.GET.get('order_by', 'nome')
    clientes = Cliente.objects.all().order_by(order_by)
    
    # Adiciona uma propriedade extra para indicar se há associações
    for cliente in clientes:
        cliente.tem_associacoes = cliente.equipamentos.exists() or (hasattr(cliente, 'pats') and cliente.pats.exists())
    
    return render(request, 'clientes/lista_clientes.html', {'clientes': clientes, 'order_by': order_by})

def detalhes_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    return render(request, 'clientes/detalhes_cliente.html', {'cliente': cliente})

def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)  # Obtém o cliente ou dá erro 404
    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)  # Carrega o formulário com os dados do cliente
        if form.is_valid():
            form.save()
            return redirect('listar_clientes')  # Redireciona para a lista de clientes
    else:
        form = ClienteForm(instance=cliente)  # Preenche o formulário com os dados atuais do cliente
    
    return render(request, 'clientes/editar_cliente.html', {'form': form, 'cliente': cliente})

@require_POST
@csrf_exempt
def excluir_cliente(request, cliente_id):
    """
    Exclui um cliente. Se o cliente tiver equipamentos e/ou PAT's associados e o parâmetro force 
    não for 'true', retorna um JSON com uma mensagem para exibir o segundo modal.
    Se force for 'true', procede à exclusão.
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)
    force = request.POST.get("force", "false").lower() == "true"

    # Verifica se há associações
    has_equipamentos = cliente.equipamentos.exists()
    has_pats = cliente.pats.exists() if hasattr(cliente, 'pats') else False
    associations_exist = has_equipamentos or has_pats

    if associations_exist and not force:
        return JsonResponse({
            "success": False,
            "message": (
                "Este cliente possui equipamentos e/ou PAT's associados. "
                "Ao excluir, todos os equipamentos associados e PAT's serão removidos. "
                "Confirma a exclusão?"
            )
        })

    try:
        cliente.delete()
    except Exception as e:
        return JsonResponse({"success": False, "message": "Erro ao excluir: " + str(e)})

    return JsonResponse({"success": True})

def adicionar_equipamento_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    if request.method == "POST":
        form = EquipamentoClienteForm(request.POST)
        if form.is_valid():
            equipamento_cliente = form.save(commit=False)
            equipamento_cliente.cliente = cliente
            equipamento_cliente.save()
            return redirect('detalhes_cliente', cliente_id=cliente.id)  # Redireciona para detalhes do cliente
    else:
        form = EquipamentoClienteForm()
    
    return render(request, 'clientes/adicionar_equipamento_cliente.html', {'equipamento_form': form, 'cliente': cliente})