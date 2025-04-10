import os
import shutil
import sys

def reset_migrations(app_name):
    """Reset migrations for the specified app."""
    migrations_dir = os.path.join(app_name, 'migrations')
    
    if not os.path.exists(migrations_dir):
        print(f"Migrations directory for {app_name} doesn't exist.")
        return
    
    # Create backup directory
    backup_dir = os.path.join(app_name, 'migrations_backup')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Move all migration files to backup except __init__.py
    migration_files = [f for f in os.listdir(migrations_dir) 
                      if f.endswith('.py') and f != '__init__.py']
    
    for file in migration_files:
        src = os.path.join(migrations_dir, file)
        dst = os.path.join(backup_dir, file)
        shutil.move(src, dst)
        print(f"Moved {file} to backup")

    print(f"Migrations for {app_name} have been reset.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reset_migrations.py app_name")
        sys.exit(1)
    
    app_name = sys.argv[1]
    reset_migrations(app_name)
