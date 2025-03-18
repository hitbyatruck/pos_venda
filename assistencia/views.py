from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import PedidoAssistencia
from .forms import PedidoAssistenciaForm, EditItemPatFormSet, PedidoAssistenciaFormSet
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

def criar_pat(request):
    """Cria um novo Pedido de Assistência Técnica (PAT)"""
    if request.method == "POST":
        form = PedidoAssistenciaForm(request.POST)
        formset = PedidoAssistenciaFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            pat = form.save()
            formset.instance = pat
            formset.save()
            messages.success(request, "PAT criada com sucesso.")
            return redirect('assistencia:listar_pats')

    else:
        form = PedidoAssistenciaForm()
        formset = PedidoAssistenciaFormSet()

    return render(request, 'assistencia/criar_pat.html', {'form': form, 'formset': formset})

def listar_pats(request):
    """Lista todas as PATs separadas por Estado em abas"""
    ordenar_por = request.GET.get("ordenar_por", "pat_number")
    direcao = request.GET.get("direcao", "asc")

    # Mapear nomes de colunas para os nomes reais no modelo
    mapeamento_colunas = {
        "data_criacao": "data_entrada",
        "data_entrada": "data_entrada",
        "data_reparacao": "data_reparacao",
        "cliente": "cliente__nome",
        "equipamento": "equipamento__equipamento_fabricado__nome",
        "estado": "estado",
        "pat_number": "pat_number"
    }

    # Usar o nome correto do modelo ou padrão de fallback
    ordenar_por = mapeamento_colunas.get(ordenar_por, "pat_number")

    if direcao == "asc":
        direcao_prefix = ""
        nova_direcao = "desc"
    else:
        direcao_prefix = "-"
        nova_direcao = "asc"

    # Filtrar PATs por estado
    pats_abertos = PedidoAssistencia.objects.filter(estado__in=["aberto", "em_curso", "em_diagnostico"]).order_by(f"{direcao_prefix}{ordenar_por}")
    pats_concluidos = PedidoAssistencia.objects.filter(estado="concluido").order_by(f"{direcao_prefix}{ordenar_por}")
    pats_cancelados = PedidoAssistencia.objects.filter(estado="cancelado").order_by(f"{direcao_prefix}{ordenar_por}")

    return render(request, 'assistencia/listar_pats.html', {
        'pats_abertos': pats_abertos,
        'pats_concluidos': pats_concluidos,
        'pats_cancelados': pats_cancelados,
        'ordenar_por': ordenar_por,
        'direcao': nova_direcao
    })


def detalhes_pat(request, pat_id):
    """Exibe os detalhes de um Pedido de Assistência Técnica (PAT)"""
    pat = get_object_or_404(PedidoAssistencia, id=pat_id)
    total_geral = sum(item.total for item in pat.itens.all())
    
    return render(request, 'assistencia/detalhes_pat.html', {
        'pat': pat,
        'total_geral': total_geral
    })

def editar_pat(request, pat_id):
    """Edita uma PAT e os seus itens"""
    pat = get_object_or_404(PedidoAssistencia, id=pat_id)

    if request.method == "POST":
        form = PedidoAssistenciaForm(request.POST, instance=pat)
        formset = EditItemPatFormSet(request.POST, instance=pat)

        if form.is_valid() and formset.is_valid():
            pat = form.save()
            formset.save()
            messages.success(request, "PAT atualizada com sucesso.")
            return redirect('assistencia:detalhes_pat', pat_id=pat.id)
        else:
            messages.error(request, "Erro na validação. Verifique os dados.")

    else:
        form = PedidoAssistenciaForm(instance=pat)
        formset = EditItemPatFormSet(instance=pat)

    return render(request, 'assistencia/editar_pat.html', {'form': form, 'formset': formset, 'pat': pat})

@require_POST
@csrf_exempt
def excluir_pat(request, pat_id):
    """Exclui uma PAT com confirmação dupla"""
    pat = get_object_or_404(PedidoAssistencia, id=pat_id)

    try:
        pat.delete()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "message": f"Erro ao excluir PAT: {str(e)}"})

def equipamentos_por_cliente(request):
    """Retorna os equipamentos associados ao cliente selecionado"""
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
            "numero_serie": eq.numero_serie
        }
        for eq in equipamentos
    ]

    return JsonResponse({"equipamentos": equipamentos_data})


