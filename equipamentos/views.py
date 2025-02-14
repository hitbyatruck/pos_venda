from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import EquipamentoFabricado, DocumentoEquipamento, CategoriaEquipamento
from .forms import EquipamentoFabricadoForm, DocumentoEquipamentoForm, CategoriaEquipamentoForm
from clientes.models import EquipamentoCliente



def listar_equipamentos_fabricados(request):
    """ Lista os equipamentos fabricados com opção de ordenação dinâmica. """

    ordenar_por = request.GET.get("ordenar_por", "nome")  # Ordenação padrão: Nome
    direcao = request.GET.get("direcao", "asc")  # Direção padrão: Ascendente

    # Alternar entre ascendente e descendente
    if direcao == "asc":
        equipamentos = EquipamentoFabricado.objects.all().order_by(ordenar_por)
        nova_direcao = "desc"
    else:
        equipamentos = EquipamentoFabricado.objects.all().order_by(f"-{ordenar_por}")
        nova_direcao = "asc"

    return render(request, "equipamentos/lista_equipamentos_fabricados.html", {
        "equipamentos": equipamentos,
        "ordenar_por": ordenar_por,
        "direcao": nova_direcao,  # Alternar direção corretamente
    })

def adicionar_equipamento_fabricado(request):
    if request.method == 'POST':
        form = EquipamentoFabricadoForm(request.POST, request.FILES)
        if form.is_valid():
            equipamento = form.save()
            return redirect('lista_equipamentos_fabricados')
    else:
        form = EquipamentoFabricadoForm()

    return render(request, 'equipamentos/adicionar_equipamento_fabricado.html', {'form': form})

def listar_equipamentos_cliente(request):
    equipamentos = EquipamentoCliente.objects.all()
    return render(request, 'equipamentos/lista_equipamentos_cliente.html', {'equipamentos': equipamentos})


def detalhes_equipamento(request, equipamento_id):
    equipamento = get_object_or_404(EquipamentoFabricado, id=equipamento_id)
    documentos = equipamento.documentos.all()  # Obtém todos os documentos do equipamento

    return render(request, 'equipamentos/detalhes_equipamento.html', {
        'equipamento': equipamento,
        'documentos': documentos
    })

@csrf_exempt
def excluir_equipamento_fabricado(request, equipamento_id):
    if request.method == "POST":
        equipamento = get_object_or_404(EquipamentoFabricado, id=equipamento_id)
        equipamento.delete()
        return JsonResponse({"success": True, "message": "Equipamento excluído com sucesso!"})
    return JsonResponse({"success": False, "error": "Método não permitido"}, status=405)

def editar_equipamento_fabricado(request, equipamento_id):
    equipamento = get_object_or_404(EquipamentoFabricado, pk=equipamento_id)
    form = EquipamentoFabricadoForm(instance=equipamento)
    documento_form = DocumentoEquipamentoForm()

    if request.method == 'POST':
        form = EquipamentoFabricadoForm(request.POST, request.FILES, instance=equipamento)
        if form.is_valid():
            form.save()
            return redirect('detalhes_equipamento', equipamento_id=equipamento.id)

    documentos = DocumentoEquipamento.objects.filter(equipamento=equipamento)

    return render(request, 'equipamentos/editar_equipamento_fabricado.html', {
        'form': form, 
        'documento_form': documento_form,
        'documentos': documentos
    })


def listar_categorias(request):
    categorias = CategoriaEquipamento.objects.all()
    return render(request, 'equipamentos/lista_categorias.html', {'categorias': categorias})

def adicionar_categoria(request):
    if request.method == "POST":
        form = CategoriaEquipamentoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_categorias')
    else:
        form = CategoriaEquipamentoForm()
    return render(request, 'equipamentos/adicionar_categoria.html', {'form': form})

def adicionar_documento(request, equipamento_id):
    equipamento = get_object_or_404(EquipamentoFabricado, id=equipamento_id)

    if request.method == "POST":
        form = DocumentoEquipamentoForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.equipamento = equipamento
            documento.save()
            return redirect('detalhes_equipamento', equipamento_id=equipamento.id)
    else:
        form = DocumentoEquipamentoForm()

    return render(request, 'equipamentos/adicionar_documento.html', {'form': form, 'equipamento': equipamento})

def upload_documento_equipamento(request, equipamento_id):
    if request.method == 'POST' and request.FILES.get('arquivo'):
        equipamento = get_object_or_404(EquipamentoFabricado, pk=equipamento_id)
        documento = DocumentoEquipamento(equipamento=equipamento, arquivo=request.FILES['arquivo'])
        documento.save()
        return JsonResponse({'success': True, 'documento_url': documento.arquivo.url, 'documento_id': documento.id})
    return JsonResponse({'success': False}, status=400)

def excluir_documento(request, documento_id):
    documento = get_object_or_404(DocumentoEquipamento, pk=documento_id)
    equipamento_id = documento.equipamento.id
    documento.delete()
    return redirect('editar_equipamento_fabricado', equipamento_id=equipamento_id)
