import os, re

files = [f for f in os.listdir('.') if f.endswith('.html')]

icons = {
    'dashboard': 'index.html',
    'description': 'record.html',
    'child_care': 'baby.html',
    'auto_stories': 'knowledge.html',
    'diversity_1': 'helper.html'
}

def replace_item(m):
    tag = m.group(1)
    inner = m.group(2)
    full = m.group(0)
    for icon, link in icons.items():
        if f'>{icon}<' in inner or f'"{icon}"' in inner:
            if tag == 'a':
                if 'href=' in full:
                    return re.sub(r'href="[^"]*"', f'href="{link}"', full, count=1)
                else:
                    return full.replace('<a ', f'<a href="{link}" ', 1)
            elif tag == 'div':
                new_open = full[:full.index('>')]
                new_open = new_open.replace('<div', '<a', 1)
                if 'href=' not in new_open:
                    new_open += f' href="{link}"'
                return new_open + '>' + inner + '</a>'
    return full

def replace_prof(m):
    tag = m.group(1)
    full = m.group(0)
    img_match = re.search(r'<img[^>]*>', full)
    if not img_match: return full
    inner = img_match.group(0)
    
    if tag == 'a':
        if 'href=' in full:
            return re.sub(r'href="[^"]*"', 'href="profile.html"', full, count=1)
        else:
            return full.replace('<a ', '<a href="profile.html" ', 1)
    elif tag == 'div':
        new_open = full[:full.index('>')]
        new_open = new_open.replace('<div', '<a', 1)
        if 'href=' not in new_open:
            new_open += ' href="profile.html"'
        return new_open + '>\n' + inner + '\n</a>'

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    nav_match = re.search(r'<nav.*?</nav>', content, flags=re.DOTALL)
    if nav_match:
        nav_orig = nav_match.group(0)
        nav_new = re.sub(r'<(a|div)([^>]*)>(.*?)</\1>', replace_item, nav_orig, flags=re.DOTALL)
        content = content.replace(nav_orig, nav_new)
        
    content = re.sub(r'<(div|a)[^>]*>\s*<img[^>]*alt="User Profile"[^>]*>\s*</\1>', replace_prof, content, flags=re.DOTALL)
    
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)

print("Done linking pages!")
