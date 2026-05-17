import re
import shutil

# Copy the file first
shutil.copy('add_baby_record.html', 'edit_baby_record.html')

with open('edit_baby_record.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Title and headers
content = content.replace('新增成長紀錄', '修改成長紀錄')

# 2. Prefill input values
content = re.sub(
    r'(<span class="text-\[10px\] font-bold text-on-surface-variant/80">身高 \(CM\)</span>\s*<input class=".*?" type="number" placeholder="0\.0")',
    r'\1 value="65.0"',
    content
)
content = re.sub(
    r'(<span class="text-\[10px\] font-bold text-on-surface-variant/80">體重 \(KG\)</span>\s*<input class=".*?" type="number" placeholder="0\.0")',
    r'\1 value="7.2"',
    content
)
content = re.sub(
    r'(<span class="text-\[10px\] font-bold text-on-surface-variant/80">頭圍 \(CM\)</span>\s*<input class=".*?" type="number" placeholder="0\.0")',
    r'\1 value="42.5"',
    content
)
content = re.sub(
    r'(<span class="text-\[10px\] font-bold text-on-surface-variant/80">胸圍 \(CM\)</span>\s*<input class=".*?" type="number" placeholder="0\.0")',
    r'\1 value="34.0"',
    content
)

# 3. Prefill textarea
content = content.replace(
    '</textarea>',
    '寶寶今天特別開心，會抓著小木馬玩很久！</textarea>'
)

# 4. Upload Area prefill
upload_area = """        <!-- Upload Area -->
        <div class="bg-surface-container-lowest border-2 border-primary-container rounded-[2rem] p-0 flex flex-col items-center justify-center gap-3 cursor-pointer hover:bg-primary/5 transition-all aspect-[4/3] md:aspect-video shadow-sm overflow-hidden relative group">
            <img src="https://lh3.googleusercontent.com/aida-public/AB6AXuAsFmTxE1jrirW8qMVp2ndiK0oWNDMTQsnAUPiRxPPGnM7ZPEB15HyG94PTXSO66mK-eVt_ZEgpWCGGXcvKrw8__Zv9F5sQ_k1f3y_2YFmJIZt4XP7lFWXyHLuUeAWP3NiaTRDFEhiTS3p1BHbvzrzxxqirT-nJnKBOwvZ0Udy3yHJRDNWrEIEt-CEQh_LSa5odUOxxP8h7tmwrNvhv-tijRUgdZj84sdWZUscx3oEi31W1dUmyPg4hSxXscuuUawfsKm0AU5JOlWmH" class="w-full h-full object-cover">
            <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2 text-white font-bold">
                <span class="material-symbols-outlined">edit</span> 更換照片
            </div>
        </div>"""
        
content = re.sub(
    r'<!-- Upload Area -->.*?<p class="text-sm font-bold text-on-surface-variant">點擊上傳成長照片</p>\s*</div>',
    upload_area,
    content,
    flags=re.DOTALL
)

with open('edit_baby_record.html', 'w', encoding='utf-8') as f:
    f.write(content)
