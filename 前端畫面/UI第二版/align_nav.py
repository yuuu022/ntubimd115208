import re
import os
import glob

folder = r"c:\Users\user\Desktop\專題\UI\UI第二版"
files = glob.glob(os.path.join(folder, "*.html"))

def get_nav_html(active_key):
    items = [
        {"key": "home", "href": "home_mom.html", "icon": "home", "label": "首頁"},
        {"key": "record", "href": "pregnancyrecord.html", "icon": "edit_note", "label": "紀錄"},
        {"key": "growth", "href": "babyinformation.html", "icon": "auto_graph", "label": "成長"},
        {"key": "knowledge", "href": "qa_conversation.html", "icon": "menu_book", "label": "知識"},
        {"key": "profile", "href": "userprofile.html", "icon": "person", "label": "個人"},
    ]
    
    html = '<nav class="fixed bottom-0 left-0 w-full md:w-[600px] flex justify-around items-center px-4 pb-6 pt-3 bg-[#f7f6f3]/80 backdrop-blur-xl z-50 rounded-t-[3rem] shadow-[0_-20px_40px_rgba(46,47,45,0.06)] md:left-1/2 md:-translate-x-1/2 md:bottom-8 md:rounded-[2.5rem] md:pt-4 md:pb-4 md:shadow-2xl md:border md:border-surface-container-high/50 transition-all duration-500">\n'
    
    for item in items:
        if item["key"] == active_key:
            html += f'''        <a href="{item['href']}"
            class="flex flex-col items-center justify-center bg-[#d6beff] text-[#65518a] rounded-[1.5rem] px-5 py-2 scale-90 transition-transform duration-300">
            <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">{item['icon']}</span>
            <span class="font-['Be_Vietnam_Pro'] text-[10px] font-medium mt-1">{item['label']}</span>
        </a>\n'''
        else:
            html += f'''        <a href="{item['href']}"
            class="flex flex-col items-center justify-center text-[#5b5c5a] px-5 py-2 hover:text-[#65518a] transition-opacity cursor-pointer">
            <span class="material-symbols-outlined">{item['icon']}</span>
            <span class="font-['Be_Vietnam_Pro'] text-[10px] font-medium mt-1">{item['label']}</span>
        </a>\n'''
    html += '    </nav>'
    return html

page_map = {
    'home_mom.html': 'home',
    'home_baby.html': 'home',
    'history.html': 'home',
    'pregnancyrecord.html': 'record',
    'pregnancyrecord_new copy.html': 'record',
    'babyinformation.html': 'growth',
    'qa_conversation.html': 'knowledge',
    'userprofile.html': 'profile',
}

for filepath in files:
    filename = os.path.basename(filepath)
    if filename not in page_map:
        continue
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Replace nav bar identically across all files
    new_nav = get_nav_html(page_map[filename])
    content = re.sub(r'<nav\s+class="[^"]*fixed bottom-0[\s\S]*?</nav>', new_nav, content)
    
    # 2. Lift floating buttons
    content = re.sub(
        r'<div\s+class="([^"]*fixed[^"]*bottom-28[^"]+)"',
        lambda m: '<div class="' + m.group(1).replace('bottom-28', 'bottom-36') + '"',
        content
    )
    content = re.sub(
        r'<button\s+class="([^"]*fixed[^"]*bottom-32[^"]+)"',
        lambda m: '<button class="' + m.group(1).replace('bottom-32', 'bottom-36') + '"',
        content
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print(f"Alignment executed successfully!")
