from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import PedidoAssistencia
from .forms import PedidoAssistenciaForm, EditItemPatFormSet, PedidoAssistenciaFormSet
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

def criar_pat(request):
    if request.method == "POST":
        form = PedidoAssistenciaForm(request.POST)
        formset = PedidoAssistenciaFormSet(request.POST)  # ✅ Voltamos ao nome correto

        if form.is_valid() and formset.is_valid():
            pat = form.save()
            formset.instance = pat
            formset.save()
            messages.success(request, "PAT criada com sucesso.")
            return redirect('listar_pats')

    else:
        form = PedidoAssistenciaForm()
        formset = PedidoAssistenciaFormSet()

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
    total_geral = sum(item.total for item in pat.itens.all())
    return render(request, 'assistencia/detalhes_pat.html', {'pat': pat, 'total_geral': total_geral})

def editar_pat(request, pat_id):
    pat = get_object_or_404(PedidoAssistencia, id=pat_id)
    if request.method == "POST":
        form = PedidoAssistenciaForm(request.POST, instance=pat)
        formset = EditItemPatFormSet(request.POST, instance=pat)  # <-- Não passe extra aqui
        if form.is_valid() and formset.is_valid():
            pat = form.save()
            formset.save()
            messages.success(request, "PAT atualizada com sucesso.")
            return redirect('detalhes_pat', pat_id=pat.id)
        else:
            print("Form errors:", form.errors)
            print("Formset errors:", formset.errors)
            messages.error(request, "Erro na validação. Veja os logs do servidor.")
    else:
        form = PedidoAssistenciaForm(instance=pat)
        formset = EditItemPatFormSet(instance=pat)  # <-- Apenas instancia o formset normalmente
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
    cliente_id = request.GET.get("cliente_id")
    if not cliente_id:
        return JsonResponse({"error": "cliente_id não fornecido."}, status=400)

    try:
        from clientes.models import Cliente
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        return JsonResponse({"error": "Cliente não encontrado."}, status=404)

    equipamentos = cliente.equipamentos.all()
    equipamentos_data = [
        {
            "id": eq.id,
            "nome": eq.equipamento_fabricado.nome,
            "numero_serie": eq.numero_serie,
        }
        for eq in equipamentos
    ]
    return JsonResponse({"equipamentos": equipamentos_data})
