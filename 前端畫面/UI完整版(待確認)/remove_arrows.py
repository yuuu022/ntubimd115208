import os
import glob
import re

directory = r'c:\Users\user\Desktop\專題\UI\UI第二版'
changed = 0

for filepath in glob.glob(os.path.join(directory, '*.html')):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    
    # Remove swap_horiz from baby switchers globally
    content = re.sub(
        r'<span class="material-symbols-outlined text-primary text-\[18px\]">swap_horiz</span>\s*</button>',
        r'</button>',
        content
    )
    
    # Remove chevron_left and chevron_right around date navigation
    content = re.sub(
        r'<button\s+class="w-10 h-10 flex items-center justify-center rounded-full bg-surface-container-lowest text-primary hover:bg-primary-container transition-colors">\s*<span class="material-symbols-outlined">chevron_left</span>\s*</button>',
        r'',
        content
    )
    content = re.sub(
        r'<button\s+class="w-10 h-10 flex items-center justify-center rounded-full bg-surface-container-lowest text-primary hover:bg-primary-container transition-colors">\s*<span class="material-symbols-outlined">chevron_right</span>\s*</button>',
        r'',
        content
    )
    
    # Remove expand_more from year and month sliders
    content = re.sub(
        r'<span class="material-symbols-outlined absolute right-1 top-1/2 -translate-y-1/2 text-primary pointer-events-none text-\[18px\] group-hover/year:text-primary-dim transition-colors">expand_more</span>',
        r'',
        content
    )
    content = re.sub(
        r'<span class="material-symbols-outlined absolute right-1 top-1/2 -translate-y-1/2 text-primary pointer-events-none text-\[18px\] group-hover/month:text-primary-dim transition-colors">expand_more</span>',
        r'',
        content
    )

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Removed arrows from {os.path.basename(filepath)}')
        changed += 1

print(f'Total {changed} files updated.')
