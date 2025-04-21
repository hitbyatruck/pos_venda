"""
Model inspection script to help understand model structures
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_venda.settings')
django.setup()

def inspect_model(model_class):
    """Inspect a model's fields and print them"""
    print(f"\nModel: {model_class.__name__}")
    for field in model_class._meta.fields:
        print(f" - {field.name}: {field.__class__.__name__}")

def inspect_app_models(app_name):
    """Inspect all models in an app"""
    print(f"\n=== Models in {app_name} app ===")
    try:
        from django.apps import apps
        app_models = apps.get_app_config(app_name).get_models()

        for model in app_models:
            inspect_model(model)
    except Exception as e:
        print(f"Error inspecting {app_name} app: {e}")

if __name__ == "__main__":
    # Specify which apps to inspect
    apps_to_inspect = ['clientes', 'equipamentos', 'stock', 'assistencia', 'notas']

    for app_name in apps_to_inspect:
        inspect_app_models(app_name)
