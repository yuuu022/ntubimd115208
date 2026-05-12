import re

files = ['home_mom.html', 'home_baby.html']

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
    except Exception as e:
        print(f'Error reading {f}: {e}')
        continue

    changed = False

    # 1. Update the toggle button ID and text
    content = content.replace(
        '<button class="w-full flex justify-center items-center gap-1 py-2 text-[10px] font-bold text-primary">\n                    <span>查看全部</span>',
        '<button id="checklist-toggle-btn" class="w-full flex justify-center items-center gap-1 py-2 text-[10px] font-bold text-primary">\n                    <span>查看更多</span>'
    )

    # 2. Update the static HTML item 6 to be in the extra container
    task_6_str = '''                            <!-- Task Item 6 -->
                            <div class="flex items-center gap-4">
                                <div class="w-6 h-6 rounded-md border-2 border-[#d6beff] shrink-0"></div>
                                <div class="flex-1 flex items-center gap-2">
                                    <p class="text-xs font-semibold text-on-surface">吃鈣片</p>
                                </div>
                                <span class="material-symbols-outlined text-outline-variant text-[18px]">medication</span>
                            </div>'''
    
    if task_6_str in content and '<div id="extra-checklist-items"' not in content:
        content = content.replace(task_6_str, f'''                            <div id="extra-checklist-items" class="hidden flex-col gap-4 mt-4">
{task_6_str}
                            </div>''')
        changed = True

    # 3. Update the JS logic
    js_old = '''                let completed = 0;
                let html = '';
                items.forEach(item => {
                    if (item.done) completed++;
                    const checkIconHtml = item.done ? 
                        `<div class="w-6 h-6 rounded-md bg-[#d6beff] flex items-center justify-center shrink-0">
                            <span class="material-symbols-outlined text-primary text-sm font-bold">check</span>
                        </div>` : 
                        `<div class="w-6 h-6 rounded-md border-2 border-[#d6beff] shrink-0"></div>`;
                    const textHtml = item.done ? 
                        `<p class="text-xs font-semibold text-on-surface/50 line-through">${item.text}</p>` : 
                        `<p class="text-xs font-semibold text-on-surface">${item.text}</p>`;

                    html += `
                        <div class="flex items-center gap-4">
                            ${checkIconHtml}
                            <div class="flex-1 flex items-center gap-2">
                                ${textHtml}
                            </div>
                            <span class="material-symbols-outlined text-outline-variant text-[18px]">${item.icon}</span>
                        </div>
                    `;
                });
                
                if (checklistContainer) {
                    checklistContainer.innerHTML = html;
                }'''
    
    if js_old in content:
        js_new = '''                let completed = 0;
                let htmlFirst5 = '';
                let htmlRest = '';
                items.forEach((item, index) => {
                    if (item.done) completed++;
                    const checkIconHtml = item.done ? 
                        `<div class="w-6 h-6 rounded-md bg-[#d6beff] flex items-center justify-center shrink-0">
                            <span class="material-symbols-outlined text-primary text-sm font-bold">check</span>
                        </div>` : 
                        `<div class="w-6 h-6 rounded-md border-2 border-[#d6beff] shrink-0"></div>`;
                    const textHtml = item.done ? 
                        `<p class="text-xs font-semibold text-on-surface/50 line-through">${item.text}</p>` : 
                        `<p class="text-xs font-semibold text-on-surface">${item.text}</p>`;

                    const itemHtml = `
                        <div class="flex items-center gap-4">
                            ${checkIconHtml}
                            <div class="flex-1 flex items-center gap-2">
                                ${textHtml}
                            </div>
                            <span class="material-symbols-outlined text-outline-variant text-[18px]">${item.icon}</span>
                        </div>
                    `;
                    if (index < 5) {
                        htmlFirst5 += itemHtml;
                    } else {
                        htmlRest += itemHtml;
                    }
                });
                
                let finalHtml = htmlFirst5;
                if (items.length > 5) {
                    finalHtml += `<div id="extra-checklist-items" class="hidden flex-col gap-4 mt-4">${htmlRest}</div>`;
                }

                const checkToggleBtn = document.getElementById('checklist-toggle-btn');
                if (checkToggleBtn) {
                    checkToggleBtn.classList.remove('hidden');
                    checkToggleBtn.classList.add('flex');
                    if (items.length <= 5) {
                        checkToggleBtn.classList.add('hidden');
                        checkToggleBtn.classList.remove('flex');
                    } else {
                        // Reset to default collapsed state when switching date
                        checkToggleBtn.querySelector('span:first-child').innerText = '查看更多';
                        checkToggleBtn.querySelector('.material-symbols-outlined').innerText = 'keyboard_arrow_down';
                    }
                }

                if (checklistContainer) {
                    checklistContainer.innerHTML = finalHtml;
                }'''
        content = content.replace(js_old, js_new)
        changed = True

    # 4. Insert the global toggle event listener
    event_listener_str = '''
        const clToggleBtn = document.getElementById('checklist-toggle-btn');
        if (clToggleBtn) {
            clToggleBtn.addEventListener('click', () => {
                const extraItems = document.getElementById('extra-checklist-items');
                if (extraItems) {
                    if (extraItems.classList.contains('hidden')) {
                        extraItems.classList.remove('hidden');
                        extraItems.classList.add('flex');
                        clToggleBtn.querySelector('span:first-child').innerText = '收起';
                        clToggleBtn.querySelector('.material-symbols-outlined').innerText = 'keyboard_arrow_up';
                    } else {
                        extraItems.classList.add('hidden');
                        extraItems.classList.remove('flex');
                        clToggleBtn.querySelector('span:first-child').innerText = '查看更多';
                        clToggleBtn.querySelector('.material-symbols-outlined').innerText = 'keyboard_arrow_down';
                    }
                }
            });
        }
'''
    if 'clToggleBtn.addEventListener' not in content:
        content = content.replace('dateBtns.forEach(btn => {', event_listener_str + '\n        dateBtns.forEach(btn => {')
        changed = True

    if changed:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f'Updated {f}')
