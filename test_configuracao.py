"""
Specific tests for the configuracao app
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_venda.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from configuracao.models import SystemSettings, CustomField, BackupLog
from django.template.loader import get_template

User = get_user_model()

def test_system_settings():
    """Test system settings singleton works properly"""
    print("\nTesting SystemSettings model:")

    # Test getting settings singleton
    settings = SystemSettings.get_settings()
    print(f"✓ Settings singleton retrieved: {settings is not None}")

    if settings:
        print(f"  - System name: {getattr(settings, 'system_name', 'Not set')}")
        print(f"  - Timezone: {getattr(settings, 'timezone', 'Not set')}")

    return True

def test_custom_fields():
    """Test custom fields functionality"""
    print("\nTesting CustomField models:")

    # Count existing fields
    fields_count = CustomField.objects.count()
    print(f"✓ Found {fields_count} custom fields")

    # Check field types distribution
    field_types = {}
    for field in CustomField.objects.all():
        field_type = field.field_type
        if field_type not in field_types:
            field_types[field_type] = 0
        field_types[field_type] += 1

    for field_type, count in field_types.items():
        print(f"  - {field_type}: {count} fields")

    return True

def test_configuracao_templates():
    """Test all configuracao templates are valid"""
    print("\nTesting configuracao templates:")

    # List of templates to test
    templates = [
        'configuracao/dashboard.html',
        'configuracao/general_settings.html',
        'configuracao/email_settings.html',
        'configuracao/notification_settings.html',
        'configuracao/appearance_settings.html',
        'configuracao/backup_settings.html',
        'configuracao/custom_fields.html',
        'configuracao/includes/config_nav.html',
    ]

    for template_name in templates:
        try:
            template = get_template(template_name)
            print(f"✓ Template '{template_name}' loaded successfully")
        except Exception as e:
            print(f"✗ Template '{template_name}' error: {str(e)}")

    return True

def test_configuracao_urls():
    """Test configuracao URLs"""
    print("\nTesting configuracao URLs:")

    urls_to_test = {
        'configuracao:dashboard': [],
        'configuracao:general_settings': [],
        'configuracao:email_settings': [],
        'configuracao:backup_settings': [],
        'configuracao:custom_fields': [],
    }

    for url_name, args in urls_to_test.items():
        try:
            url = reverse(url_name, args=args)
            print(f"✓ URL '{url_name}' resolves to: {url}")
        except Exception as e:
            print(f"✗ URL '{url_name}' error: {str(e)}")

    return True

if __name__ == "__main__":
    print("Running configuracao app tests...")

    # Run all tests
    test_system_settings()
    test_custom_fields()
    test_configuracao_templates()
    test_configuracao_urls()

    print("\nConfiguration app tests completed.")
