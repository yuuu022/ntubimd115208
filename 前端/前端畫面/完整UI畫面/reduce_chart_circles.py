import re

files_to_modify = ['index.html', 'home_baby.html']

for filepath in files_to_modify:
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    # Change r="5" to r="2"
    html = re.sub(r'r="5" fill="#65518a" stroke="none" stroke-width="0"',
                  r'r="2" fill="#65518a" stroke="none" stroke-width="0"', html)

    # Change r="7" to r="2.5" (the highlighted one)
    html = re.sub(r'r="7" fill="#65518a" stroke="#ffffff" stroke-width="3"',
                  r'r="2.5" fill="#65518a" stroke="#ffffff" stroke-width="1.5"', html)
                  
    # Wait, also we made stroke-width="5" for the path earlier. Is that too thick?
    # A stroke width of 5 in a 100 viewBox means it will be 15-30px thick on screen!
    # Because vector-effect="non-scaling-stroke" is PRESENT on the path, the stroke-width="5" is rendered as exactly 5 screen pixels. So the line is fine!
    # But the circles do scale. So r="2" is correct.

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
