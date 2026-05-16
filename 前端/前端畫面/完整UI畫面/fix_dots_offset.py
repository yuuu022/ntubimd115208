import re

files = ['index.html', 'home_baby.html']

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Remove the <g> block containing circles from both HTML and JS
    # The circles might be r="2" or r="2.5" or r="5" or whatever.
    # So we'll use a regex that matches the entire <g> block that has <!-- Data Points -->
    # Actually, let's just delete <g>...</g> that contains <circle
    html = re.sub(r'<!-- Data Points -->\s*<g>.*?</g>', '', html, flags=re.DOTALL)
    # Also for the JS variables which might not have the comment anymore
    html = re.sub(r'<g>\s*<circle cx="0" cy="99.*?</g>', '', html, flags=re.DOTALL)

    # 2. Fix the positioning offset!
    # Change "absolute inset-0 pb-6" to "absolute inset-x-0 top-0 bottom-6"
    html = html.replace('absolute inset-0 flex flex-col justify-between pb-6', 'absolute inset-x-0 top-0 bottom-6 flex flex-col justify-between')
    html = html.replace('absolute inset-0 pb-6', 'absolute inset-x-0 top-0 bottom-6')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
