import os
import re

def fix_template_syntax(template_path):
    """Fix the syntax in a Django template file."""
    print(f"Processing: {template_path}")
    
    with open(template_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Fix comparison operators without spaces
    patterns = [
        (r'{%\s+if\s+(\w+)==([\'\"][^\'\"]*[\'\"])', r'{% if \1 == \2'),
        (r'{%\s+if\s+(\w+)!=([\'"][^\'\"]*[\'"])', r'{% if \1 != \2'),
        (r'{%\s+if\s+(\w+)>=([\'"][^\'\"]*[\'"])', r'{% if \1 >= \2'),
        (r'{%\s+if\s+(\w+)<=([\'"][^\'\"]*[\'"])', r'{% if \1 <= \2'),
        (r'{%\s+if\s+(\w+)>([\'"][^\'\"]*[\'"])', r'{% if \1 > \2'),
        (r'{%\s+if\s+(\w+)<([\'"][^\'\"]*[\'"])', r'{% if \1 < \2'),
    ]
    
    # Specifically target the issue in lista_categorias.html
    specific_patterns = [
        (r'sort_by==\'nome\'', r'sort_by == \'nome\''),
        (r'sort_by==\'nome_desc\'', r'sort_by == \'nome_desc\''),
        (r'sort_by==\'equipment_count\'', r'sort_by == \'equipment_count\''),
        (r'sort_by==\'nivel\'', r'sort_by == \'nivel\''),
        (r'parent_id==\'root\'', r'parent_id == \'root\''),
        (r'parent_id==cat\.id\|stringformat:', r'parent_id == cat.id|stringformat:'),
    ]
    
    modified = False
    
    # Apply specific patterns first (more precise)
    for pattern, replacement in specific_patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            modified = True
            print(f"  Fixed specific pattern: {pattern}")
    
    # Apply general patterns
    for pattern, replacement in patterns:
        matches = re.findall(pattern, content)
        if matches:
            content = re.sub(pattern, replacement, content)
            modified = True
            print(f"  Fixed general pattern: {pattern}")
    
    if modified:
        with open(template_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"✅ Fixed and saved: {template_path}")
        return True
    
    print(f"✓ No issues found in: {template_path}")
    return False

def scan_and_fix_templates(base_dir):
    """Scan all template files in the project and fix them."""
    fixed_files = 0
    
    # Look for HTML files in project directories
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.html'):
                template_path = os.path.join(root, file)
                if fix_template_syntax(template_path):
                    fixed_files += 1
    
    return fixed_files

if __name__ == "__main__":
    base_dir = os.getcwd()  # Current directory
    print(f"Scanning templates in: {base_dir}")
    
    fixed_count = scan_and_fix_templates(base_dir)
    
    print("\n=== Summary ===")
    print(f"Fixed {fixed_count} template files")
    
    specific_target = os.path.join(base_dir, 'equipamentos', 'templates', 'equipamentos', 'lista_categorias.html')
    if os.path.exists(specific_target):
        print(f"\nSpecifically checking problematic file: {specific_target}")
        fix_template_syntax(specific_target)
        
        # Verify fix
        with open(specific_target, 'r', encoding='utf-8') as f:
            content = f.read()
            if "sort_by=='nome'" in content:
                print("⚠️ WARNING: File still contains problematic syntax!")
            else:
                print("✅ File verification passed")
    
    print("\nAfter running this script, restart your Django server to clear the template cache.")
