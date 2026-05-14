import glob

css_to_add = """
        /* Hide number spinner */
        input::-webkit-outer-spin-button,
        input::-webkit-inner-spin-button {
            -webkit-appearance: none;
            margin: 0;
        }
        input[type=number] {
            -moz-appearance: textfield;
        }
"""

html_files = glob.glob('*.html')
for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "/* Hide number spinner */" in content:
        continue
        
    if '</style>' in content:
        content = content.replace('</style>', css_to_add + '</style>', 1)
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {html_file}")
    elif '</head>' in content:
        style_block = f"<style>{css_to_add}</style>\n</head>"
        content = content.replace('</head>', style_block, 1)
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Added style block to {html_file}")
