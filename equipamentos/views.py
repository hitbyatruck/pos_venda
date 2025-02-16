from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import EquipamentoFabricado, DocumentoEquipamento, CategoriaEquipamento
from .forms import EquipamentoFabricadoForm, DocumentoEquipamentoForm, CategoriaEquipamentoForm
from clientes.models import EquipamentoCliente
from assistencia.models import PedidoAssistencia

# LISTAR EQUIPAMENTOS FABRICADOS
def listar_equipamentos_fabricados(request):
    ordenar_por = request.GET.get("ordenar_por", "nome")  
    direcao = request.GET.get("direcao", "asc")  

    if direcao == "asc":
        equipamentos = EquipamentoFabricado.objects.all().order_by(ordenar_por)
        nova_direcao = "desc"
    else:
        equipamentos = EquipamentoFabricado.objects.all().order_by(f"-{ordenar_por}")
        nova_direcao = "asc"

    return render(request, "equipamentos/lista_equipamentos_fabricados.html", {
        "equipamentos": equipamentos,
        "ordenar_por": ordenar_por,
        "direcao": nova_direcao,
    })

# ADICIONAR EQUIPAMENTO FABRICADO
def adicionar_equipamento_fabricado(request):
    if request.method == 'POST':
        form = EquipamentoFabricadoForm(request.POST, request.FILES)
        if form.is_valid():
            equipamento = form.save()

            # Verifica e adiciona documentos ao equipamento
            for arquivo in request.FILES.getlist('documentos'):
                DocumentoEquipamento.objects.create(equipamento=equipamento, arquivo=arquivo)

            return redirect('lista_equipamentos_fabricados')
    else:
        form = EquipamentoFabricadoForm()

    return render(request, 'equipamentos/adicionar_equipamento_fabricado.html', {'form': form})

# DETALHES DO EQUIPAMENTO
def detalhes_equipamento(request, equipamento_id):
    equipamento = get_object_or_404(EquipamentoFabricado, id=equipamento_id)
    documentos = DocumentoEquipamento.objects.filter(equipamento=equipamento)
    return render(request, 'equipamentos/detalhes_equipamento.html', {'equipamento': equipamento, 'documentos': documentos})

# EDITAR EQUIPAMENTO FABRICADO
def editar_equipamento_fabricado(request, equipamento_id):
    equipamento = get_object_or_404(EquipamentoFabricado, pk=equipamento_id)
    documentos = DocumentoEquipamento.objects.filter(equipamento=equipamento)

    if request.method == 'POST':
        form = EquipamentoFabricadoForm(request.POST, request.FILES, instance=equipamento)
        if form.is_valid():
            form.save()
            return redirect('detalhes_equipamento', equipamento_id=equipamento.id)

    form = EquipamentoFabricadoForm(instance=equipamento)
    documento_form = DocumentoEquipamentoForm()

    return render(request, 'equipamentos/editar_equipamento_fabricado.html', {
        'form': form, 
        'documento_form': documento_form,
        'documentos': documentos,
        'equipamento': equipamento,
    })

# EXCLUIR EQUIPAMENTO FABRICADO (AJAX)
@csrf_exempt
def excluir_equipamento_fabricado(request, equipamento_id):
    equipamento = get_object_or_404(EquipamentoFabricado, id=equipamento_id)

    if EquipamentoCliente.objects.filter(equipamento_fabricado=equipamento).exists() or PedidoAssistencia.objects.filter(equipamento=equipamento).exists():
        return JsonResponse({"success": False, "message": "O equipamento não pode ser excluído porque está associado a um cliente ou a uma PAT."})

    equipamento.delete()
    return JsonResponse({"success": True})

# UPLOAD DOCUMENTO EQUIPAMENTO (AJAX)
@csrf_exempt
def upload_documento_equipamento(request, equipamento_id):
    equipamento = get_object_or_404(EquipamentoFabricado, id=equipamento_id)

    if request.method == 'POST' and request.FILES.get('arquivo'):
        documento = DocumentoEquipamento.objects.create(
            equipamento=equipamento,
            arquivo=request.FILES['arquivo']
        )
        return JsonResponse({'success': True, 'documento_id': documento.id, 'documento_url': documento.arquivo.url})

    return JsonResponse({'success': False})

# EXCLUIR DOCUMENTO (AJAX)
@csrf_exempt
def excluir_documento(request, documento_id):
    documento = get_object_or_404(DocumentoEquipamento, id=documento_id)

    if request.method == 'POST':
        documento.delete()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False})

def listar_equipamentos_cliente(request):
    equipamentos = EquipamentoCliente.objects.all()
    return render(request, 'equipamentos/lista_equipamentos_cliente.html', {'equipamentos': equipamentos})

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