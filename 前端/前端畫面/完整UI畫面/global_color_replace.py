import glob
import re

# Dictionary of replacements to enforce the strict 4-color palette
replacements = {
    # Replace Secondary (teal/blue) with Primary (lavender) or Grey
    # Exception: secondary-container is allowed (super light blue)
    r'\btext-secondary\b': 'text-primary',
    r'\bbg-secondary\b': 'bg-primary',
    r'\border-secondary\b': 'border-primary',
    r'\bring-secondary\b': 'ring-primary',
    r'\btext-on-secondary\b': 'text-on-primary',
    
    # on-secondary-container is dark teal, change to dark grey
    r'\btext-on-secondary-container\b': 'text-on-surface',
    
    # Replace Tertiary (pink/red) with Primary (lavender)
    r'\btext-tertiary\b': 'text-primary',
    r'\bbg-tertiary\b': 'bg-primary',
    r'\btext-on-tertiary\b': 'text-on-primary',
    r'\bbg-tertiary-container\b': 'bg-primary-container',
    r'\btext-on-tertiary-container\b': 'text-on-primary-container',
    
    # Replace Error (red) with Primary or Grey
    r'\btext-error\b': 'text-primary',
    r'\bbg-error\b': 'bg-primary',
    r'\btext-on-error\b': 'text-on-primary',
    r'\bbg-error-container\b': 'bg-primary-container',
    r'\btext-on-error-container\b': 'text-on-primary-container',
    
    # Replace explicit hex codes if they are teal or pink
    # #2f6275 (secondary) -> #65518a (primary)
    r'#2f6275': '#65518a',
    # #1f5467 (on-secondary-container) -> #2e2f2d (on-surface)
    r'#1f5467': '#2e2f2d',
    # #7d4d5f (tertiary) -> #65518a (primary)
    r'#7d4d5f': '#65518a',
    # #b41340 (error) -> #65518a
    r'#b41340': '#65518a',
}

files_modified = []

for filepath in glob.glob('*.html'):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    for pattern, repl in replacements.items():
        new_content = re.sub(pattern, repl, new_content, flags=re.IGNORECASE)
        
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        files_modified.append(filepath)

print('Modified files:', files_modified)
