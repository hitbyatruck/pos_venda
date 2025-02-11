from django.shortcuts import render, get_object_or_404, redirect
from .models import Cliente
from .forms import ClienteForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


# LISTAGEM DE FUNÇÕES DE CLIENTES

def adicionar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')  # Redireciona após salvar
    else:
        form = ClienteForm()
    
    return render(request, 'clientes/adicionar_cliente.html', {'form': form})

def listar_clientes(request):
    """ Lista os clientes com opção de ordenação dinâmica, incluindo Empresa. """

    ordenar_por = request.GET.get("ordenar_por", "nome")  # Ordenação padrão: Nome
    direcao = request.GET.get("direcao", "asc")  # Direção padrão: Ascendente

    # Define a direção correta da ordenação
    if direcao == "desc":
        ordenar_por = f"-{ordenar_por}"

    # Obtém os clientes ordenados conforme a seleção
    clientes = Cliente.objects.all().order_by(ordenar_por)

    return render(request, "clientes/lista_clientes.html", {
        "clientes": clientes,
        "ordenar_por": request.GET.get("ordenar_por", ""),
        "direcao": "asc" if direcao == "desc" else "desc",  # Alternar direção na próxima ordenação
    })

def detalhes_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    return render(request, 'clientes/detalhes_cliente.html', {'cliente': cliente})

def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)  # Obtém o cliente ou dá erro 404
    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)  # Carrega o formulário com os dados do cliente
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')  # Redireciona para a lista de clientes
    else:
        form = ClienteForm(instance=cliente)  # Preenche o formulário com os dados atuais do cliente
    
    return render(request, 'clientes/editar_cliente.html', {'form': form, 'cliente': cliente})

@csrf_exempt
def excluir_cliente(request, cliente_id):
    if request.method == "POST":
        cliente = get_object_or_404(Cliente, id=cliente_id)
        cliente.delete()
        return JsonResponse({"status": "ok"})  # Remove sem erro

    return JsonResponse({"error": "Método não permitido"}, status=400)