import re

import os

for f in ['home_mom.html', 'home_baby.html']:
    if not os.path.exists(f):
        continue
    with open(f, 'r', encoding='utf-8') as file:
        c = file.read()
    
    c = re.sub(r'\n?\s*<div class="w-1 h-1 bg-primary/40 rounded-full mt-1\.5"></div>', '', c)
    c = re.sub(r'\n?\s*<div class="w-1\.5 h-1\.5 bg-white rounded-full mt-1\.5"></div>', '', c)
    
    with open(f, 'w', encoding='utf-8') as file:
        file.write(c)

print("Dots removed successfully.")
