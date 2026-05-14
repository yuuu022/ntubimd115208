import re

with open('The Ethereal Nursery_filled.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Inputs
text = text.replace('placeholder="體重 (kg)" type="number"', 'placeholder="體重 (kg)" type="number" value="62.5"')
text = text.replace('placeholder="身高 (cm)" type="number"', 'placeholder="身高 (cm)" type="number" value="160"')
text = text.replace('placeholder="FHR" type="number"', 'placeholder="FHR" type="number" value="140"')
text = text.replace('placeholder="120" type="number"', 'placeholder="120" type="number" value="110"')
text = text.replace('placeholder="80" type="number"', 'placeholder="80" type="number" value="70"')

# 2. Selects
text = text.replace('<option value="-">- (陰性)</option>', '<option value="-" selected>- (陰性)</option>')
text = text.replace('<option value="無">無水腫</option>', '<option value="無" selected>無水腫</option>')

# 3. Textarea
text = text.replace('placeholder="記錄下這幾天的感受、飲食或寶寶的胎動..."></textarea>', 'placeholder="記錄下這幾天的感受、飲食或寶寶的胎動...">今天感覺很棒！食慾不錯，但晚上頻尿稍微影響了睡眠。有感覺到寶寶在踢！</textarea>')

# 4. Save Button
text = text.replace('完成並儲存紀錄', '修改並更新紀錄')
text = text.replace('新增產檢紀錄', '產檢紀錄明細')

# 5. Image upload to selected state
upload_original = """<div
                    class="bg-secondary-container/10 border-2 border-dashed border-secondary-container rounded-xl p-6 flex flex-col items-center justify-center gap-2 group cursor-pointer hover:bg-secondary-container/20 transition-all aspect-video md:aspect-auto">
                    <span
                        class="material-symbols-outlined text-secondary text-3xl group-hover:scale-110 transition-transform">add_a_photo</span>
                    <p class="text-sm font-bold text-secondary">上傳超音波照</p>
                    <p class="text-[10px] text-secondary/60">點擊或拖曳檔案至此</p>
                </div>"""

upload_filled = """<div class="relative w-full h-full min-h-[150px] bg-secondary-container/20 rounded-xl overflow-hidden border-2 border-secondary-container mx-auto flex items-center justify-center group cursor-pointer">
                    <span class="material-symbols-outlined text-secondary text-5xl">ultrasound</span>
                    <div class="absolute inset-0 bg-black/40 flex flex-col items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity backdrop-blur-sm">
                        <span class="material-symbols-outlined text-white text-3xl">edit</span>
                        <p class="text-white text-xs font-bold mt-1">更換超音波照</p>
                    </div>
                </div>"""
text = text.replace(upload_original, upload_filled)

# 6. Active symptom "頻尿"
text = text.replace("""<button
                            class="px-6 py-3 bg-surface-container-low text-on-surface-variant rounded-full text-sm font-medium hover:bg-primary-container/30 transition-colors">頻尿</button>""",
                   """<button
                            class="px-6 py-3 bg-primary text-white rounded-full text-sm font-semibold flex items-center gap-2 shadow-md">
                            <span class="material-symbols-outlined text-sm">check</span>
                            頻尿
                        </button>""")

# 7. Active mood to "愉快"
# Deactivate "平靜"
text = text.replace("""<span
                                class="text-3xl bg-primary-container/30 w-14 h-14 flex items-center justify-center rounded-2xl border-2 border-primary transition-all shadow-sm">😌</span>
                            <span class="text-[11px] font-bold text-primary">平靜</span>""",
                   """<span
                                class="text-3xl bg-surface-container-low w-14 h-14 flex items-center justify-center rounded-2xl group-hover:bg-primary-container/20 transition-all border-2 border-transparent">😌</span>
                            <span
                                class="text-[11px] font-medium text-on-surface-variant group-hover:text-primary">平靜</span>""")
# Activate "愉快"
text = text.replace("""<span
                                class="text-3xl bg-surface-container-low w-14 h-14 flex items-center justify-center rounded-2xl group-hover:bg-primary-container/20 transition-all border-2 border-transparent">😊</span>
                            <span
                                class="text-[11px] font-medium text-on-surface-variant group-hover:text-primary">愉快</span>""",
                   """<span
                                class="text-3xl bg-primary-container/30 w-14 h-14 flex items-center justify-center rounded-2xl border-2 border-primary transition-all shadow-sm">😊</span>
                            <span class="text-[11px] font-bold text-primary">愉快</span>""")


with open('The Ethereal Nursery_filled.html', 'w', encoding='utf-8') as f:
    f.write(text)
print("Done")
