from django.shortcuts import render, redirect, get_object_or_404
from .models import PedidoAssistencia
from .forms import PedidoAssistenciaForm, ItemPatFormSet
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

def criar_pat(request):
    if request.method == "POST":
        form = PedidoAssistenciaForm(request.POST)
        formset = ItemPatFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            pat = form.save()
            formset.instance = pat
            formset.save()
            return redirect('detalhes_pat', pat_id=pat.id)
    else:
        form = PedidoAssistenciaForm()
        formset = ItemPatFormSet()
    return render(request, 'assistencia/criar_pat.html', {'form': form, 'formset': formset})
    
def listar_pats(request):
    ordenar_por = request.GET.get("ordenar_por", "pat_number")
    direcao = request.GET.get("direcao", "asc")
    if direcao == "asc":
        pats = PedidoAssistencia.objects.all().order_by(ordenar_por)
        nova_direcao = "desc"
    else:
        pats = PedidoAssistencia.objects.all().order_by(f"-{ordenar_por}")
        nova_direcao = "asc"
    return render(request, 'assistencia/listar_pats.html', {
        'pats': pats,
        'ordenar_por': ordenar_por,
        'direcao': nova_direcao
    })

def detalhes_pat(request, pat_id):
    pat = get_object_or_404(PedidoAssistencia, id=pat_id)
    return render(request, 'assistencia/detalhes_pat.html', {'pat': pat})

def editar_pat(request, pat_id):
    pat = get_object_or_404(PedidoAssistencia, id=pat_id)
    if request.method == "POST":
        form = PedidoAssistenciaForm(request.POST, instance=pat)
        formset = ItemPatFormSet(request.POST, instance=pat)
        if form.is_valid() and formset.is_valid():
            pat = form.save()
            formset.save()
            return redirect('detalhes_pat', pat_id=pat.id)
    else:
        form = PedidoAssistenciaForm(instance=pat)
        formset = ItemPatFormSet(instance=pat)
    return render(request, 'assistencia/editar_pat.html', {'form': form, 'formset': formset, 'pat': pat})

@require_POST
@csrf_exempt
def excluir_pat(request, pat_id):
    pat = get_object_or_404(PedidoAssistencia, id=pat_id)
    try:
        pat.delete()
    except Exception as e:
        return JsonResponse({"success": False, "message": "Erro ao excluir PAT: " + str(e)})
    return JsonResponse({"success": True})

def equipamentos_por_cliente(request):
    """
    Retorna os equipamentos associados a um cliente em formato JSON.
    Espera um parâmetro GET 'cliente_id'.
    """
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
