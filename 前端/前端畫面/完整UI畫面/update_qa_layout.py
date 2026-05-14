import re

with open('qa_conversation.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update body classes
html = re.sub(
    r'<body class="([^"]*)">',
    r'<body class="bg-background font-body text-on-surface h-[100dvh] overflow-hidden flex">',
    html
)

# 2. Update Sidebar classes
html = html.replace(
    '<aside id="history-sidebar" class="fixed inset-y-0 left-0 w-[280px] bg-surface-container-lowest shadow-2xl z-50 transform -translate-x-full transition-transform duration-300 flex flex-col">',
    '<aside id="history-sidebar" class="fixed md:relative inset-y-0 left-0 w-[280px] shrink-0 bg-surface-container-lowest md:shadow-none shadow-2xl z-50 transform -translate-x-full md:translate-x-0 md:ml-0 transition-all duration-300 flex flex-col border-r border-surface-container-highest/30">'
)

# 3. Create Main Wrapper & adjust TopAppBar
main_wrapper_start = '''
    <!-- Main Content Wrapper -->
    <div class="flex-grow flex flex-col min-w-0 h-full relative">
'''

# We need to wrap from nav TopAppBar to the end of main.
# Find TopAppBar
nav_start_idx = html.find('<!-- TopAppBar -->')
# We replace the top nav
old_nav = '''    <!-- TopAppBar -->
    <nav class="sticky top-0 z-30 bg-[#f7f6f3]/70 backdrop-blur-md rounded-b-[3rem] shadow-[0_20px_40px_rgba(46,47,45,0.06)] flex justify-between items-center px-6 py-4 w-full md:px-12 transition-all duration-500 md:px-8 lg:px-16 xl:px-32 2xl:px-64">
        <div class="flex items-center gap-3">
            <button id="hamburger-menu-btn"
                class="w-10 h-10 flex items-center justify-center text-[#65518a] hover:bg-primary/10 rounded-full transition-colors mr-2 cursor-pointer">
                <span class="material-symbols-outlined">menu</span>
            </button>
            <span class="material-symbols-outlined text-[#65518a] text-2xl" data-icon="child_care">child_care</span>
            <h1 class="text-xl font-bold text-[#65518a] font-['Plus_Jakarta_Sans'] tracking-tight">AuraLink</h1>
        </div>
    </nav>

    <!-- Sidebar Overlay Backdrop -->'''

new_nav = '''    <!-- Main Content Wrapper -->
    <div class="flex-grow flex flex-col min-w-0 h-full relative">
        <!-- TopAppBar -->
        <nav class="shrink-0 flex justify-between items-center px-4 py-3 md:px-6 bg-background z-20 border-b border-surface-container-highest/20">
            <div class="flex items-center gap-3">
                <button id="hamburger-menu-btn"
                    class="w-10 h-10 flex items-center justify-center text-[#65518a] hover:bg-primary/10 rounded-full transition-colors cursor-pointer">
                    <span class="material-symbols-outlined">menu</span>
                </button>
                <div class="flex items-center gap-2 px-2">
                    <span class="material-symbols-outlined text-[#65518a] text-2xl">child_care</span>
                    <h1 class="text-xl font-bold text-[#65518a] font-['Plus_Jakarta_Sans'] tracking-tight">AuraLink</h1>
                </div>
            </div>
            <!-- Add a right-side element if needed, or leave empty for balance -->
            <div></div>
        </nav>

        <!-- Sidebar Overlay Backdrop -->'''
html = html.replace(old_nav, new_nav)

# 4. Modify main content to be scrollable
old_main = '''    <!-- Main Canvas -->
    <main class="flex-grow flex flex-col mx-auto px-4 pt-6 pb-32 md:pb-56 gap-6 max-w-md md:max-w-none w-full transition-all duration-500 ease-in-out md:px-8 lg:px-16 xl:px-32 2xl:px-64">
        <!-- AI Chat Layout -->
        <div class="flex-grow flex flex-col gap-8">'''

new_main = '''    <!-- Main Canvas (Scrollable) -->
    <main class="flex-grow overflow-y-auto px-4 pt-6 pb-40 md:pb-32 hide-scrollbar flex flex-col items-center">
        <div class="w-full max-w-3xl flex flex-col gap-8">'''
html = html.replace(old_main, new_main)

# 5. Modify Input Area
old_input = '''        <!-- Input Area (Floating Interaction) -->
        <div class="fixed bottom-24 md:bottom-36 left-0 right-0 md:max-w-none mx-auto px-4 z-40 pointer-events-none transition-all duration-500">
            <div
                class="pointer-events-auto bg-surface-container-lowest/90 backdrop-blur-xl rounded-2xl p-3 shadow-[0_20px_40px_rgba(46,47,45,0.12)] flex items-center gap-3 border border-outline-variant/30">'''

new_input = '''        <!-- Input Area (Floating Interaction) -->
        </div> <!-- End of scrollable main messages max-w-3xl -->
    </main>
    <div class="absolute bottom-24 md:bottom-6 left-0 w-full px-4 md:px-8 flex justify-center z-10 pointer-events-none">
        <div class="w-full max-w-3xl pointer-events-auto bg-surface-container-lowest/90 backdrop-blur-xl rounded-2xl p-3 shadow-[0_20px_40px_rgba(46,47,45,0.12)] flex items-center gap-3 border border-outline-variant/30">'''
html = html.replace(old_input, new_input)

# Close the new flex-grow wrapper just before Bottom Navigation Bar
html = html.replace(
    '</main>\n    <!-- Bottom Navigation Bar -->',
    '    </div>\n    <!-- Bottom Navigation Bar -->\n    <!-- Bottom Navigation Bar -->'
)
# Since we replaced </main> manually in new_input, we need to be careful.
# Let's fix this: 
# The original code had </main> at the end. We already added </main> in new_input and replaced the old fixed input area.
# Wait, the old code had:
#         </div>
#     </main>
#     <!-- Bottom Navigation Bar -->

# Let's use regex to replace the old `</main>` and close the wrapper
html = re.sub(
    r'</main>\s*<!-- Bottom Navigation Bar -->',
    r'</div> <!-- End Main Content Wrapper -->\n    <!-- Bottom Navigation Bar -->',
    html
)

# 6. Make bottom nav hidden on md
html = html.replace(
    '<nav class="fixed bottom-0 left-0 w-full md:w-full flex justify-around items-center px-4 pb-6 pt-3 bg-[#f7f6f3]/80 backdrop-blur-xl z-50 rounded-t-[3rem] shadow-[0_-10px_40px_rgba(46,47,45,0.06)] md:bottom-0 md:rounded-none md:pt-4 md:pb-4 md:shadow-2xl md:border md:border-surface-container-high/50 transition-all duration-500 md:px-8 lg:px-16 xl:px-32 2xl:px-64">',
    '<nav class="md:hidden fixed bottom-0 left-0 w-full flex justify-around items-center px-4 pb-6 pt-3 bg-[#f7f6f3]/90 backdrop-blur-xl z-50 rounded-t-[3rem] shadow-[0_-10px_40px_rgba(46,47,45,0.06)] transition-all duration-500">'
)

# 7. Update script to handle desktop toggle
old_script = '''            function openSidebar() {
                sidebar.classList.remove('-translate-x-full');
                overlay.classList.remove('opacity-0', 'pointer-events-none');
                overlay.classList.add('opacity-100', 'pointer-events-auto');
                document.body.style.overflow = 'hidden'; // Prevent scrolling
            }

            function closeSidebar() {
                sidebar.classList.add('-translate-x-full');
                overlay.classList.remove('opacity-100', 'pointer-events-auto');
                overlay.classList.add('opacity-0', 'pointer-events-none');
                document.body.style.overflow = '';
            }

            if(hamburgerBtn) hamburgerBtn.addEventListener('click', openSidebar);
            if(closeBtn) closeBtn.addEventListener('click', closeSidebar);
            if(overlay) overlay.addEventListener('click', closeSidebar);'''

new_script = '''            function toggleSidebar() {
                if (window.innerWidth >= 768) {
                    // Desktop toggle
                    sidebar.classList.toggle('md:-ml-[280px]');
                } else {
                    // Mobile toggle
                    const isOpen = !sidebar.classList.contains('-translate-x-full');
                    if (isOpen) {
                        sidebar.classList.add('-translate-x-full');
                        overlay.classList.remove('opacity-100', 'pointer-events-auto');
                        overlay.classList.add('opacity-0', 'pointer-events-none');
                    } else {
                        sidebar.classList.remove('-translate-x-full');
                        overlay.classList.remove('opacity-0', 'pointer-events-none');
                        overlay.classList.add('opacity-100', 'pointer-events-auto');
                    }
                }
            }

            if(hamburgerBtn) hamburgerBtn.addEventListener('click', toggleSidebar);
            if(closeBtn) closeBtn.addEventListener('click', toggleSidebar);
            if(overlay) overlay.addEventListener('click', () => { if (window.innerWidth < 768) toggleSidebar(); });'''

html = html.replace(old_script, new_script)

with open('qa_conversation.html', 'w', encoding='utf-8') as f:
    f.write(html)
