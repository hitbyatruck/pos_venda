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
            equipamento = form.save(commit=False)

            # Verifica se há categoria selecionada antes de salvar
            if 'categoria' in request.POST and request.POST['categoria']:
                equipamento.categoria_id = request.POST['categoria']
            else:
                equipamento.categoria = None  # Permitir salvar sem categoria

            equipamento.save()
            return redirect('lista_equipamentos_fabricados')
    else:
        form = EquipamentoFabricadoForm()

    categorias = CategoriaEquipamento.objects.all()

    return render(request, 'equipamentos/adicionar_equipamento_fabricado.html', {'form': form, 'categorias': categorias})
    


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
    equipamento = get_object_or_404(EquipamentoFabricado, id=equipamento_id)
    documentos = equipamento.documentos.all()

    if request.method == "POST":
        form = EquipamentoFabricadoForm(request.POST, request.FILES, instance=equipamento)
        documento_form = DocumentoEquipamentoForm(request.POST, request.FILES)

        # Atualiza apenas os dados do equipamento (sem afetar documentos)
        if form.is_valid():
            form.save()

        # Se um ficheiro for realmente enviado, então grava o documento
        if 'arquivo' in request.FILES:
            if documento_form.is_valid():
                novo_documento = documento_form.save(commit=False)
                novo_documento.equipamento = equipamento
                novo_documento.save()
        
        return redirect('detalhes_equipamento', equipamento_id=equipamento.id)

    else:
        form = EquipamentoFabricadoForm(instance=equipamento)
        documento_form = DocumentoEquipamentoForm()

    return render(request, 'equipamentos/editar_equipamento_fabricado.html', {
        'form': form,
        'documento_form': documento_form,
        'equipamento': equipamento,
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

def excluir_documento(request, documento_id):
    documento = get_object_or_404(DocumentoEquipamento, id=documento_id)
    equipamento_id = documento.equipamento.id  # Guardar o ID do equipamento para redirecionamento
    documento.delete()
    messages.success(request, "Documento excluído com sucesso.")
    return redirect('detalhes_equipamento', equipamento_id=equipamento_id)