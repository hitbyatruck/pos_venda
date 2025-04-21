"""
Script to test the stock app functionality
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_venda.settings')
django.setup()

from django.urls import reverse
from django.template.loader import get_template
from stock.models import Peca, Fornecedor, CategoriaPeca, EncomendaPeca, MovimentacaoStock

def test_stock_models():
    """Test stock app models"""
    print("\nTesting Stock Models:")

    # Print count of each model
    print(f"- Peças: {Peca.objects.count()}")
    print(f"- Fornecedores: {Fornecedor.objects.count()}")
    print(f"- Categorias: {CategoriaPeca.objects.count()}")
    print(f"- Encomendas: {EncomendaPeca.objects.count()}")
    print(f"- Movimentações: {MovimentacaoStock.objects.count()}")

    return True

def test_stock_templates():
    """Test stock app templates"""
    print("\nTesting Stock Templates:")

    templates = [
        'stock/dashboard.html',
        'stock/listar_pecas.html',
        'stock/adicionar_peca.html',
        'stock/listar_fornecedores.html',
        'stock/adicionar_fornecedor.html',
        'stock/listar_categorias.html',
        'stock/adicionar_categoria.html',
        'stock/listar_encomendas.html',
        'stock/adicionar_encomenda.html',
        'stock/listar_movimentacoes.html',
        'stock/adicionar_movimentacao.html',
        'stock/pecas_baixo_stock.html',
    ]

    for template_name in templates:
        try:
            template = get_template(template_name)
            print(f"✓ Template '{template_name}' loaded successfully")
        except Exception as e:
            print(f"✗ Template '{template_name}' error: {str(e)}")

    return True

def test_stock_urls():
    """Test stock app URLs"""
    print("\nTesting Stock URLs:")

    urls_to_test = {
        'stock:listar_pecas': [],
        'stock:adicionar_peca': [],
        'stock:listar_fornecedores': [],
        'stock:adicionar_fornecedor': [],
        'stock:listar_categorias': [],
        'stock:adicionar_categoria': [],
        'stock:listar_encomendas': [],
        'stock:listar_movimentacoes': [],
        'stock:pecas_baixo_stock': [],
    }

    for url_name, args in urls_to_test.items():
        try:
            url = reverse(url_name, args=args)
            print(f"✓ URL '{url_name}' resolves to: {url}")
        except Exception as e:
            print(f"✗ URL '{url_name}' error: {str(e)}")

    return True

if __name__ == "__main__":
    print("Running stock app tests...")

    # Run all tests
    test_stock_models()
    test_stock_templates()
    test_stock_urls()

    print("\nStock app tests completed.")
