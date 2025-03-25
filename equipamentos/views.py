from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import EquipamentoFabricado, DocumentoEquipamento, CategoriaEquipamento
from .forms import EquipamentoFabricadoForm, CategoriaEquipamentoForm
from clientes.models import EquipamentoCliente
from assistencia.models import PedidoAssistencia
from notas.models import Nota
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.db.models import Q
from core.utils import group_required
from django.urls import reverse
@login_required
@group_required(['Administradores', 'Técnicos'])
def listar_equipamentos_fabricados(request):
    equipamentos = EquipamentoFabricado.objects.all()
    
    breadcrumbs = [
        {'title': ('Equipamentos'), 'url': None}
    ]
    
    return render(request, 'equipamentos/listar_equipamentos_fabricados.html', {
        'equipamentos': equipamentos,
        'breadcrumbs': breadcrumbs
    })


@login_required
@group_required(['Administradores', 'Técnicos'])
def adicionar_equipamento_fabricado(request):
    if request.method == 'POST':
        form = EquipamentoFabricadoForm(request.POST, request.FILES)
        if form.is_valid():
            equipamento = form.save()
            for arquivo in request.FILES.getlist('documentos'):
                DocumentoEquipamento.objects.create(equipamento=equipamento, arquivo=arquivo)
            return redirect('equipamentos:listar_equipamentos_fabricados')
    else:
        form = EquipamentoFabricadoForm()
    return render(request, 'equipamentos/adicionar_equipamento_fabricado.html', {'form': form})

@login_required
@group_required(['Administradores', 'Técnicos'])
def detalhes_equipamento(request, equipamento_id):
    equipamento = get_object_or_404(EquipamentoFabricado, id=equipamento_id)
    assistencias = PedidoAssistencia.objects.filter(equipamento=equipamento).order_by('-data_criacao')
    notas = Nota.objects.filter(equipamento=equipamento).order_by('-data_criacao')
    
    # Adicione breadcrumbs
    breadcrumbs = [
        {'title': ('Equipamentos'), 'url': reverse('equipamentos:listar_equipamentos')},
        {'title': equipamento.numero_serie, 'url': None}
    ]
    
    return render(request, 'equipamentos/detalhes_equipamento.html', {
        'equipamento': equipamento,
        'assistencias': assistencias,
        'notas': notas,
        'breadcrumbs': breadcrumbs  # Adicione esta linha
    })

@login_required
@group_required(['Administradores', 'Técnicos'])
def editar_equipamento_fabricado(request, equipamento_id):
    equipamento = get_object_or_404(EquipamentoFabricado, pk=equipamento_id)
    documentos = DocumentoEquipamento.objects.filter(equipamento=equipamento)
    if request.method == 'POST':
        form = EquipamentoFabricadoForm(request.POST, request.FILES, instance=equipamento)
        if form.is_valid():
            equipamento = form.save()
            for arquivo in request.FILES.getlist('documentos'):
                DocumentoEquipamento.objects.create(equipamento=equipamento, arquivo=arquivo)
            return redirect('equipamentos:detalhes_equipamento', equipamento_id=equipamento.id)
    else:
        form = EquipamentoFabricadoForm(instance=equipamento)
    return render(request, 'equipamentos/editar_equipamento_fabricado.html', {
        'form': form,
        'documentos': documentos,
        'equipamento': equipamento,
    })

@login_required
@group_required(['Administradores', 'Técnicos'])
@require_http_methods(["DELETE"])
def excluir_equipamento_fabricado(request, pk):
    try:
        equipamento = get_object_or_404(EquipamentoFabricado, pk=pk)
        force = request.GET.get('force') == 'true'
        
        try:
            equipamento.delete(force=force)
            return JsonResponse({'status': 'success'})
        except ValidationError as e:
            # Get the first message without list formatting
            message = str(e.message) if hasattr(e, 'message') else str(e.messages[0])
            return JsonResponse({
                'status': 'warning',
                'message': message,
                'requireForce': True
            })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@login_required
@group_required(['Administradores', 'Técnicos'])   
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

@login_required
@group_required(['Administradores', 'Técnicos'])
@csrf_exempt
def excluir_documento(request, documento_id):
    documento = get_object_or_404(DocumentoEquipamento, id=documento_id)
    if request.method == 'POST':
        documento.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

def listar_equipamentos_cliente(request):
    equipamentos = EquipamentoCliente.objects.all()
    
    # Adicione breadcrumbs
    breadcrumbs = [
        {'title': ('Equipamentos de Clientes'), 'url': None}
    ]
    
    return render(request, 'equipamentos/listar_equipamentos_cliente.html', {
        'equipamentos': equipamentos,
        'breadcrumbs': breadcrumbs
    })

def listar_categorias(request):
    categorias = CategoriaEquipamento.objects.all()
    return render(request, 'equipamentos/lista_categorias.html', {'categorias': categorias})

def adicionar_categoria(request):
    from .forms import CategoriaEquipamentoForm
    if request.method == "POST":
        form = CategoriaEquipamentoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('equipamentos:listar_categorias')
    else:
        form = CategoriaEquipamentoForm()
    return render(request, 'equipamentos/adicionar_categoria.html', {'form': form})
