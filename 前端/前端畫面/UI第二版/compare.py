import re

def extract_classes(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract just header, main and body classes
    body_match = re.search(r'<body[^>]*class="([^"]+)"', content)
    header_match = re.search(r'<header[^>]*class="([^"]+)"', content)
    main_match = re.search(r'<main[^>]*class="([^"]+)"', content)
    
    return {
        'body': body_match.group(1) if body_match else None,
        'header': header_match.group(1) if header_match else None,
        'main': main_match.group(1) if main_match else None
    }

mom_classes = extract_classes('home_mom.html')
baby_classes = extract_classes('home_baby.html')

print("BODY DIFFERENCES:")
if mom_classes['body'] != baby_classes['body']:
    print(f"Mom : {mom_classes['body']}")
    print(f"Baby: {baby_classes['body']}")
else:
    print("Identical")

print("\nHEADER DIFFERENCES:")
if mom_classes['header'] != baby_classes['header']:
    print(f"Mom : {mom_classes['header']}")
    print(f"Baby: {baby_classes['header']}")
else:
    print("Identical")

print("\nMAIN DIFFERENCES:")
if mom_classes['main'] != baby_classes['main']:
    print(f"Mom : {mom_classes['main']}")
    print(f"Baby: {baby_classes['main']}")
else:
    print("Identical")
