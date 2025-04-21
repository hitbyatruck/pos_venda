"""
Script to test UI integration across apps
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_venda.settings')
django.setup()

from django.template.loader import get_template, TemplateDoesNotExist
import re

def analyze_template_includes(template_name):
    """Analyze template includes to find cross-app references"""
    try:
        with open(template_name, 'r', encoding='utf-8') as f:
            content = f.read()

            # Find all includes
            includes = re.findall(r'{%\s*include\s+[\'"]([^\'"]+)[\'"]', content)
            extends = re.findall(r'{%\s*extends\s+[\'"]([^\'"]+)[\'"]', content)
            urls = re.findall(r'{%\s*url\s+[\'"]([^\'"]+)[\'"]', content)

            return {
                'includes': includes,
                'extends': extends,
                'urls': urls
            }
    except Exception as e:
        return {
            'error': str(e),
            'includes': [],
            'extends': [],
            'urls': []
        }

def find_base_templates():
    """Find all base templates and their usage"""
    print("\nAnalyzing base templates:")

    # Find common base templates
    base_templates = [
        'base.html',
        'core/base.html',
        'includes/base.html'
    ]

    for template_name in base_templates:
        try:
            template = get_template(template_name)
            print(f"✓ Base template '{template_name}' exists")

            # Find all templates that extend this base
            count = count_templates_extending(template_name)
            print(f"  - Used by {count} templates")
        except TemplateDoesNotExist:
            print(f"✗ Base template '{template_name}' not found")

    return True

def count_templates_extending(base_template):
    """Count templates that extend a given base template"""
    # This is a simplified approach - in a real scenario, you would scan the template directories
    return 0  # Placeholder

def analyze_navigation_components():
    """Analyze navigation components across the system"""
    print("\nAnalyzing navigation components:")

    nav_components = [
        'includes/sidebar.html',
        'includes/navbar.html',
        'includes/breadcrumbs.html',
        'clientes/includes/menu_clientes.html',
        'equipamentos/includes/menu_equipamentos.html',
        'stock/includes/menu_stock.html',
        'notas/includes/menu_notas.html',
        'configuracao/includes/config_nav.html',
    ]

    for component in nav_components:
        try:
            template = get_template(component)
            print(f"✓ Navigation component '{component}' exists")

            # Find the template file in the file system
            from django.template import engines
            from django.conf import settings
            import os

            # Try to locate the template file
            template_file = None
            for template_dir in settings.TEMPLATES[0]['DIRS']:
                possible_path = os.path.join(template_dir, component)
                if os.path.exists(possible_path):
                    template_file = possible_path
                    break

            # Also check app template directories
            if not template_file:
                for app_config in settings.INSTALLED_APPS:
                    if app_config.startswith('django.') or app_config.startswith('rest_framework'):
                        continue
                    try:
                        module = __import__(app_config, fromlist=[''])
                        app_dir = os.path.dirname(module.__file__)
                        template_path = os.path.join(app_dir, 'templates', component)
                        if os.path.exists(template_path):
                            template_file = template_path
                            break
                    except (ImportError, AttributeError):
                        continue

            # Analyze the template content if found
            if template_file:
                refs = analyze_template_includes(template_file)
                if 'error' not in refs:
                    print(f"  - Contains {len(refs['urls'])} URL references")
                else:
                    print(f"  - Error analyzing file: {refs['error']}")
            else:
                print(f"  - Template found but file location unknown")

        except TemplateDoesNotExist:
            print(f"✗ Navigation component '{component}' not found")
        except Exception as e:
            print(f"✗ Error analyzing component '{component}': {str(e)}")

    return True

if __name__ == "__main__":
    print("Running UI integration analysis...")

    # Run analyses
    find_base_templates()
    analyze_navigation_components()

    print("\nUI integration analysis completed.")
