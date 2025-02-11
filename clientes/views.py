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
    """ Lista os clientes com opção de ordenação dinâmica. """

    ordenar_por = request.GET.get("ordenar_por", "nome")  # Ordenação padrão: Nome
    direcao = request.GET.get("direcao", "asc")  # Direção padrão: Ascendente

    # Alternar entre ascendente e descendente
    if direcao == "asc":
        clientes = Cliente.objects.all().order_by(ordenar_por)
        nova_direcao = "desc"
    else:
        clientes = Cliente.objects.all().order_by(f"-{ordenar_por}")
        nova_direcao = "asc"

    return render(request, "clientes/lista_clientes.html", {
        "clientes": clientes,
        "ordenar_por": ordenar_por,
        "direcao": nova_direcao,  # Alternar direção corretamente
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

def excluir_cliente(request, cliente_id):
    if request.method == "POST":
        try:
            cliente = Cliente.objects.get(id=cliente_id)
            cliente.delete()
            return JsonResponse({"success": True})
        except Cliente.DoesNotExist:
            return JsonResponse({"success": False, "error": "Cliente não encontrado"})
    return JsonResponse({"success": False, "error": "Método inválido"})