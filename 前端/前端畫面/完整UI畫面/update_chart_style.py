import re

files_to_modify = ['index.html', 'home_baby.html']

for filepath in files_to_modify:
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Remove the area gradient paths
    html = re.sub(r'\s*<!-- Area Gradient -->\s*<path d="[^"]*Z" fill="url\(#[a-zA-Z]+\)"></path>', '', html)
    html = re.sub(r'<path d="M0,100[^"]*Z" fill="url\(#[a-zA-Z]+\)"></path>', '', html)

    # 2. Make lines thicker
    html = re.sub(r'fill="none" stroke="#65518a" stroke-linecap="round" stroke-linejoin="round" stroke-width="3"',
                  r'fill="none" stroke="#65518a" stroke-linecap="round" stroke-linejoin="round" stroke-width="5"', html)

    # 3. Make the circles solid purple and slightly larger
    html = re.sub(r'r="3\.5" fill="#ffffff" stroke="#65518a" stroke-width="2\.5"',
                  r'r="5" fill="#65518a" stroke="none" stroke-width="0"', html)

    # 4. Make the highlighted circle slightly larger
    html = re.sub(r'r="5" fill="#65518a" stroke="#ffffff" stroke-width="2\.5"',
                  r'r="7" fill="#65518a" stroke="#ffffff" stroke-width="3"', html)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
