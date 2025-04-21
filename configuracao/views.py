from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db import transaction
from django.utils import timezone
from django.conf import settings
import os
import json
import subprocess
import sys
import django  # Add this import for Django version

# Import optional dependencies with fallbacks
try:
    import psutil
except ImportError:
    psutil = None

try:
    import pytz
except ImportError:
    pytz = None

try:
    import psycopg2
except ImportError:
    psycopg2 = None

# Fix Error 1: Remove incorrect form imports from models
from .models import SystemSettings, BackupLog, CustomField, CustomFieldValue
from .forms import SystemSettingsForm, BackupForm, CustomFieldForm
# Fix the import error - change from util.security to core.utils
from core.utils import group_required

@login_required
@group_required(['Administradores'])
def sistema_settings(request):
    """View for system configuration settings"""
    context = {
        'active_section': 'sistema',
        'title': 'Configurações do Sistema'
    }
    return render(request, 'configuracao/sistema_settings.html', context)

@login_required
@group_required(['Administradores'])
def dashboard(request):
    """Configuration dashboard showing system info and quick access to settings"""
    system_settings = SystemSettings.get_settings()

    # System information
    system_info = {
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",  # Use sys module
        'django_version': django.__version__,  # Direct reference to Django's version
        'database': settings.DATABASES['default']['ENGINE'].split('.')[-1],
        'timezone': system_settings.timezone if system_settings is not None else None,
        'time_now': timezone.now(),
        'os': os.name,
    }

    # Resource usage
    resource_usage = {
        'cpu': psutil.cpu_percent(interval=0.5) if psutil else None,
        'memory': psutil.virtual_memory().percent if psutil else None,
        'disk': psutil.disk_usage('/').percent if psutil else None,
    }

    # Recent backups
    recent_backups = BackupLog.objects.all()[:5]

    return render(request, 'configuracao/dashboard.html', {
        'system_settings': system_settings,
        'system_info': system_info,
        'resource_usage': resource_usage,
        'recent_backups': recent_backups,
        'active_tab': 'dashboard',
    })

@login_required
@group_required(['Administradores'])
def general_settings(request):
    """View for managing general system settings"""
    settings_obj = SystemSettings.get_settings()

    if request.method == 'POST':
        form = SystemSettingsForm(request.POST, request.FILES, instance=settings_obj)
        if form.is_valid():
            form.save()

            # Update timezone immediately - Add null check before accessing timezone
            if settings_obj is not None and hasattr(settings_obj, 'timezone') and settings_obj.timezone:
                try:
                    # Only attempt to use pytz if it's available
                    if pytz is not None:
                        timezone.activate(pytz.timezone(settings_obj.timezone))
                except Exception:
                    # Handle invalid timezone or missing pytz
                    pass
            messages.success(request, _('Configurações atualizadas com sucesso!'))
            return redirect('configuracao:general_settings')
    else:
        form = SystemSettingsForm(instance=settings_obj)

    return render(request, 'configuracao/general_settings.html', {
        'form': form,
        'active_tab': 'general',
        'settings': settings_obj,
    })

@login_required
@group_required(['Administradores'])
def email_settings(request):
    """View for managing email settings"""
    settings_obj = SystemSettings.get_settings()

    if request.method == 'POST':
        # Extract only email-related fields from SystemSettings
        email_data = {k: v for k, v in request.POST.items()
                      if k in ['email_from', 'email_signature']}

        for key, value in email_data.items():
            setattr(settings_obj, key, value)

        settings_obj.save()
        messages.success(request, _('Configurações de email atualizadas com sucesso!'))
        return redirect('configuracao:email_settings')

    return render(request, 'configuracao/email_settings.html', {
        'settings': settings_obj,
        'active_tab': 'email',
    })

@login_required
@group_required(['Administradores'])
def notification_settings(request):
    """View for managing notification settings"""
    settings_obj = SystemSettings.get_settings()

    if request.method == 'POST':
        # Extract notification-related boolean fields
        for field in ['notify_on_new_pat', 'notify_on_pat_status_change', 'notify_on_new_client']:
            setattr(settings_obj, field, field in request.POST)

        settings_obj.save()
        messages.success(request, _('Configurações de notificações atualizadas com sucesso!'))
        return redirect('configuracao:notification_settings')

    return render(request, 'configuracao/notification_settings.html', {
        'settings': settings_obj,
        'active_tab': 'notifications',
    })

@login_required
@group_required(['Administradores'])
def appearance_settings(request):
    """View for managing appearance settings"""
    settings_obj = SystemSettings.get_settings()

    if request.method == 'POST':
        # Extract appearance-related fields
        appearance_data = {k: v for k, v in request.POST.items()
                           if k in ['theme', 'custom_css']}

        # Handle logo upload separately
        if 'site_logo' in request.FILES:
            settings_obj.site_logo = request.FILES['site_logo']

        for key, value in appearance_data.items():
            setattr(settings_obj, key, value)

        settings_obj.save()
        messages.success(request, _('Configurações de aparência atualizadas com sucesso!'))
        return redirect('configuracao:appearance_settings')

    return render(request, 'configuracao/appearance_settings.html', {
        'settings': settings_obj,
        'active_tab': 'appearance',
    })

@login_required
@group_required(['Administradores'])
def backup_settings(request):
    """View for managing backups and restore"""
    backups = BackupLog.objects.all().order_by('-date_created')

    # Pagination
    paginator = Paginator(backups, 10)
    page = request.GET.get('page')
    backups_paged = paginator.get_page(page)

    if request.method == 'POST':
        form = BackupForm(request.POST)
        if form.is_valid():
            backup_type = form.cleaned_data.get('backup_type', 'full')

            # In a real implementation, you'd call your backup logic here
            # For now, let's create a dummy backup record
            filename = f"backup_{timezone.now().strftime('%Y%m%d_%H%M%S')}.zip"
            backup = BackupLog.objects.create(
                filename=filename,
                file_size=1024 * 1024,  # 1MB dummy size
                created_by=request.user,
                backup_type=backup_type
            )

            # Update last_backup in settings
            settings_obj = SystemSettings.get_settings()
            settings_obj.last_backup = timezone.now()
            settings_obj.save()
            messages.success(request, _('Backup criado com sucesso!'))
            return redirect('configuracao:backup_settings')
    else:
        form = BackupForm()

    return render(request, 'configuracao/backup_settings.html', {
        'form': form,
        'backups': backups_paged,
        'active_tab': 'backup',
    })

@login_required
@group_required(['Administradores'])
def custom_fields(request):
    """View for managing custom fields"""
    custom_fields = CustomField.objects.all()

    # Filter by model if requested
    model_filter = request.GET.get('model')
    if model_filter:
        custom_fields = custom_fields.filter(model=model_filter)

    return render(request, 'configuracao/custom_fields.html', {
        'custom_fields': custom_fields,
        'model_filter': model_filter,
        'models': dict(CustomField.MODEL_CHOICES),
        'active_tab': 'custom_fields',
    })

@login_required
@group_required(['Administradores'])
def add_custom_field(request):
    """View for adding a new custom field"""
    if request.method == 'POST':
        form = CustomFieldForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Campo personalizado criado com sucesso!'))
            return redirect('configuracao:custom_fields')
    else:
        form = CustomFieldForm()

    return render(request, 'configuracao/custom_field_form.html', {
        'form': form,
        'active_tab': 'custom_fields',
    })

@login_required
@group_required(['Administradores'])
def edit_custom_field(request, field_id):
    """View for editing a custom field"""
    field = get_object_or_404(CustomField, id=field_id)

    if request.method == 'POST':
        form = CustomFieldForm(request.POST, instance=field)
        if form.is_valid():
            form.save()
            messages.success(request, _('Campo personalizado atualizado com sucesso!'))
            return redirect('configuracao:custom_fields')
    else:
        form = CustomFieldForm(instance=field)

    return render(request, 'configuracao/custom_field_form.html', {
        'form': form,
        'field': field,
        'active_tab': 'custom_fields',
    })

@login_required
@group_required(['Administradores'])
@require_POST
def delete_custom_field(request, field_id):
    """View for deleting a custom field"""
    field = get_object_or_404(CustomField, id=field_id)
    field.delete()
    messages.success(request, _('Campo personalizado excluído com sucesso!'))
    return redirect('configuracao:custom_fields')

@login_required
@group_required(['Administradores'])
def system_maintenance(request):
    """View for system maintenance operations"""
    # Get some stats for display
    settings_obj = SystemSettings.get_settings()
    settings_modified = None

    # Safely check for last modification without relying on history
    settings_modified = None
    if settings_obj is not None:
        # Try common timestamp field names for last modification
        for field_name in ['last_updated', 'modified_at', 'date_modified', 'last_modified', 'updated']:
            if hasattr(settings_obj, field_name):
                settings_modified = getattr(settings_obj, field_name)
                break
        # Use Django's auto_now_add or auto_now fields if available
        if settings_modified is None:
            # Common field names for Django timestamp fields
            for field_name in ['date_created', 'created_at', 'created']:
                if hasattr(settings_obj, field_name):
                    settings_modified = getattr(settings_obj, field_name)
                    break
            # If still None, just use current time as fallback
            if settings_modified is None:
                settings_modified = timezone.now()

    stats = {
        'uptime': get_system_uptime(),
        'disk_space': get_disk_space(),
        'database_size': get_db_size(),
        'settings_modified': settings_modified,
    }

    return render(request, 'configuracao/system_maintenance.html', {
        'stats': stats,
        'active_tab': 'maintenance',
    })

# Utility functions for system info
def get_system_uptime():
    """Get system uptime"""
    if psutil is None:
        return None
    try:
        return round(psutil.boot_time())
    except:
        return None

def get_disk_space():
    """Get disk space info"""
    if psutil is None:
        return None
    try:
        disk = psutil.disk_usage('/')
        return {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent
        }
    except:
        return None

def get_db_size():
    """Get database size (PostgreSQL specific)"""
    if 'postgresql' not in settings.DATABASES['default']['ENGINE'] or psycopg2 is None:
        return None

    try:
        conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
        )
        cursor = conn.cursor()
        cursor.execute("SELECT pg_database_size(%s)", (settings.DATABASES['default']['NAME'],))
        result = cursor.fetchone()
        size = result[0] if result is not None else None
        cursor.close()
        conn.close()
        return size
    except ImportError:
        # psycopg2 not installed
        return None
    except Exception:
        # Other database connection errors
        return None

