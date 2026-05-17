import os
import glob
import re

directory = r'c:\Users\user\Desktop\專題\UI\UI第二版'

desktop_padding = "md:px-12 lg:px-[10vw] xl:px-[15vw] 2xl:px-[20vw]"

for filepath in glob.glob(os.path.join(directory, '*.html')):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Update <main> classes
    def main_repl(match):
        classes = match.group(1)
        if 'lg:px-' not in classes:
            classes = classes + " " + desktop_padding
        return f'<main class="{classes}"'
    
    content = re.sub(r'<main\s+class="([^"]+)"', main_repl, content)

    # 2. Update top header/nav classes
    def top_repl(match):
        tag = match.group(1)
        before_class = match.group(2)
        classes = match.group(3)
        if 'lg:px-' not in classes:
            classes = classes + " " + desktop_padding
        return f'<{tag}{before_class}class="{classes}"'
    
    content = re.sub(r'<(header|nav)([^>]*)class="([^"]*top-0[^"]*)"', top_repl, content)

    # 3. Update bottom nav
    def bottom_nav_repl(match):
        before_class = match.group(1)
        classes = match.group(2)
        if 'lg:px-' not in classes:
            classes = classes + " " + desktop_padding
        return f'<nav{before_class}class="{classes}"'
    
    content = re.sub(r'<nav([^>]*)class="([^"]*bottom-0[^"]*)"', bottom_nav_repl, content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Updated desktop padding for all HTML files.")
