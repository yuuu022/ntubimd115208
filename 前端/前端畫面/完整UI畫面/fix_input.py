import re

with open('qa_conversation.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Reduce Input Area size
html = html.replace(
    'rounded-2xl p-3 shadow-[0_20px_40px_rgba(46,47,45,0.12)] flex items-center gap-3',
    'rounded-2xl p-2 shadow-[0_20px_40px_rgba(46,47,45,0.12)] flex items-center gap-2'
)
html = html.replace(
    'font-medium py-3 px-2"',
    'text-sm font-medium py-2 px-2"'
)
html = html.replace(
    'w-12 h-12 bg-primary text-white rounded-xl',
    'w-9 h-9 bg-primary text-white rounded-lg'
)
html = html.replace(
    '<span class="material-symbols-outlined">send</span>',
    '<span class="material-symbols-outlined text-[20px]">send</span>'
)

# 2. Fix the scroll padding at the bottom.
html = html.replace('gap-8 pb-[280px]', 'gap-8')

spacer = '''                </div>
                <!-- Spacer to guarantee scroll clearance -->
                <div class="h-48 shrink-0 w-full md:h-64"></div>
            </div>
        </div>
        <!-- Input Area (Floating Interaction) -->'''

html = html.replace(
    '''                </div>
            </div>
        </div>
        <!-- Input Area (Floating Interaction) -->''',
    spacer
)

with open('qa_conversation.html', 'w', encoding='utf-8') as f:
    f.write(html)
