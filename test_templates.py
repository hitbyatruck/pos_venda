"""
Test script for checking template rendering with improved error handling
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_venda.settings')
django.setup()

from django.template import Context, Template
from django.template.loader import get_template
from django.template.exceptions import TemplateDoesNotExist, TemplateSyntaxError
from django.conf import settings
import os

def discover_templates():
    """Discover all templates in the project"""
    template_dirs = []

    # Get all template directories from settings
    for template_setting in settings.TEMPLATES:
        if 'DIRS' in template_setting:
            template_dirs.extend(template_setting['DIRS'])

    # Add app template directories
    for app_config in settings.INSTALLED_APPS:
        if not app_config.startswith('django.') and not app_config.startswith('rest_framework'):
            # Check for a templates directory in the app
            app_path = None
            try:
                module = __import__(app_config, fromlist=[''])
                app_path = os.path.dirname(module.__file__)
            except (ImportError, AttributeError):
                continue

            template_dir = os.path.join(app_path, 'templates')
            if os.path.isdir(template_dir):
                template_dirs.append(template_dir)

    print(f"Found {len(template_dirs)} template directories:")
    for directory in template_dirs:
        print(f"  - {directory}")

    # Find template files
    template_files = []
    for directory in template_dirs:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.html'):
                    rel_path = os.path.relpath(os.path.join(root, file), directory)
                    template_files.append(rel_path)

    print(f"\nFound {len(template_files)} template files, showing first 10:")
    for template in sorted(template_files)[:10]:
        print(f"  - {template}")

    return template_files

def test_template_loading():
    """Test if key templates can be loaded"""
    # Common templates to test
    templates_to_test = [
        'base.html',
        'configuracao/dashboard.html',
        'configuracao/general_settings.html',
        'configuracao/system_maintenance.html'
    ]

    print("\nTesting template loading:")
    for template_name in templates_to_test:
        try:
            template = get_template(template_name)
            print(f"✓ Template '{template_name}' loaded successfully")
        except TemplateDoesNotExist:
            print(f"✗ Template '{template_name}' not found")
        except Exception as e:
            print(f"✗ Error loading template '{template_name}': {str(e)}")

    return True

def check_available_libraries():
    """List all available template libraries"""
    print("\nAvailable template libraries:")

    try:
        from django.template import engines
        from django.template.backends.django import DjangoTemplates

        # engines.all() returns a list, not a dictionary
        for engine in engines.all():  # Remove the .values() call
            if isinstance(engine, DjangoTemplates):
                try:
                    # Go through a different route to access libraries
                    from django.template.backends.django import get_installed_libraries
                    libraries = get_installed_libraries()
                    if libraries:
                        for lib_name in sorted(libraries.keys()):
                            print(f"  - {lib_name}")
                    else:
                        print("  No template libraries found")
                except Exception as e:
                    # Fallback method to try listing builtins
                    if hasattr(engine.engine, 'builtins'):
                        print("  Built-in libraries:")
                        for builtin in engine.engine.builtins:
                            print(f"  - {builtin}")
                    else:
                        print(f"  Unable to access template libraries: {str(e)}")
            else:
                print(f"  Engine is not a Django template engine")
    except Exception as e:
        print(f"Error listing template libraries: {str(e)}")

    # Additional direct check for common libraries
    print("\nChecking specific template libraries:")
    libraries_to_check = ['humanize', 'static', 'i18n', 'l10n', 'tz']

    for lib in libraries_to_check:
        try:
            # Try creating a template that loads the library
            test_template = Template("{% load " + lib + " %}")
            print(f"✓ Library '{lib}' is available")
        except Exception as e:
            print(f"✗ Library '{lib}' is not available: {str(e)}")

    return True

if __name__ == "__main__":
    print("Testing template system...")
    discover_templates()
    test_template_loading()
    check_available_libraries()
    print("\nTemplate tests completed.")
