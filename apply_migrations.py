import os
import sys
import subprocess
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_venda.settings')
django.setup()

def backup_database():
    """Create a backup of the database"""
    print("Creating database backup...")
    subprocess.run([
        sys.executable, 'manage.py', 'dumpdata', '--exclude', 'contenttypes', 
        '--exclude', 'auth.permission', '--indent', '2', '--output', 
        f'backup_{django.utils.timezone.now().strftime("%Y%m%d_%H%M%S")}.json'
    ])
    print("Backup created successfully.")

def apply_migrations():
    """Apply migrations to all apps"""
    print("Applying migrations...")
    
    # First check if there are any migrations to apply
    result = subprocess.run(
        [sys.executable, 'manage.py', 'showmigrations', '--plan'], 
        capture_output=True, 
        text=True
    )
    
    # If there are no migrations to apply
    if "[ ] " not in result.stdout:
        print("No migrations to apply.")
        
        # Run sqlmigrate to see what changes would be applied for cliente
        print("Checking SQL for Cliente model...")
        subprocess.run([
            sys.executable, 'manage.py', 'sqlmigrate', 'clientes', '0004_categoriacliente_remove_individual_empresa_associada_and_more'
        ])
        
        # Use fake migration
        print("Using --fake for cliente migrations...")
        subprocess.run([
            sys.executable, 'manage.py', 'migrate', 'clientes', 
            '0004_categoriacliente_remove_individual_empresa_associada_and_more', '--fake'
        ])
    
    # Apply all migrations
    print("Applying all migrations...")
    subprocess.run([sys.executable, 'manage.py', 'migrate'])
    print("Migrations applied successfully.")

if __name__ == "__main__":
    # Backup before any changes
    backup_database()
    
    # Apply migrations
    apply_migrations()
