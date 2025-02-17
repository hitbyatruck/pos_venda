from django.shortcuts import render, get_object_or_404, redirect
from .models import Cliente, EquipamentoCliente 
from django.contrib import messages
from .forms import EquipamentoClienteForm, ClienteForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


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

@csrf_exempt
def excluir_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    # Verifica se existem equipamentos associados
    equipamentos_associados = cliente.equipamentos.exists()
    
    # Verifica se o objeto 'cliente' possui o atributo 'pats'
    if hasattr(cliente, 'pats'):
        pats_associadas = cliente.pats.exists()
    else:
        pats_associadas = False

    if request.method == 'POST':
        # O delete remove o cliente e, devido ao on_delete=models.CASCADE, também remove as associações
        cliente.delete()
        messages.success(request, "Cliente e todas as suas associações foram excluídos!")
        return redirect('listar_clientes')
    else:
        if equipamentos_associados or pats_associadas:
            mensagem = ("Atenção: este cliente possui equipamentos associados e/ou PAT's. "
                        "Ao excluir, todas as PAT's relacionadas e os números de série dos equipamentos associados serão removidos. "
                        "Deseja realmente excluir este cliente?")
        else:
            mensagem = "Confirma a exclusão deste cliente?"
    return render(request, 'clientes/confirmar_exclusao.html', {'cliente': cliente, 'mensagem': mensagem})

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