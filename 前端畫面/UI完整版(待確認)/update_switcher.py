import os
import glob
import re

directory = r'c:\Users\user\Desktop\專題\UI\UI第二版'

simplified_switcher = """            <!-- Baby Switcher Button -->
            <button id="baby-switcher-btn" class="flex items-center gap-1.5 bg-primary/10 px-3 py-1.5 rounded-full hover:bg-primary/20 transition-colors cursor-pointer group">
                <div class="w-5 h-5 rounded-full bg-white flex items-center justify-center shrink-0 shadow-sm group-hover:scale-105 transition-transform">
                    <span class="material-symbols-outlined text-primary text-[14px]">face</span>
                </div>
                <span class="text-[13px] font-bold text-primary">小寶</span>
                <span class="material-symbols-outlined text-primary text-[18px]">swap_horiz</span>
            </button>
            <!-- Dropdown Menu -->
            <div id="baby-switcher-menu" class="absolute top-full right-0 mt-2 w-40 bg-white rounded-2xl shadow-xl border border-surface-container-high overflow-hidden opacity-0 pointer-events-none transition-all duration-200 z-50 transform origin-top-right scale-95">
                <div class="max-h-56 overflow-y-auto hide-scrollbar flex flex-col">
                    <button class="w-full text-left px-4 py-3 bg-primary/5 flex items-center justify-between border-b border-surface-container-highest cursor-pointer">
                        <span class="text-sm font-bold text-primary">小寶</span>
                        <span class="material-symbols-outlined text-primary text-[16px]">check</span>
                    </button>
                    <button class="w-full text-left px-4 py-3 hover:bg-primary/5 transition-colors flex items-center justify-between border-b border-surface-container-highest cursor-pointer">
                        <span class="text-sm font-bold text-on-surface">大寶</span>
                    </button>
                    <!-- New Links -->
                    <button onclick="window.location.href='add_pregnancy_baby.html'" class="w-full text-left px-4 py-3 hover:bg-primary/5 transition-colors flex items-center gap-2 cursor-pointer">
                        <span class="material-symbols-outlined text-[16px] text-primary">pregnant_woman</span>
                        <span class="text-[13px] font-bold text-primary">新增胎數與小孩</span>
                    </button>
                </div>
            </div>"""

changed = 0
for filepath in glob.glob(os.path.join(directory, '*.html')):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # The block starts with "<!-- Baby Switcher Button -->" and ends with the closing div of "<!-- Dropdown Menu -->"
    # We find "<!-- Baby Switcher Button -->" up to the second "</div>\n            </div>" or something similar.
    # A safer regex:
    pattern = r'<!-- Baby Switcher Button -->.*?<!-- Dropdown Menu -->.*?<div id="baby-switcher-menu".*?>.*?</div>\s*</div>'
    
    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(pattern, simplified_switcher, content, flags=re.DOTALL)
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Simplified switcher in {os.path.basename(filepath)}')
            changed += 1

print(f'Total {changed} files updated.')
