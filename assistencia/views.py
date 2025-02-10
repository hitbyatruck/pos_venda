from django.shortcuts import render, get_object_or_404, redirect
from .models import PedidoAssistencia
from django.http import JsonResponse
from .forms import PedidoAssistenciaForm
from clientes.models import Cliente
from equipamentos.models import EquipamentoCliente

def lista_pats(request):
    pats = PedidoAssistencia.objects.all()
    return render(request, "assistencia/lista_pats.html", {"pats": pats})

def adicionar_pedido_assistencia(request):
    clientes = Cliente.objects.all()  # Lista todos os clientes
    cliente_id = request.GET.get('cliente_id', None)  # Obtém cliente_id da URL
    equipamentos = EquipamentoCliente.objects.none()  # Inicializa lista vazia

    if cliente_id:
        equipamentos = EquipamentoCliente.objects.filter(cliente_id=cliente_id)  # Filtra equipamentos do cliente

    form = PedidoAssistenciaForm()

    return render(request, 'assistencia/adicionar_pedido_assistencia.html', {
        'form': form,
        'clientes': clientes,
        'equipamentos': equipamentos,  # Passamos os equipamentos para o template
        'cliente_id': cliente_id,
    })

def detalhes_pedido_assistencia(request, pedido_id):
    pedido = get_object_or_404(PedidoAssistencia, id=pedido_id)
    return render(request, 'assistencia/detalhes_pedido_assistencia.html', {'pedido': pedido})

def editar_pedido_assistencia(request, pat_id):
    pedido = get_object_or_404(PedidoAssistencia, id=pat_id)
    
    if request.method == "POST":
        form = PedidoAssistenciaForm(request.POST, instance=pedido)
        if form.is_valid():
            form.save()
            return redirect("lista_pats")  # Volta para a lista de PATs
    else:
        form = PedidoAssistenciaForm(instance=pedido)
    
    return render(request, "assistencia/adicionar_pedido_assistencia.html", {"form": form})

def excluir_pedido_assistencia(request, pat_id):
    pedido = get_object_or_404(PedidoAssistencia, id=pat_id)
    
    if request.method == "POST":
        pedido.delete()
        return redirect("lista_pats")  # Voltar para a lista após exclusão

    return render(request, "assistencia/confirmar_exclusao.html", {"pedido": pedido})

def get_equipamentos(request, cliente_id):
    equipamentos = EquipamentoCliente.objects.filter(cliente_id=cliente_id).values("id", "nome", "numero_serie")
    return JsonResponse({"equipamentos": list(equipamentos)})

# Create your views here.
