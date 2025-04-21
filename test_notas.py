"""
Script to test the notas app functionality
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_venda.settings')
django.setup()

from django.urls import reverse
from django.template.loader import get_template
from notas.models import Nota, Tarefa

def test_notas_models():
    """Test notas app models"""
    print("\nTesting Notas Models:")

    # Print count of each model
    print(f"- Notas: {Nota.objects.count()}")
    print(f"- Tarefas: {Tarefa.objects.count()}")

    # Print notes by association
    client_notes = Nota.objects.filter(cliente__isnull=False).count()
    equipment_notes = Nota.objects.filter(equipamento__isnull=False).count()
    # Fixed field name from 'pedido_assistencia' to 'pat'
    pat_notes = Nota.objects.filter(pat__isnull=False).count()

    print(f"- Notas relacionadas a clientes: {client_notes}")
    print(f"- Notas relacionadas a equipamentos: {equipment_notes}")
    print(f"- Notas relacionadas a PATs: {pat_notes}")

    return True

def test_notas_templates():
    """Test notas app templates"""
    print("\nTesting Notas Templates:")

    templates = [
        'notas/listar_notas.html',
        'notas/criar_nota.html',
        'notas/detalhes_nota.html',
        'notas/editar_nota.html',
        'notas/listar_tarefas.html',
        'notas/criar_tarefa.html',
        'notas/detalhes_tarefa.html',
        'notas/editar_tarefa.html',
    ]

    for template_name in templates:
        try:
            template = get_template(template_name)
            print(f"✓ Template '{template_name}' loaded successfully")
        except Exception as e:
            print(f"✗ Template '{template_name}' error: {str(e)}")

    return True

def test_notas_urls():
    """Test notas app URLs"""
    print("\nTesting Notas URLs:")

    urls_to_test = {
        'notas:listar_notas': [],
        'notas:criar_nota': [],
        'notas:listar_tarefas_a_fazer': [],
        'notas:criar_tarefa': [],
        'notas:api_clientes': [],
        'notas:api_equipamentos': [],
        'notas:api_pats': [],
    }

    for url_name, args in urls_to_test.items():
        try:
            url = reverse(url_name, args=args)
            print(f"✓ URL '{url_name}' resolves to: {url}")
        except Exception as e:
            print(f"✗ URL '{url_name}' error: {str(e)}")

    return True

if __name__ == "__main__":
    print("Running notas app tests...")

    # Run all tests
    test_notas_models()
    test_notas_templates()
    test_notas_urls()

    print("\nNotas app tests completed.")
