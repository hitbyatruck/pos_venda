"""
Integration testing between different apps in the system
"""
import os
import sys
import django
import importlib
from collections import defaultdict

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_venda.settings')
django.setup()

from django.db import models
from django.apps import apps
from django.template.loader import get_template
from django.template.exceptions import TemplateDoesNotExist

def discover_real_templates():
    """Find templates that actually exist in the project"""
    print("\nMapping template structure in each app:")

    # Get all template directories
    template_dirs = {}
    project_dir = os.path.dirname(os.path.abspath(__file__))

    # Look for templates in each app directory
    for app_config in apps.get_app_configs():
        if not app_config.name.startswith('django.') and not app_config.name.startswith('rest_framework'):
            try:
                # Check if module and __file__ exist before accessing
                if hasattr(app_config, 'module') and app_config.module is not None and hasattr(app_config.module, '__file__'):
                    app_path = os.path.dirname(app_config.module.__file__)
                    template_dir = os.path.join(app_path, 'templates')
                    if os.path.exists(template_dir) and os.path.isdir(template_dir):
                        template_dirs[app_config.name] = template_dir
            except Exception as e:
                print(f"Error accessing templates for {app_config.name}: {str(e)}")
                continue

    # Also add project-level templates
    base_templates = os.path.join(project_dir, 'templates')
    if os.path.exists(base_templates) and os.path.isdir(base_templates):
        template_dirs['project'] = base_templates

    # Find templates in each app
    app_templates = defaultdict(list)

    for app, directory in template_dirs.items():
        if app != 'project':  # Skip project templates for this check
            app_specific_dir = os.path.join(directory, app)
            if os.path.exists(app_specific_dir) and os.path.isdir(app_specific_dir):
                # Look for app-specific templates
                for root, dirs, files in os.walk(app_specific_dir):
                    for file in files:
                        if file.endswith('.html'):
                            rel_path = os.path.relpath(os.path.join(root, file), directory)
                            app_templates[app].append(rel_path)

    # Test loading a few templates from each app
    print("\nTesting key templates from each app:")
    for app, templates in app_templates.items():
        print(f"\n{app.upper()} app templates:")
        for template_path in templates[:3]:  # Test first 3 templates
            try:
                template = get_template(template_path)
                print(f"✓ Successfully loaded: {template_path}")
            except TemplateDoesNotExist:
                print(f"✗ Template not found: {template_path}")
            except Exception as e:
                print(f"✗ Error loading {template_path}: {str(e)}")

    return app_templates

def analyze_model_relationships():
    """Analyze how models from different apps relate to each other"""
    print("\nAnalyzing database relationships between apps:")

    # Track relationships between apps
    app_relationships = defaultdict(set)

    for app_config in apps.get_app_configs():
        if app_config.name.startswith('django.') or app_config.name.startswith('rest_framework'):
            continue

        for model in app_config.get_models():
            model_name = model.__name__
            app_name = app_config.name

            # Check fields for relationships to other apps
            for field in model._meta.get_fields():
                # Look for ForeignKey, ManyToMany and OneToOne fields
                if isinstance(field, (models.ForeignKey, models.ManyToManyField, models.OneToOneField)):
                    try:
                        related_model = field.related_model
                        related_app = related_model._meta.app_label

                        # Only care about relationships to other apps
                        if related_app != app_name:
                            relationship = f"{app_name}.{model_name} → {related_app}.{related_model.__name__}"
                            app_relationships[app_name].add(relationship)
                    except Exception:
                        pass

    # Print the relationships
    if app_relationships:
        for app, relationships in app_relationships.items():
            if relationships:
                print(f"\n{app} depends on:")
                for rel in relationships:
                    print(f"  - {rel}")
    else:
        print("No cross-app model relationships found.")

    return app_relationships

def check_url_patterns():
    """Check how URL patterns are organized and connected"""
    print("\nAnalyzing URL patterns and includes:")

    try:
        from django.urls import get_resolver
        resolver = get_resolver()

        # Find URL includes across apps
        url_includes = defaultdict(list)

        def process_patterns(patterns, current_path=""):
            for pattern in patterns:
                if hasattr(pattern, 'url_patterns'):
                    # This is an include
                    app_name = getattr(pattern, 'app_name', '')
                    namespace = getattr(pattern, 'namespace', '')
                    new_path = current_path
                    if namespace:
                        new_path = f"{current_path}{namespace}:"
                    process_patterns(pattern.url_patterns, new_path)

                    # Try to determine which app this include is for
                    if app_name:
                        parent_app = current_path.split(':')[0] if ':' in current_path else 'root'
                        if parent_app != app_name:
                            url_includes[parent_app].append(app_name)

        process_patterns(resolver.url_patterns)

        # Display URL includes
        if url_includes:
            print("\nURL includes between apps:")
            for parent_app, included_apps in url_includes.items():
                if included_apps:
                    print(f"{parent_app} includes URLs from: {', '.join(included_apps)}")
        else:
            print("No URL includes between apps found.")

    except Exception as e:
        print(f"Error analyzing URL patterns: {str(e)}")

if __name__ == "__main__":
    print("Running comprehensive integration tests...\n")

    # Test template structure
    templates = discover_real_templates()

    # Analyze database relationships
    relationships = analyze_model_relationships()

    # Check URL patterns
    check_url_patterns()

    print("\nIntegration tests completed.")
