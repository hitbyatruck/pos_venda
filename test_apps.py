"""
Utility script to test individual app functionality
"""
import os
import sys
import django
import importlib

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_venda.settings')
django.setup()

def test_configuracao_app():
    """Test core functionality of the configuration app"""
    from configuracao.models import SystemSettings

    # Test settings singleton
    settings = SystemSettings.get_settings()
    print(f"System settings loaded: {settings is not None}")

    # Test backup functionality
    from configuracao.models import BackupLog
    backup_count = BackupLog.objects.count()
    print(f"Current backup records: {backup_count}")

    # Test custom fields
    from configuracao.models import CustomField
    custom_fields = CustomField.objects.all()
    print(f"Custom fields defined: {custom_fields.count()}")

    return True

def check_app_exists(app_name):
    """Check if an app exists in the project"""
    try:
        importlib.import_module(f"{app_name}.models")
        return True
    except ImportError:
        print(f"App '{app_name}' not found or models.py missing")
        return False

# Remove test_cliente_app and test_vendas_app functions since they don't exist

def discover_available_apps():
    """Discover which Django apps are available in the project"""
    from django.apps import apps
    available_apps = [app.name for app in apps.get_app_configs()]
    print(f"Available apps in project: {', '.join(available_apps)}")
    return available_apps

def create_test_function_for_app(app_name):
    """Dynamically create a test function for an app that exists but doesn't have a specific test"""
    def generic_test():
        print(f"Running generic test for {app_name}")
        try:
            # Import the models module
            models_module = importlib.import_module(f"{app_name}.models")
            # Get all model classes
            import inspect
            from django.db import models as django_models

            model_classes = []
            for name, obj in inspect.getmembers(models_module):
                if inspect.isclass(obj) and issubclass(obj, django_models.Model) and obj.__module__ == models_module.__name__:
                    model_classes.append(obj)

            print(f"Found {len(model_classes)} models in {app_name}")
            for model in model_classes:
                try:
                    count = model.objects.count()
                    print(f"  - {model.__name__}: {count} records")
                except Exception as e:
                    print(f"  - Error counting {model.__name__}: {str(e)}")

            return True
        except Exception as e:
            print(f"Error testing {app_name}: {str(e)}")
            return False

    return generic_test

if __name__ == "__main__":
    print("Discovering available apps in project...")
    available_apps = discover_available_apps()

    # Only include configuracao and other existing apps
    apps_to_test = []

    # Add known apps that we have tests for
    if "configuracao" in available_apps:
        apps_to_test.append("configuracao")

    # Check other installed apps and create generic tests for them
    for app_name in available_apps:
        # Skip Django's built-in apps and apps we already have tests for
        if (app_name not in apps_to_test and
            not app_name.startswith('django.') and
            not app_name.startswith('rest_framework')):
            apps_to_test.append(app_name)

    print(f"\nWill test the following apps: {', '.join(apps_to_test)}")

    for app_name in apps_to_test:
        print(f"\n---Testing {app_name} app---")
        test_func = globals().get(f"test_{app_name}_app")

        if test_func:
            # Use existing test function
            success = test_func()
            print(f"{app_name} tests {'passed' if success else 'failed'}")
        else:
            # Create and use a generic test function
            if check_app_exists(app_name):
                generic_test = create_test_function_for_app(app_name)
                success = generic_test()
                print(f"{app_name} generic tests {'passed' if success else 'failed'}")
            else:
                print(f"Skipping {app_name} - no models found")
