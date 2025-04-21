#!/usr/bin/env python
"""
Script to automatically fix Django template comparison operators.
Run this script whenever you encounter the "Could not parse the remainder" error.
"""
import os
import re
import sys

def fix_template_operators(directory):
    """
    Scans all .html files in the given directory (recursively) and fixes Django template 
    comparison operators by adding spaces around them.
    """
    fixed_files = 0
    fixed_occurrences = 0
    
    # Regular expressions to find problematic comparisons without spaces
    patterns = [
        (r'{% if ([a-zA-Z0-9_\.]+)==([\'"][^\']*[\'"]) %}', r'{% if \1 == \2 %}'),
        (r'{% if ([a-zA-Z0-9_\.]+)==([\'"][^\']*[\'"]) %}', r'{% if \1 == \2 %}'),
        (r'{% if ([a-zA-Z0-9_\.]+)!=([\'"][^\']*[\'"]) %}', r'{% if \1 != \2 %}'),
        (r'{% if ([a-zA-Z0-9_\.]+)>([\'"][^\']*[\'"]) %}', r'{% if \1 > \2 %}'),
        (r'{% if ([a-zA-Z0-9_\.]+)<([\'"][^\']*[\'"]) %}', r'{% if \1 < \2 %}'),
        (r'{% if ([a-zA-Z0-9_\.]+)>=([\'"][^\']*[\'"]) %}', r'{% if \1 >= \2 %}'),
        (r'{% if ([a-zA-Z0-9_\.]+)<=([\'"][^\']*[\'"]) %}', r'{% if \1 <= \2 %}'),
    ]
    
    # More specific patterns for the common scenarios we've been seeing
    specific_patterns = [
        # Common scenarios we've been fixing manually
        (r'{%\s+if\s+([a-zA-Z0-9_\.]+)==([\'][^\']*[\']|[\"][^\"]*[\"])\s+%}', r'{% if \1 == \2 %}'),
        (r'{%\s+if\s+([a-zA-Z0-9_\.]+)==([\'][^\']*[\']|[\"][^\"]*[\"])\s*%}', r'{% if \1 == \2 %}'),
        (r'{%\s+if\s+sort_by==\'([^\']+)\'\s+%}', r'{% if sort_by == \'\1\' %}'),
        
        # Handle other common variations
        (r'{%\s+if\s+parent_id\s*==\s*\'root\'\s*%}', r'{% if parent_id == \'root\' %}'),
        (r'{%\s+if\s+only_active\s*%}', r'{% if only_active %}')  # Fix completely different issue
    ]
    
    # Include specific patterns first (more precise matches)
    all_patterns = specific_patterns + patterns
    
    print(f"Scanning directory: {directory}")
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                file_fixed = False
                
                # Apply all regex patterns
                for pattern, replacement in all_patterns:
                    # Count occurrences before replacement
                    matches = re.findall(pattern, content)
                    if matches:
                        # Apply the fix
                        content = re.sub(pattern, replacement, content)
                        fixed_occurrences += len(matches)
                        file_fixed = True
                
                # Only write to file if changes were made
                if file_fixed:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    fixed_files += 1
                    print(f"Fixed: {file_path}")
    
    return fixed_files, fixed_occurrences

if __name__ == "__main__":
    # Default directory is the current Django project, but allow specifying a different one
    directory = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.getcwd())
    
    # Ensure we're in the Django project root
    if not os.path.exists(os.path.join(directory, 'manage.py')):
        parent_dir = os.path.dirname(directory)
        if os.path.exists(os.path.join(parent_dir, 'manage.py')):
            directory = parent_dir
    
    fixed_files, fixed_occurrences = fix_template_operators(directory)
    
    print("\n--- Summary ---")
    print(f"Fixed {fixed_occurrences} comparison operators in {fixed_files} files")
    
    if fixed_files > 0:
        print("\n✅ Templates have been fixed successfully!")
    else:
        print("\n✅ No issues found in templates!")
