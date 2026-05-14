import re

files = ['c:/Users/user/Desktop/專題/UI/UI第二版/index.html', 'c:/Users/user/Desktop/專題/UI/UI第二版/home_baby.html']

replacement_html = '''                            <div class="flex gap-1">
                                <button class="text-on-surface-variant/50 hover:bg-primary/10 hover:text-primary p-1 rounded-full transition-colors cursor-pointer">
                                    <span class="material-symbols-outlined text-[18px]">edit</span>
                                </button>
                                <button class="text-on-surface-variant/50 hover:bg-error/10 hover:text-error p-1 rounded-full transition-colors cursor-pointer">
                                    <span class="material-symbols-outlined text-[18px]">delete</span>
                                </button>
                            </div>'''

js_pattern = re.compile(r'<span class="material-symbols-outlined text-outline-variant text-\[18px\]">\$\{item\.icon\}</span>')

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Replace in JS
        content = js_pattern.sub(replacement_html, content)
        
        # Replace hardcoded HTML instances
        content = re.sub(r'<span class="material-symbols-outlined text-outline-variant text-\[18px\]">.*?</span>', replacement_html, content)
        content = re.sub(r'<span class="material-symbols-outlined text-outline-variant text-xl">.*?</span>', replacement_html, content)

        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f'Updated {f}')
    except Exception as e:
        print(f'Error processing {f}: {e}')
