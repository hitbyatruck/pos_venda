import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group, Permission
from django.db.models import Count, Q
from assistencia.models import PedidoAssistencia
from clientes.models import Cliente
from equipamentos.models import EquipamentoFabricado, EquipamentoCliente
from datetime import datetime, timedelta
from django.utils import timezone
from core.utils import group_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _
from django.http import JsonResponse

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

    # Clientes mais ativos (com mais PATs)
    clientes_ativos = Cliente.objects.annotate(
        num_pats=Count('pats')
    ).filter(num_pats__gt=0).order_by('-num_pats')[:5]

    # Equipamentos mais frequentes em PATs
    try:
        top_equipamentos = EquipamentoFabricado.objects.annotate(
            num_pats=Count('cliente_equipamentos__pedidoassistencia')
        ).filter(num_pats__gt=0).order_by('-num_pats')[:5]
    except Exception as e:
        print(f"Erro ao consultar equipamentos mais frequentes: {e}")
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

    # Dados para gráfico de evolução de PATs ao longo do tempo (últimos 6 meses)
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

    # Converter para JSON para uso no JavaScript
    dados_grafico_json = json.dumps(dados_grafico)
    dados_pizza_json = json.dumps(dados_pizza)

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
        'dados_grafico': dados_grafico,
        'dados_pizza': dados_pizza,
        'dados_grafico_json': dados_grafico_json,  # Adicionando o JSON para o gráfico
        'dados_pizza_json': dados_pizza_json,      # Adicionando o JSON para o pizza
    }

    return render(request, 'core/dashboard.html', context)

@login_required
def settings_dashboard(request):
    """Main settings dashboard view"""
    return render(request, 'admin/settings_dashboard.html', {
        'active_section': 'dashboard'
    })

@login_required
def user_management(request):
    """User management settings page"""
    # Add logic to manage users
    return render(request, 'admin/user_management.html', {
        'active_section': 'users'
    })

@login_required
def roles_permissions(request):
    """Roles and permissions settings page"""
    # Add logic to manage roles and permissions
    return render(request, 'admin/roles_permissions.html', {
        'active_section': 'roles'
    })

@login_required
@group_required(['Administradores'])
def settings_dashboard(request):
    """Settings dashboard, accessible only to administrators"""
    return render(request, 'admin/settings_dashboard.html', {
        'active_section': 'dashboard'
    })

@login_required
@group_required(['Administradores'])
def user_management(request):
    """User management view"""
    users = get_user_model().objects.all().order_by('username')
    groups = Group.objects.all().order_by('name')

    return render(request, 'admin/user_management.html', {
        'active_section': 'users',
        'users': users,
        'groups': groups
    })

@login_required
@group_required(['Administradores'])
def user_add(request):
    """Add a new user"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        group_ids = request.POST.getlist('groups')

        # Validate the form
        if not username or not email or not password:
            messages.error(request, _('Por favor, preencha todos os campos obrigatórios.'))
            return redirect('core:user_management')

        if password != confirm_password:
            messages.error(request, _('As passwords não coincidem.'))
            return redirect('core:user_management')

        # Check if username already exists
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            messages.error(request, _('Nome de utilizador já existe.'))
            return redirect('core:user_management')

        # Create the user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Add user to groups
            if group_ids:
                groups = Group.objects.filter(id__in=group_ids)
                for group in groups:
                    user.groups.add(group)

            messages.success(request, _('Utilizador criado com sucesso.'))
        except Exception as e:
            messages.error(request, f'Erro ao criar utilizador: {str(e)}')

        return redirect('core:user_management')

    # If not POST, redirect to user management
    return redirect('core:user_management')

@login_required
@group_required(['Administradores'])
def user_edit(request):
    """Edit an existing user"""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        is_active = 'is_active' in request.POST
        group_ids = request.POST.getlist('groups')

        # Validate the form
        if not user_id or not username or not email:
            messages.error(request, _('Por favor, preencha todos os campos obrigatórios.'))
            return redirect('core:user_management')

        # Get the user
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)

            # Check if username is already taken by another user
            if User.objects.exclude(id=user_id).filter(username=username).exists():
                messages.error(request, _('Nome de utilizador já existe.'))
                return redirect('core:user_management')

            # Update the user
            user.username = username
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.is_active = is_active
            user.save()

            # Update groups
            user.groups.clear()
            if group_ids:
                groups = Group.objects.filter(id__in=group_ids)
                for group in groups:
                    user.groups.add(group)

            messages.success(request, _('Utilizador atualizado com sucesso.'))
        except User.DoesNotExist:
            messages.error(request, _('Utilizador não encontrado.'))
        except Exception as e:
            messages.error(request, f'Erro ao atualizar utilizador: {str(e)}')

        return redirect('core:user_management')

    # If not POST, redirect to user management
    return redirect('core:user_management')

@login_required
@group_required(['Administradores'])
def user_delete(request):
    """Delete a user"""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')

        if not user_id:
            messages.error(request, _('ID de utilizador não fornecido.'))
            return redirect('core:user_management')

        # Get the user
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
            username = user.username

            # Don't allow deletion of superusers or self
            if user.is_superuser:
                messages.error(request, _('Não é possível excluir um superutilizador.'))
                return redirect('core:user_management')

            if user == request.user:
                messages.error(request, _('Não é possível excluir o seu próprio utilizador.'))
                return redirect('core:user_management')

            # Delete the user
            user.delete()
            messages.success(request, _('Utilizador {} excluído com sucesso.').format(username))
        except User.DoesNotExist:
            messages.error(request, _('Utilizador não encontrado.'))
        except Exception as e:
            messages.error(request, f'Erro ao excluir utilizador: {str(e)}')

        return redirect('core:user_management')

    # If not POST, redirect to user management
    return redirect('core:user_management')

@login_required
@group_required(['Administradores'])
def group_add(request):
    """Add a new group"""
    if request.method == 'POST':
        name = request.POST.get('name')

        if not name:
            messages.error(request, _('Nome do grupo é obrigatório.'))
            return redirect('core:user_management')

        # Check if group already exists
        if Group.objects.filter(name=name).exists():
            messages.error(request, _('Grupo com este nome já existe.'))
            return redirect('core:user_management')

        # Create the group
        try:
            Group.objects.create(name=name)
            messages.success(request, _('Grupo criado com sucesso.'))
        except Exception as e:
            messages.error(request, f'Erro ao criar grupo: {str(e)}')

        return redirect('core:user_management')

    # If not POST, redirect to user management
    return redirect('core:user_management')

@login_required
@group_required(['Administradores'])
def group_edit(request):
    """Edit an existing group"""
    if request.method == 'POST':
        group_id = request.POST.get('group_id')
        name = request.POST.get('name')

        if not group_id or not name:
            messages.error(request, _('Por favor, preencha todos os campos obrigatórios.'))
            return redirect('core:user_management')

        # Get the group
        try:
            group = Group.objects.get(id=group_id)

            # Check if name is already taken by another group
            if Group.objects.exclude(id=group_id).filter(name=name).exists():
                messages.error(request, _('Grupo com este nome já existe.'))
                return redirect('core:user_management')

            # Update the group
            group.name = name
            group.save()
            messages.success(request, _('Grupo atualizado com sucesso.'))
        except Group.DoesNotExist:
            messages.error(request, _('Grupo não encontrado.'))
        except Exception as e:
            messages.error(request, f'Erro ao atualizar grupo: {str(e)}')

        return redirect('core:user_management')

    # If not POST, redirect to user management
    return redirect('core:user_management')

@login_required
@group_required(['Administradores'])
def group_delete(request):
    """Delete a group"""
    if request.method == 'POST':
        group_id = request.POST.get('group_id')

        if not group_id:
            messages.error(request, _('ID de grupo não fornecido.'))
            return redirect('core:user_management')

        # Get the group
        try:
            group = Group.objects.get(id=group_id)
            name = group.name

            # Delete the group
            group.delete()
            messages.success(request, _('Grupo {} excluído com sucesso.').format(name))
        except Group.DoesNotExist:
            messages.error(request, _('Grupo não encontrado.'))
        except Exception as e:
            messages.error(request, f'Erro ao excluir grupo: {str(e)}')

        return redirect('core:user_management')

    # If not POST, redirect to user management
    return redirect('core:user_management')

@login_required
@group_required(['Administradores'])
def roles_permissions(request):
    """Roles and permissions management view"""
    groups = Group.objects.all().order_by('name')
    permissions = Permission.objects.all().order_by('codename')

    return render(request, 'admin/roles_permissions.html', {
        'active_section': 'roles',
        'groups': groups,
        'permissions': permissions
    })

@login_required
@group_required(['Administradores'])
def group_permissions(request):
    """Update permissions for a group"""
    if request.method == 'POST':
        group_id = request.POST.get('group_id')
        permission_ids = request.POST.getlist('permissions')

        try:
            # Get the group
            group = Group.objects.get(id=group_id)

            # Clear current permissions
            group.permissions.clear()

            # Add selected permissions
            if permission_ids:
                permissions = Permission.objects.filter(id__in=permission_ids)
                group.permissions.add(*permissions)

            messages.success(request, _('Permissões atualizadas com sucesso.'))
        except Group.DoesNotExist:
            messages.error(request, _('Grupo não encontrado.'))
        except Exception as e:
            messages.error(request, f'Erro ao atualizar permissões: {str(e)}')

        return redirect('core:roles_permissions')

    # If not POST, redirect to roles and permissions page
    return redirect('core:roles_permissions')

@login_required
@group_required(['Administradores'])
def get_group_permissions(request, group_id):
    """Get permissions for a group - used for AJAX requests"""
    try:
        group = Group.objects.get(id=group_id)
        permissions = list(group.permissions.values_list('id', flat=True))
        return JsonResponse({'success': True, 'permissions': permissions})
    except Group.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Grupo não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@group_required(['Administradores'])
def settings_client_sectors(request):
    """Client sectors management view in settings app"""
    from clientes.models import Setor

    sectors = Setor.objects.all().order_by('nome')

    context = {
        'active_section': 'setores',
        'sectors': sectors,
        'title': _('Setores de Clientes')
    }

    return render(request, 'admin/settings_client_sectors.html', context)

@login_required
@group_required(['Administradores'])
def settings_contact_types(request):
    """Contact types management view in settings app"""
    from clientes.models import TipoContacto

    contact_types = TipoContacto.objects.all().order_by('nome')

    context = {
        'active_section': 'tipos_contacto',
        'contact_types': contact_types,
        'title': _('Tipos de Contacto')
    }

    return render(request, 'admin/settings_contact_types.html', context)

@login_required
@group_required(['Administradores'])
def settings_equipment_categories(request):
    """Equipment categories management view in settings app"""
    from equipamentos.models import CategoriaEquipamento

    categories = CategoriaEquipamento.objects.all().order_by('nome')

    context = {
        'active_section': 'categorias_equipamento',
        'categories': categories,
        'title': _('Categorias de Equipamentos')
    }

    return render(request, 'admin/settings_equipment_categories.html', context)

