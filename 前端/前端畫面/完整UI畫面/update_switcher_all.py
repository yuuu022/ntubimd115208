import re
import os
import glob

directory = r'c:\Users\user\Desktop\專題\UI\UI第二版'

new_menu = """            <!-- Dropdown Menu -->
            <div id="baby-switcher-menu" class="absolute top-full right-0 mt-2 w-56 bg-white rounded-2xl shadow-xl border border-surface-container-high overflow-hidden opacity-0 pointer-events-none transition-all duration-200 z-50 transform origin-top-right scale-95">
                <div class="max-h-56 overflow-y-auto hide-scrollbar flex flex-col">
                    <div class="w-full text-left px-4 py-3 bg-primary/5 flex items-center justify-between border-b border-surface-container-highest group">
                        <div class="flex items-center gap-2 cursor-pointer flex-1" onclick="window.location.reload()">
                            <span class="text-sm font-bold text-primary">小寶</span>
                            <span class="material-symbols-outlined text-primary text-[16px]">check</span>
                        </div>
                        <div class="flex items-center gap-1 opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity">
                            <button onclick="window.location.href='edit_baby_profile.html'" class="p-1 hover:bg-primary/10 rounded text-primary transition-colors cursor-pointer" title="編輯">
                                <span class="material-symbols-outlined text-[14px]">edit</span>
                            </button>
                            <button onclick="alert('確定要刪除嗎？')" class="p-1 hover:bg-error/10 rounded text-error transition-colors cursor-pointer" title="刪除">
                                <span class="material-symbols-outlined text-[14px]">delete</span>
                            </button>
                        </div>
                    </div>
                    <div class="w-full text-left px-4 py-3 hover:bg-primary/5 transition-colors flex items-center justify-between border-b border-surface-container-highest group">
                        <div class="flex items-center gap-2 cursor-pointer flex-1" onclick="window.location.reload()">
                            <span class="text-sm font-bold text-on-surface">大寶</span>
                        </div>
                        <div class="flex items-center gap-1 opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity">
                            <button onclick="window.location.href='edit_baby_profile.html'" class="p-1 hover:bg-primary/10 rounded text-primary transition-colors cursor-pointer" title="編輯">
                                <span class="material-symbols-outlined text-[14px]">edit</span>
                            </button>
                            <button onclick="alert('確定要刪除嗎？')" class="p-1 hover:bg-error/10 rounded text-error transition-colors cursor-pointer" title="刪除">
                                <span class="material-symbols-outlined text-[14px]">delete</span>
                            </button>
                        </div>
                    </div>
                    <!-- New Links -->
                    <button onclick="window.location.href='add_pregnancy_baby.html'" class="w-full text-left px-4 py-3 hover:bg-primary/5 transition-colors flex items-center gap-2 cursor-pointer">
                        <span class="material-symbols-outlined text-[16px] text-primary">pregnant_woman</span>
                        <span class="text-[13px] font-bold text-primary">新增胎數與小孩</span>
                    </button>
                </div>
            </div>"""

pattern = r'<!-- Dropdown Menu -->\s*<div id="baby-switcher-menu".*?</div>\s*</div>'

for filepath in glob.glob(os.path.join(directory, '*.html')):
    if 'index.html' in filepath or 'home_baby.html' in filepath:
        continue # Already updated

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'id="baby-switcher-menu"' in content:
        # Some files might not have <!-- Dropdown Menu --> comment, so we match more loosely
        pattern2 = r'<div id="baby-switcher-menu".*?</div>\s*</div>'
        new_menu_no_comment = new_menu.replace('            <!-- Dropdown Menu -->\n', '')
        
        if '<!-- Dropdown Menu -->' in content:
            new_content = re.sub(pattern, new_menu, content, flags=re.DOTALL)
        else:
            new_content = re.sub(pattern2, new_menu_no_comment, content, flags=re.DOTALL)
            
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Updated {filepath}')
