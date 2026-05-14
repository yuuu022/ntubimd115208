import glob, re

for filepath in glob.glob('*.html'):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '</script>' in content:
        body = content.split('</script>')[-1]
    else:
        body = content
        
    hex_colors = set(re.findall(r'(?:bg|text|border|ring)-\\[#([a-fA-F0-9]+)\\]', body))
    if hex_colors:
        print(f'{filepath}: {hex_colors}')
