"""
Script to test if a template exists and can be loaded
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_venda.settings')
django.setup()

from django.template.loader import get_template

template_name = 'configuracao/system_maintenance.html'
try:
    template = get_template(template_name)
    print(f"✓ Template '{template_name}' loaded successfully")
except Exception as e:
    print(f"✗ Template '{template_name}' error: {str(e)}")
