import os
import sys
import subprocess
import shutil
import sqlite3
import django
from datetime import datetime

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_venda.settings')
django.setup()

from django.conf import settings

def backup_database():
    """Create a backup of the current database file"""
    db_path = settings.DATABASES['default']['NAME']
    
    if os.path.exists(db_path):
        # Create backup directory if it doesn't exist
        backup_dir = os.path.join(os.path.dirname(db_path), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f'db_backup_{timestamp}.sqlite3')
        
        # Copy database file
        shutil.copy2(db_path, backup_path)
        print(f"Database backed up to {backup_path}")
        return True
    else:
        print(f"Warning: Database file {db_path} not found")
        return False

def reset_migrations():
    """Reset migrations for all apps"""
    apps = ['clientes', 'equipamentos', 'assistencia', 'notas', 'stock', 'core', 'configuracao']
    
    for app in apps:
        migrations_dir = os.path.join(app, 'migrations')
        
        if os.path.exists(migrations_dir):
            # Create backup directory
            backup_dir = os.path.join(app, 'migrations_backup')
            os.makedirs(backup_dir, exist_ok=True)
            
            # Move all migration files to backup except __init__.py
            for file in os.listdir(migrations_dir):
                if file.endswith('.py') and file != '__init__.py':
                    src = os.path.join(migrations_dir, file)
                    dst = os.path.join(backup_dir, file)
                    if os.path.exists(src):
                        shutil.move(src, dst)
                        print(f"Moved {file} to backup")
    
    print("All migrations have been reset")

def recreate_database():
    """Delete and recreate the database"""
    db_path = settings.DATABASES['default']['NAME']
    
    # Remove existing database file
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed database file: {db_path}")
    
    # Create empty database
    conn = sqlite3.connect(db_path)
    conn.close()
    print(f"Created new empty database file: {db_path}")

def run_migrations():
    """Create and run migrations"""
    # Make migrations
    print("Creating migrations...")
    subprocess.run([sys.executable, 'manage.py', 'makemigrations'])
    
    # Apply migrations
    print("Applying migrations...")
    subprocess.run([sys.executable, 'manage.py', 'migrate'])
    
    # Create superuser
    print("Creating default superuser (admin/admin123)...")
    subprocess.run([
        sys.executable, 'manage.py', 'shell', '-c',
        "from django.contrib.auth.models import User; "
        "User.objects.filter(username='admin').exists() or "
        "User.objects.create_superuser('admin', 'admin@example.com', 'admin123')"
    ])

if __name__ == "__main__":
    print("This script will reset your database. All existing data will be lost.")
    confirmation = input("Are you sure you want to continue? (yes/no): ")
    
    # Accept both "yes" and "y" as confirmation
    if confirmation.lower() not in ['yes', 'y']:
        print("Aborted")
        sys.exit(0)
    
    # Backup existing database
    backup_database()
    
    # Reset migrations
    reset_migrations()
    
    # Recreate database
    recreate_database()
    
    # Create and run migrations
    run_migrations()
    
    print("Database reset and migrations applied successfully!")
    print("You can now run the development server and create new data.")
