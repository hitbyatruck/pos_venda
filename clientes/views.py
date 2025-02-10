from django.shortcuts import render, get_object_or_404, redirect
from .models import Cliente
from .forms import ClienteForm


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
    clientes = Cliente.objects.all()
    return render(request, 'clientes/lista_clientes.html', {'clientes': clientes})

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
    cliente = get_object_or_404(Cliente, id=cliente_id)  # Obtém o cliente ou dá erro 404
    if request.method == "POST":
        cliente.delete()  # Remove o cliente da base de dados
        return redirect('lista_clientes')  # Redireciona para a lista de clientes

    return render(request, 'clientes/excluir_cliente.html', {'cliente': cliente})

