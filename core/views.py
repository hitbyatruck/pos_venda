from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from assistencia.models import PedidoAssistencia
from clientes.models import Cliente, EquipamentoCliente
from equipamentos.models import EquipamentoFabricado
from datetime import datetime, timedelta
from django.utils import timezone

def permission_denied_view(request, exception=None):
    """View personalizada para erros 403 Permission Denied"""
    return render(request, '403.html', status=403)

@login_required
def dashboard(request):
    """
    Dashboard principal do sistema POS Venda
    """
    # Dados básicos
    total_clientes = Cliente.objects.count()
    total_equipamentos = EquipamentoFabricado.objects.count()
    total_pats = PedidoAssistencia.objects.count()
    
    # PATs por estado
    pats_por_estado = {
        'aberto': PedidoAssistencia.objects.filter(estado='aberto').count(),
        'em_curso': PedidoAssistencia.objects.filter(estado='em_curso').count(),
        'em_diagnostico': PedidoAssistencia.objects.filter(estado='em_diagnostico').count(),
        'concluido': PedidoAssistencia.objects.filter(estado='concluido').count(),
        'cancelado': PedidoAssistencia.objects.filter(estado='cancelado').count()
    }
    
    # PATs recentes
    pats_recentes = PedidoAssistencia.objects.select_related(
        'cliente', 'equipamento', 'equipamento__equipamento_fabricado'
    ).order_by('-data_entrada')[:5]
    
    # Clientes mais ativos (com mais PATs) - corrigido para usar 'pats' em vez de 'pedidoassistencia'
    clientes_ativos = Cliente.objects.annotate(
        num_pats=Count('pats')  # Corrigido aqui
    ).filter(num_pats__gt=0).order_by('-num_pats')[:5]
    
    # Equipamentos mais frequentes em PATs
    try:
        # Aqui também precisamos verificar o relacionamento correto
        top_equipamentos = EquipamentoFabricado.objects.annotate(
            num_pats=Count('equipamentocliente__pats', distinct=True)  # Ajuste conforme necessário
        ).filter(num_pats__gt=0).order_by('-num_pats')[:5]
    except Exception as e:
        print(f"Erro ao consultar equipamentos mais frequentes: {e}")
        # Use uma abordagem alternativa se a consulta falhar
        top_equipamentos = []
    
    # Atividade recente (últimos 30 dias)
    data_limite = datetime.now() - timedelta(days=30)
    pats_ultimos_30_dias = PedidoAssistencia.objects.filter(data_entrada__gte=data_limite).count()
    
    # Tendência (comparação com período anterior)
    periodo_anterior = datetime.now() - timedelta(days=60)
    pats_periodo_anterior = PedidoAssistencia.objects.filter(
        data_entrada__gte=periodo_anterior,
        data_entrada__lt=data_limite
    ).count()
    
    # Calcular tendência percentual
    if pats_periodo_anterior > 0:
        tendencia_percentual = ((pats_ultimos_30_dias - pats_periodo_anterior) / pats_periodo_anterior) * 100
    else:
        tendencia_percentual = 100 if pats_ultimos_30_dias > 0 else 0
    
    context = {
        'total_clientes': total_clientes,
        'total_equipamentos': total_equipamentos,
        'total_pats': total_pats,
        'pats_por_estado': pats_por_estado,
        'pats_recentes': pats_recentes,
        'clientes_ativos': clientes_ativos,
        'top_equipamentos': top_equipamentos,
        'pats_ultimos_30_dias': pats_ultimos_30_dias,
        'tendencia_percentual': tendencia_percentual,
        'tendencia_positiva': tendencia_percentual >= 0,
    }
    
    hoje = timezone.now().date()
    dados_grafico = []
    
    for i in range(5, -1, -1):
        data_inicio = hoje.replace(day=1) - timedelta(days=i*30)
        if i > 0:
            data_fim = hoje.replace(day=1) - timedelta(days=(i-1)*30)
        else:
            data_fim = hoje
            
        mes_nome = data_inicio.strftime('%b')
        count = PedidoAssistencia.objects.filter(
            data_entrada__gte=data_inicio,
            data_entrada__lt=data_fim
        ).count()
        
        dados_grafico.append({
            'mes': mes_nome, 
            'count': count
        })
    
    # Dados para gráfico pizza de PATs por estado
    dados_pizza = [
        {'estado': 'Abertos', 'count': pats_por_estado['aberto'], 'cor': '#dc3545'},
        {'estado': 'Em Curso', 'count': pats_por_estado['em_curso'], 'cor': '#ffc107'},
        {'estado': 'Em Diagnóstico', 'count': pats_por_estado['em_diagnostico'], 'cor': '#17a2b8'},
        {'estado': 'Concluídos', 'count': pats_por_estado['concluido'], 'cor': '#28a745'},
        {'estado': 'Cancelados', 'count': pats_por_estado['cancelado'], 'cor': '#6c757d'}
    ]
    
    # Adicionar os dados ao contexto
    context.update({
        'dados_grafico': dados_grafico,
        'dados_pizza': dados_pizza,
    })
    
    return render(request, 'core/dashboard.html', context)