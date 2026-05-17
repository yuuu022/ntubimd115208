import os

files = [
    "pregnancyrecord.html",
    "pregnancyrecord_new copy.html",
    "babyinformation.html",
    "babyinformation_empty.html"
]

html_to_remove = """            <div class="p-4 border-t border-surface-container-high/50 flex justify-end gap-3 items-center shrink-0">
                <button type="button" id="close-month-picker" class="px-6 py-2 rounded-full font-bold text-on-surface-variant hover:bg-surface-container-low transition-colors cursor-pointer">
                    取消
                </button>
                <button type="button" id="confirm-month-picker" class="px-6 py-2 rounded-full font-bold bg-primary text-white shadow-lg shadow-primary/30 hover:scale-[1.02] active:scale-95 transition-all cursor-pointer">
                    確定
                </button>
            </div>"""

old_js_onclick = """                    btn.onclick = () => {
                        tempMonth = i;
                        renderMonthGrid();
                    };"""

new_js_onclick = """                    btn.onclick = () => {
                        tempMonth = i;
                        currentSelectedYear = tempYear;
                        currentSelectedMonth = tempMonth;
                        customDatePickerText.innerHTML = `${currentSelectedYear}年 ${currentSelectedMonth}月 <span class="material-symbols-outlined text-primary ml-1">keyboard_arrow_down</span>`;
                        
                        if (window.navigator && window.navigator.vibrate) {
                            window.navigator.vibrate(50);
                        }
                        
                        renderMonthGrid();
                        setTimeout(() => {
                            closeMonthPickerModal();
                        }, 150);
                    };"""

old_js_vars = """            const closeMonthPicker = document.getElementById('close-month-picker');
            const confirmMonthPicker = document.getElementById('confirm-month-picker');"""

old_js_listeners = """            closeMonthPicker.addEventListener('click', closeMonthPickerModal);
            monthPickerBackdrop.addEventListener('click', closeMonthPickerModal);
            
            confirmMonthPicker.addEventListener('click', () => {
                currentSelectedYear = tempYear;
                currentSelectedMonth = tempMonth;
                customDatePickerText.innerHTML = `${currentSelectedYear}年 ${currentSelectedMonth}月 <span class="material-symbols-outlined text-primary ml-1">keyboard_arrow_down</span>`;
                closeMonthPickerModal();
            });"""

new_js_listeners = """            monthPickerBackdrop.addEventListener('click', closeMonthPickerModal);"""

for file in files:
    if not os.path.exists(file):
        print(f"Skipping {file}, not found")
        continue

    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Remove buttons HTML
    content = content.replace(html_to_remove, "")
    
    # 2. Update onclick logic
    content = content.replace(old_js_onclick, new_js_onclick)
    
    # 3. Remove variables
    content = content.replace(old_js_vars, "")
    
    # 4. Remove old event listeners
    content = content.replace(old_js_listeners, new_js_listeners)

    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Updated {file}")
