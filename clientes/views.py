from django.shortcuts import render, get_object_or_404, redirect
from .models import Cliente, EquipamentoCliente
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
    ordenar_por = request.GET.get("ordenar_por", "nome")  
    direcao = request.GET.get("direcao", "asc")  

    if direcao == "asc":
        clientes = Cliente.objects.all().order_by(ordenar_por)
        nova_direcao = "desc"
    else:
        clientes = Cliente.objects.all().order_by(f"-{ordenar_por}")
        nova_direcao = "asc"


    
    
    # Adiciona uma propriedade extra para indicar se há associações
    for cliente in clientes:
        cliente.tem_associacoes = cliente.equipamentos.exists() or (hasattr(cliente, 'pats') and cliente.pats.exists())
    
    return render(request, "clientes/lista_clientes.html", {
        "clientes": clientes,
        "ordenar_por": ordenar_por,
        "direcao": nova_direcao,
    })

def detalhes_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    pats = cliente.pats.all().order_by('pat_number')
    return render(request, 'clientes/detalhes_cliente.html', {'cliente': cliente, 'pats': pats})

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

def equipamentos_por_cliente(request):
    cliente_id = request.GET.get("cliente_id")
    if not cliente_id:
        return JsonResponse({"error": "cliente_id não fornecido."}, status=400)
    try:
        from clientes.models import Cliente
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return JsonResponse({"error": "Cliente não encontrado."}, status=404)
    
    equipamentos = cliente.equipamentos.all()
    equipamentos_data = []
    for eq in equipamentos:
        equipamentos_data.append({
            "id": eq.id,
            "nome": eq.equipamento_fabricado.nome,
            "numero_serie": eq.numero_serie,
        })
    return JsonResponse({"equipamentos": equipamentos_data})

def desassociar_equipamento(request, equipamento_cliente_id):
    equipamento = get_object_or_404(EquipamentoCliente, id=equipamento_cliente_id)
    cliente_id = equipamento.cliente.id
    equipamento.delete()
    return redirect('detalhes_cliente', cliente_id=cliente_id)
