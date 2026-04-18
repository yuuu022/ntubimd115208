import os

directory = r"c:\Users\user\Desktop\專題\UI\UI第二版"

def fix_file(filename, is_mom):
    path = os.path.join(directory, filename)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix the history button
    content = content.replace(
        '<a class="flex items-center gap-1.5 text-on-surface-variant font-bold text-xs bg-surface-container-high px-4 py-2 rounded-full hover:bg-surface-container-highest transition-colors"\n                href="#">\n                <span class="material-symbols-outlined text-lg" data-icon="history">history</span>\n                <span>歷史回顧</span>\n            </a>',
        '<a class="flex items-center gap-1.5 text-on-surface-variant font-bold text-xs bg-surface-container-high px-4 py-2 rounded-full hover:bg-surface-container-highest transition-colors"\n                href="history.html">\n                <span class="material-symbols-outlined text-lg" data-icon="history">history</span>\n                <span>歷史回顧</span>\n            </a>'
    )
    
    # Fix the generic History links
    content = content.replace('href="#"', 'href="history.html"') if '歷史回顧' in content and 'href="#"' in content else content
    
    # Fix the mom/baby toggles
    mom_btn = '<button onclick="window.location.href=\'home_mom.html\'" class="px-4 py-1.5 rounded-full bg-white text-primary shadow-sm">媽媽</button>' if is_mom else '<button onclick="window.location.href=\'home_mom.html\'" class="px-4 py-1.5 rounded-full text-on-surface-variant">媽媽</button>'
    baby_btn = '<button onclick="window.location.href=\'home_baby.html\'" class="px-4 py-1.5 rounded-full text-on-surface-variant">寶寶</button>' if is_mom else '<button onclick="window.location.href=\'home_baby.html\'" class="px-4 py-1.5 rounded-full bg-white text-primary shadow-sm">寶寶</button>'

    # Replace existing toggles
    content = content.replace(
        '<button class="px-4 py-1.5 rounded-full bg-white text-primary shadow-sm">媽媽</button>\n                    <button class="px-4 py-1.5 rounded-full text-on-surface-variant">寶寶</button>',
        f'{mom_btn}\n                    {baby_btn}'
    )
    content = content.replace(
        '<button class="px-4 py-1.5 rounded-full text-on-surface-variant">媽媽</button>\n                    <button class="px-4 py-1.5 rounded-full bg-white text-primary shadow-sm">寶寶</button>',
        f'{mom_btn}\n                    {baby_btn}'
    )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

fix_file('home_mom.html', True)
fix_file('home_baby.html', False)

print("Linked inner buttons.")
