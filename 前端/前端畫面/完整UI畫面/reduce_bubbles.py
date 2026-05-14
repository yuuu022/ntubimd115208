import re

with open('qa_conversation.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Bubble paddings
old_html = html
html = re.sub(r'px-6 py-4', 'px-4 py-2.5', html)
print('Replaced px-6 py-4:', old_html != html)

# 2. Bubble roundings
old_html = html
html = re.sub(r'rounded-\[2rem\]', 'rounded-2xl', html)
print('Replaced rounded-[2rem]:', old_html != html)

# 3. Text size inside bubbles
old_html = html
html = re.sub(r'<p class="font-medium leading-relaxed">', '<p class="text-[13px] font-medium leading-relaxed">', html)
print('Replaced <p class...:', old_html != html)

# 4. Bento cards padding
old_html = html
html = re.sub(r'class="bg-surface-container-lowest p-6', 'class="bg-surface-container-lowest p-4', html)
print('Replaced Bento padding:', old_html != html)

# 5. Bento card text
old_html = html
html = re.sub(r'<h4 class="font-headline font-bold text-on-surface">', '<h4 class="font-headline font-bold text-sm text-on-surface">', html)
html = re.sub(r'<p class="text-sm text-on-surface-variant leading-relaxed">', '<p class="text-[12px] text-on-surface-variant leading-relaxed">', html)
print('Replaced Bento text:', old_html != html)

# 6. Suggestion chips
old_html = html
html = re.sub(r'px-4 py-2 rounded-full text-sm', 'px-3 py-1.5 rounded-full text-[11px]', html)
print('Replaced suggestion chips:', old_html != html)

with open('qa_conversation.html', 'w', encoding='utf-8') as f:
    f.write(html)
