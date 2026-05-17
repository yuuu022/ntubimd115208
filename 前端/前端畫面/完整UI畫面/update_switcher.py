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
            <div id="baby-switcher-menu" class="absolute top-full right-0 mt-2 w-64 bg-white rounded-2xl shadow-xl border border-surface-container-high overflow-hidden opacity-0 pointer-events-none transition-all duration-200 z-50 transform origin-top-right scale-95">
                <div class="max-h-[28rem] overflow-y-auto hide-scrollbar flex flex-col">
                    <div class="px-4 py-2 bg-surface-container-low/50 border-b border-surface-container-highest">
                        <span class="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">切換小孩 / 胎數</span>
                    </div>
                    
                    <!-- Baby Item 1 (Active) -->
                    <div class="w-full text-left px-4 py-3 bg-primary/5 flex items-center justify-between border-b border-surface-container-highest group">
                        <div class="flex items-center gap-3 cursor-pointer w-full" onclick="window.location.reload()">
                            <div class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                                <span class="material-symbols-outlined text-primary text-[18px]">face</span>
                            </div>
                            <div class="flex flex-col">
                                <span class="text-sm font-bold text-primary">小寶</span>
                                <span class="text-[10px] text-primary/70 font-medium">第二胎</span>
                            </div>
                        </div>
                    </div>

                    <!-- Baby Item 2 -->
                    <div class="w-full text-left px-4 py-3 hover:bg-surface-container-low transition-colors flex items-center justify-between border-b border-surface-container-highest group">
                        <div class="flex items-center gap-3 cursor-pointer w-full" onclick="window.location.reload()">
                            <div class="w-8 h-8 rounded-full bg-surface-container-high flex items-center justify-center shrink-0">
                                <span class="material-symbols-outlined text-on-surface-variant text-[18px]">face_6</span>
                            </div>
                            <div class="flex flex-col">
                                <span class="text-sm font-bold text-on-surface">大寶</span>
                                <span class="text-[10px] text-on-surface-variant font-medium">第一胎</span>
                            </div>
                        </div>
                    </div>

                    <!-- Pregnancy Item -->
                    <div class="w-full text-left px-4 py-3 hover:bg-surface-container-low transition-colors flex items-center justify-between border-b border-surface-container-highest group">
                        <div class="flex items-center gap-3 cursor-pointer w-full" onclick="window.location.reload()">
                            <div class="w-8 h-8 rounded-full bg-surface-container-high flex items-center justify-center shrink-0">
                                <span class="material-symbols-outlined text-on-surface-variant text-[18px]">pregnant_woman</span>
                            </div>
                            <div class="flex flex-col">
                                <span class="text-sm font-bold text-on-surface">第三胎</span>
                                <span class="text-[10px] text-on-surface-variant font-medium">懷孕中 (24w)</span>
                            </div>
                        </div>
                    </div>

                    <!-- New Actions -->
                    <div class="p-2 bg-surface-container-low/30">
                        <button onclick="window.location.href='manage_profiles.html'" class="w-full text-left px-3 py-2.5 hover:bg-primary/5 transition-colors flex items-center gap-3 rounded-xl cursor-pointer">
                            <span class="material-symbols-outlined text-[18px] text-primary">settings</span>
                            <span class="text-[13px] font-bold text-primary">管理所有胎數與寶寶</span>
                        </button>
                        <button onclick="window.location.href='add_pregnancy_baby.html'" class="w-full text-left px-3 py-2.5 hover:bg-primary/5 transition-colors flex items-center gap-3 rounded-xl cursor-pointer">
                            <span class="material-symbols-outlined text-[18px] text-primary">add_circle</span>
                            <span class="text-[13px] font-bold text-primary">新增胎數或小孩</span>
                        </button>
                    </div>
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
