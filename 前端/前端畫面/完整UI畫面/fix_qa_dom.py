import re

with open('qa_conversation.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Current order is:
# <body class="bg-background font-body text-on-surface h-[100dvh] overflow-hidden flex">
#     <!-- Main Content Wrapper -->
#     <div class="flex-grow flex flex-col min-w-0 h-full relative">
#         <!-- TopAppBar -->
#         <nav> ... </nav>
#
#         <!-- Sidebar Overlay Backdrop -->
#     <div id="sidebar-overlay"...></div>
#
#     <!-- Sidebar / Chat History Drawer -->
#     <aside id="history-sidebar"...> ... </aside>
#     <!-- Main Canvas (Scrollable) -->
#     <main> ... </main>
#     <div class="absolute bottom-24... input area"> ... </div>
#     </div> <!-- End Main Content Wrapper -->
#     <!-- Bottom Navigation Bar -->

# We need to extract the sidebar and overlay, and place them BEFORE the Main Content Wrapper.
# Let's extract the overlay and sidebar.
overlay_start = html.find('        <!-- Sidebar Overlay Backdrop -->')
sidebar_start = html.find('    <!-- Sidebar / Chat History Drawer -->')
main_start = html.find('    <!-- Main Canvas (Scrollable) -->')

# Extract the block from overlay_start to main_start
sidebar_block = html[overlay_start:main_start]

# Remove sidebar_block from its current position
html = html[:overlay_start] + html[main_start:]

# Now find where the Main Content Wrapper starts
wrapper_start = html.find('    <!-- Main Content Wrapper -->')

# Insert sidebar_block right before the wrapper
html = html[:wrapper_start] + sidebar_block.strip() + '\n' + html[wrapper_start:]

with open('qa_conversation.html', 'w', encoding='utf-8') as f:
    f.write(html)
