# STEP 1: Initial commit (current state)
git add .
git commit -m "Initial commit before cleanup"

# STEP 2: Remove unnecessary files and folders

# Remove migration backups
Get-ChildItem -Path . -Filter "migrations_backup" -Directory -Recurse | Remove-Item -Recurse -Force

# Remove Python cache files
Get-ChildItem -Path . -Filter "__pycache__" -Directory -Recurse | Remove-Item -Recurse -Force
Get-ChildItem -Path . -Filter "*.pyc" -Recurse | Remove-Item -Force
Get-ChildItem -Path . -Filter "*.pyo" -Recurse | Remove-Item -Force
Get-ChildItem -Path . -Filter "*.pyd" -Recurse | Remove-Item -Force

# Remove screenshots and temporary files
Get-ChildItem -Path . -Filter "screenshot_*.png" | Remove-Item -Force
Get-ChildItem -Path . -Filter "*.tmp" | Remove-Item -Force
Get-ChildItem -Path . -Filter "*.temp" | Remove-Item -Force

# Remove log files
Get-ChildItem -Path . -Filter "*.log" | Remove-Item -Force

# Remove backup files
Get-ChildItem -Path . -Filter "*_backup.*" | Remove-Item -Force
Get-ChildItem -Path . -Filter "*_backup" -Directory | Remove-Item -Recurse -Force

# STEP 3: Commit the cleanup
git add --all
git commit -m "Project cleanup: removed unnecessary files and folders"

# Push the changes (optional)
# git push origin navegacao-unificada
