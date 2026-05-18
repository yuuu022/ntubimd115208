import os
import glob

# HTML files that might need the dropdown
files = glob.glob('*.html')

dropdown_block = '''        <div class="flex items-center gap-3 relative">
            <!-- Baby Switcher Button -->
            <button id="baby-switcher-btn" class="flex items-center gap-1.5 bg-primary/10 px-3 py-1.5 rounded-full hover:bg-primary/20 transition-colors cursor-pointer">
                <div class="w-5 h-5 rounded-full bg-white flex items-center justify-center shrink-0 shadow-sm">
                    <span class="material-symbols-outlined text-primary text-[14px]">face</span>
                </div>
                <span class="text-sm font-bold text-primary">小寶</span>
                <span class="material-symbols-outlined text-primary text-[18px]">swap_horiz</span>
            </button>
            <!-- Dropdown Menu -->
            <div id="baby-switcher-menu" class="absolute top-full right-0 mt-2 w-44 bg-white rounded-2xl shadow-xl border border-surface-container-high overflow-hidden opacity-0 pointer-events-none transition-all duration-200 z-50 transform origin-top-right scale-95">
                <div class="max-h-48 overflow-y-auto hide-scrollbar">
                    <button class="w-full text-left px-4 py-3 hover:bg-primary/5 transition-colors flex items-center gap-3 group border-b border-surface-container-highest">
                        <div class="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white group-hover:scale-110 transition-transform shadow-sm">
                            <span class="material-symbols-outlined text-[16px]">child_care</span>
                        </div>
                        <div class="flex flex-col">
                            <span class="text-sm font-bold text-primary">小寶</span>
                            <span class="text-[10px] font-medium text-primary/80">孕期</span>
                        </div>
                        <span class="material-symbols-outlined text-primary text-sm ml-auto opacity-100">check</span>
                    </button>
                    <button class="w-full text-left px-4 py-3 hover:bg-primary/5 transition-colors flex items-center gap-3 group border-b border-surface-container-highest">
                        <div class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                            <span class="material-symbols-outlined text-[16px]">face</span>
                        </div>
                        <div class="flex flex-col">
                            <span class="text-sm font-bold text-on-surface">小寶</span>
                            <span class="text-[10px] font-medium text-on-surface-variant">出生後</span>
                        </div>
                        <span class="material-symbols-outlined text-primary text-sm ml-auto opacity-0">check</span>
                    </button>
                    <button class="w-full text-left px-4 py-3 hover:bg-primary/5 transition-colors flex items-center gap-3 group border-b border-surface-container-highest">
                        <div class="w-8 h-8 rounded-full bg-secondary/10 flex items-center justify-center text-secondary group-hover:scale-110 transition-transform">
                            <span class="material-symbols-outlined text-[16px]">child_care</span>
                        </div>
                        <div class="flex flex-col">
                            <span class="text-sm font-bold text-on-surface">大寶</span>
                            <span class="text-[10px] font-medium text-on-surface-variant">孕期</span>
                        </div>
                        <span class="material-symbols-outlined text-primary text-sm ml-auto opacity-0">check</span>
                    </button>
                    <button class="w-full text-left px-4 py-3 hover:bg-primary/5 transition-colors flex items-center gap-3 group">
                        <div class="w-8 h-8 rounded-full bg-secondary/10 flex items-center justify-center text-secondary group-hover:scale-110 transition-transform">
                            <span class="material-symbols-outlined text-[16px]">face_3</span>
                        </div>
                        <div class="flex flex-col">
                            <span class="text-sm font-bold text-on-surface">大寶</span>
                            <span class="text-[10px] font-medium text-on-surface-variant">出生後</span>
                        </div>
                        <span class="material-symbols-outlined text-primary text-sm ml-auto opacity-0">check</span>
                    </button>
                </div>
            </div>
        </div>
    </header>'''

script_block = '''    <!-- Baby Switcher Script -->
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const switcherBtn = document.getElementById('baby-switcher-btn');
            const switcherMenu = document.getElementById('baby-switcher-menu');
            
            if (switcherBtn && switcherMenu) {
                switcherBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const isOpen = !switcherMenu.classList.contains('opacity-0');
                    if (isOpen) {
                        switcherMenu.classList.add('opacity-0', 'pointer-events-none', 'scale-95');
                        switcherMenu.classList.remove('opacity-100', 'pointer-events-auto', 'scale-100');
                    } else {
                        switcherMenu.classList.remove('opacity-0', 'pointer-events-none', 'scale-95');
                        switcherMenu.classList.add('opacity-100', 'pointer-events-auto', 'scale-100');
                    }
                });

                document.addEventListener('click', (e) => {
                    if (!switcherBtn.contains(e.target) && !switcherMenu.contains(e.target)) {
                        switcherMenu.classList.add('opacity-0', 'pointer-events-none', 'scale-95');
                        switcherMenu.classList.remove('opacity-100', 'pointer-events-auto', 'scale-100');
                    }
                });
            }
        });
    </script>
</body>'''

import re

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
    except Exception as e:
        print(f"Could not read {f}: {e}")
        continue

    changed = False

    # Check if header needs rewriting to flex justify-between
    if 'id="baby-switcher-btn"' not in content:
        # Check if the header has inner div wrapping the back btn and title. Look at The Ethereal Nursery.html
        # or history.html
        if '</header>' in content:
            # We want to insert the dropdown block so we replace </header> with the dropdown_block
            # First ensure the header has justify-between.
            header_open_tag = content.find('<header')
            header_close_bracket = content.find('>', header_open_tag)
            inner_content_start = header_close_bracket + 1
            inner_content_end = content.find('</header>', header_open_tag)
            
            header_inner = content[inner_content_start:inner_content_end]
            header_str = content[header_open_tag:header_close_bracket+1]
            
            if "justify-between" not in header_str:
                new_header_str = header_str.replace('class="', 'class="justify-between ')
                content = content.replace(header_str, new_header_str)
            
            # Since some headers like in `history.html` and `The Ethereal Nursery.html` wrap the left items 
            # in `<div class="flex items-center w-full">`, we need to change it to `<div class="flex items-center gap-3">`
            # or remove the inline w-full to allow justify-between to work.
            content = content.replace('<div class="flex items-center w-full">', '<div class="flex items-center gap-3">')
            content = content.replace('<div class="flex items-center w-full mb-6">', '<div class="flex items-center gap-3 mb-6">')
            
            # Remove any extra <div class="flex items-center gap-3"> that might be floating
            content = content.replace('</header>', dropdown_block)
            changed = True

    if 'Baby Switcher Script' not in content:
        content = content.replace('</body>', script_block)
        changed = True

    if changed:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Updated {f}")
