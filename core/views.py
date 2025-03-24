from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from assistencia.models import PedidoAssistencia
from clientes.models import Cliente
from datetime import datetime, timedelta
from django.utils import timezone

def permission_denied_view(request, exception=None):
    """View personalizada para erros 403 Permission Denied"""
    return render(request, '403.html', status=403)

@login_required
def dashboard(request):
    """Dashboard principal do sistema"""
    # Dados comuns para todos os usuários
    context = {
        'title': 'Dashboard',
        'today': timezone.now().date(),
    }
    
    # Estatísticas básicas - visíveis para todos
    context['total_clientes'] = Cliente.objects.count()
    
    # PATs nos últimos 30 dias
    data_limite = timezone.now() - timedelta(days=30)
    context['pat_ultimo_mes'] = PedidoAssistencia.objects.filter(
        data_entrada__gte=data_limite
    ).count()
    
    # Diferentes estatísticas baseadas no grupo do usuário
    if request.user.groups.filter(name='Administradores').exists() or request.user.is_superuser:
        # Estatísticas completas para administradores
        context['total_pats'] = PedidoAssistencia.objects.count()
        context['pats_abertos'] = PedidoAssistencia.objects.filter(estado='aberto').count()
        context['pats_concluidos'] = PedidoAssistencia.objects.filter(estado='concluido').count()
        
        # Top 5 clientes com mais PATs
        context['top_clientes'] = Cliente.objects.annotate(
            num_pats=Count('pats')
        ).order_by('-num_pats')[:5]
        
        # PATs recentes
        context['pats_recentes'] = PedidoAssistencia.objects.order_by('-data_entrada')[:10]
        
    elif request.user.groups.filter(name='Técnicos').exists():
        # Estatísticas para técnicos
        # Assumindo que há um campo técnico no modelo PAT - ajuste conforme necessário
        context['total_pats'] = PedidoAssistencia.objects.count()
        context['pats_abertos'] = PedidoAssistencia.objects.filter(estado='aberto').count()
        context['pats_atribuidos'] = PedidoAssistencia.objects.filter(
            Q(estado='aberto') | Q(estado='em_andamento')
        ).count()
        
        # PATs recentes
        context['pats_recentes'] = PedidoAssistencia.objects.order_by('-data_entrada')[:5]
        
    elif request.user.groups.filter(name='Gestores de Clientes').exists():
        # Estatísticas para gestores de clientes
        context['clientes_recentes'] = Cliente.objects.order_by('-id')[:10]
        
    return render(request, 'core/dashboard.html', context)