html_content = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="utf-8" />
    <meta content="width=device-width, initial-scale=1.0" name="viewport" />
    <title>修改協助者權限 - AuraLink</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Be+Vietnam+Pro:wght@400;500;600;700&display=swap" rel="stylesheet" />
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
    <script id="tailwind-config">
        tailwind.config = {
            darkMode: "class",
            theme: {
                extend: {
                    colors: {
                        "primary": "#65518a",
                        "primary-container": "#d6beff",
                        "secondary": "#2f6275",
                        "secondary-container": "#b2e4fb",
                        "background": "#f7f6f3",
                        "surface": "#f7f6f3",
                        "on-surface": "#2e2f2d",
                        "on-surface-variant": "#5b5c5a",
                        "outline": "#767775",
                        "surface-container-lowest": "#ffffff",
                        "surface-container-low": "#f1f1ee",
                        "surface-container-high": "#e3e3df",
                        "surface-container-highest": "#ddddd9",
                        "error": "#b41340",
                    },
                    fontFamily: {
                        "headline": ["Plus Jakarta Sans"],
                        "body": ["Be Vietnam Pro"],
                        "label": ["Be Vietnam Pro"]
                    }
                }
            }
        };
    </script>
    <style>
        .material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; vertical-align: middle; }
        body { font-family: 'Be Vietnam Pro', sans-serif; background-color: #f7f6f3; color: #2e2f2d; overflow-x: hidden; }
        h1, h2, h3, .headline { font-family: 'Plus Jakarta Sans', sans-serif; }
    </style>
</head>
<body class="bg-surface text-on-surface min-h-screen pb-32">
    <!-- Header Section -->
    <header class="justify-between fixed top-0 w-full z-50 bg-[#f7f6f3]/70 backdrop-blur-md flex items-center px-6 h-16 w-full shadow-sm">
        <div class="flex items-center gap-3">
            <button onclick="window.history.back()" class="p-2 hover:bg-surface-container-low transition-colors active:scale-95 duration-200 rounded-full cursor-pointer">
                <span class="material-symbols-outlined text-primary">arrow_back</span>
            </button>
            <h1 class="font-headline font-semibold tracking-tight text-lg text-primary">修改協助者權限</h1>
        </div>
    </header>

    <!-- Main Content -->
    <main class="pt-24 px-4 mx-auto max-w-md md:max-w-2xl lg:max-w-3xl w-full">
        <form onsubmit="event.preventDefault(); window.location.href='userprofile.html';" class="space-y-6">
            
            <!-- Target Helper Info -->
            <div class="bg-primary/5 rounded-3xl p-6 flex items-center gap-4 border border-primary/10">
                <div class="w-14 h-14 bg-primary/10 text-primary rounded-full flex items-center justify-center font-bold text-xl shrink-0">
                    <span class="material-symbols-outlined text-[28px]">face</span>
                </div>
                <div class="flex flex-col">
                    <span class="text-sm font-bold text-on-surface-variant uppercase tracking-wider mb-1">正在設定權限給</span>
                    <span class="text-xl font-bold text-primary">張偉明 <span class="text-sm font-medium text-on-surface-variant ml-1">(爸爸)</span></span>
                </div>
            </div>

            <!-- Permissions Section -->
            <section class="bg-surface-container-lowest rounded-3xl p-6 shadow-sm border border-surface-container-high">
                <div class="flex items-center gap-2 mb-6">
                    <div class="w-10 h-10 bg-secondary/10 rounded-full flex items-center justify-center">
                        <span class="material-symbols-outlined text-secondary text-[20px]">vpn_key</span>
                    </div>
                    <h2 class="font-headline font-bold text-lg text-secondary">功能權限設定</h2>
                </div>

                <div class="space-y-6">
                    <!-- Feature 1: 小孩紀錄 -->
                    <div class="flex flex-col gap-3">
                        <label class="text-sm font-bold text-on-surface flex items-center gap-2">
                            <span class="material-symbols-outlined text-on-surface-variant text-[18px]">child_care</span>
                            小孩紀錄
                        </label>
                        <div class="flex bg-surface-container-low rounded-xl p-1 w-full relative">
                            <!-- 3 Segmented buttons -->
                            <button type="button" class="flex-1 py-2 text-xs font-bold rounded-lg transition-all text-on-surface-variant hover:bg-surface-container-high/50 cursor-pointer">關閉</button>
                            <button type="button" class="flex-1 py-2 text-xs font-bold rounded-lg transition-all text-on-surface-variant hover:bg-surface-container-high/50 cursor-pointer">檢視</button>
                            <button type="button" class="flex-1 py-2 text-xs font-bold rounded-lg transition-all bg-white text-primary shadow-sm border border-surface-container-highest cursor-pointer">修改</button>
                        </div>
                    </div>

                    <!-- Feature 2: 媽媽紀錄 -->
                    <div class="flex flex-col gap-3">
                        <label class="text-sm font-bold text-on-surface flex items-center gap-2">
                            <span class="material-symbols-outlined text-on-surface-variant text-[18px]">pregnant_woman</span>
                            媽媽紀錄
                        </label>
                        <div class="flex bg-surface-container-low rounded-xl p-1 w-full relative">
                            <button type="button" class="flex-1 py-2 text-xs font-bold rounded-lg transition-all text-on-surface-variant hover:bg-surface-container-high/50 cursor-pointer">關閉</button>
                            <button type="button" class="flex-1 py-2 text-xs font-bold rounded-lg transition-all bg-white text-primary shadow-sm border border-surface-container-highest cursor-pointer">檢視</button>
                            <button type="button" class="flex-1 py-2 text-xs font-bold rounded-lg transition-all text-on-surface-variant hover:bg-surface-container-high/50 cursor-pointer">修改</button>
                        </div>
                    </div>

                    <!-- Feature 3: 協助者清單 -->
                    <div class="flex flex-col gap-3">
                        <label class="text-sm font-bold text-on-surface flex items-center gap-2">
                            <span class="material-symbols-outlined text-on-surface-variant text-[18px]">group</span>
                            協助者清單
                        </label>
                        <div class="flex bg-surface-container-low rounded-xl p-1 w-full relative">
                            <button type="button" class="flex-1 py-2 text-xs font-bold rounded-lg transition-all bg-white text-primary shadow-sm border border-surface-container-highest cursor-pointer">關閉</button>
                            <button type="button" class="flex-1 py-2 text-xs font-bold rounded-lg transition-all text-on-surface-variant hover:bg-surface-container-high/50 cursor-pointer">檢視</button>
                            <button type="button" class="flex-1 py-2 text-xs font-bold rounded-lg transition-all text-on-surface-variant hover:bg-surface-container-high/50 cursor-pointer">修改</button>
                        </div>
                    </div>

                    <!-- Feature 4: 成長趨勢 -->
                    <div class="flex flex-col gap-3">
                        <label class="text-sm font-bold text-on-surface flex items-center gap-2">
                            <span class="material-symbols-outlined text-on-surface-variant text-[18px]">auto_graph</span>
                            成長趨勢
                        </label>
                        <div class="flex bg-surface-container-low rounded-xl p-1 w-full relative">
                            <button type="button" class="flex-1 py-2 text-xs font-bold rounded-lg transition-all text-on-surface-variant hover:bg-surface-container-high/50 cursor-pointer">關閉</button>
                            <button type="button" class="flex-1 py-2 text-xs font-bold rounded-lg transition-all bg-white text-primary shadow-sm border border-surface-container-highest cursor-pointer">檢視</button>
                            <button type="button" class="flex-1 py-2 text-xs font-bold rounded-lg transition-all text-on-surface-variant hover:bg-surface-container-high/50 cursor-pointer">修改</button>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Submit Button -->
            <button type="submit" class="w-full py-4 bg-primary text-white rounded-2xl font-headline font-bold text-base shadow-[0_10px_20px_rgba(101,81,138,0.2)] hover:scale-[1.02] active:scale-95 transition-all mt-6 cursor-pointer flex items-center justify-center gap-2">
                <span class="material-symbols-outlined text-xl">check_circle</span>
                儲存權限
            </button>
        </form>
    </main>
    
    <!-- Script for handling segmented control clicks -->
    <script>
        document.querySelectorAll('.bg-surface-container-low.rounded-xl').forEach(group => {
            const buttons = group.querySelectorAll('button');
            buttons.forEach(btn => {
                btn.addEventListener('click', () => {
                    // Reset all buttons in group
                    buttons.forEach(b => {
                        b.classList.remove('bg-white', 'text-primary', 'shadow-sm', 'border', 'border-surface-container-highest');
                        b.classList.add('text-on-surface-variant', 'hover:bg-surface-container-high/50');
                    });
                    // Set active state for clicked button
                    btn.classList.add('bg-white', 'text-primary', 'shadow-sm', 'border', 'border-surface-container-highest');
                    btn.classList.remove('text-on-surface-variant', 'hover:bg-surface-container-high/50');
                });
            });
        });
    </script>
</body>
</html>"""

with open('edit_helper_permissions.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("Generated edit_helper_permissions.html")
