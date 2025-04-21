import os
import re

def fix_template_comparisons(root_dir):
    """Fix comparison operators in Django templates to have proper spacing."""
    fixed_files = 0
    
    # Regular expression to find comparisons without spaces
    comparison_regex = r'(\{%\s+if\s+\w+)==([\'\"][\w-]+[\'\"])'
    replacement = r'\1 == \2'
    
    # Count of templates fixed
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if file needs fixing
                new_content = re.sub(comparison_regex, replacement, content)
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    fixed_files += 1
                    print(f"Fixed comparison operators in: {file_path}")
    
    return fixed_files

def fix_trans_button_text(root_dir):
    """Replace {% trans "Filter" %} with direct text in button elements"""
    fixed_files = 0
    
    # Look for buttons with trans tags
    button_regex = r'<button[^>]*>\s*<i[^>]*></i>\s*\{%\s+trans\s+["\'](Filtrar|Filter)["\'][^%]*%\}\s*</button>'
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find all button trans issues
                matches = re.findall(button_regex, content)
                if matches:
                    # Replace with direct "Filtrar" text
                    new_content = re.sub(button_regex, 
                                         r'<button type="submit" class="btn btn-primary w-100"><i class="fas fa-filter me-1"></i> Filtrar</button>', 
                                         content)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    fixed_files += 1
                    print(f"Fixed button trans text in: {file_path}")
    
    return fixed_files

if __name__ == "__main__":
    project_root = r"c:\Users\HBT\Documents\pos_venda"
    
    print("Starting template fixes...")
    comp_fixed = fix_template_comparisons(project_root)
    trans_fixed = fix_trans_button_text(project_root)
    
    print(f"Fixed {comp_fixed} files with comparison issues")
    print(f"Fixed {trans_fixed} files with button translation issues")
