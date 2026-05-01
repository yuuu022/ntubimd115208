import os

def update_labels(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define replacements
    replacements = [
        # Weight
        (
            '<div class="relative">\n                            <input\n                                class="w-full bg-surface-container-low border-none rounded-md px-4 py-4 text-primary focus:ring-2 focus:ring-primary-container transition-all"\n                                placeholder="體重 (kg)"',
            '<div class="relative">\n                            <span class="text-[10px] text-on-surface-variant uppercase tracking-wider pl-1 block mb-1">體重 (kg)</span>\n                            <input\n                                class="w-full bg-surface-container-low border-none rounded-md px-4 py-4 text-primary focus:ring-2 focus:ring-primary-container transition-all"\n                                placeholder="0.0"'
        ),
        # Height
        (
            '<div class="relative">\n                            <input\n                                class="w-full bg-surface-container-low border-none rounded-md px-4 py-4 text-primary focus:ring-2 focus:ring-primary-container transition-all"\n                                placeholder="身高 (cm)"',
            '<div class="relative">\n                            <span class="text-[10px] text-on-surface-variant uppercase tracking-wider pl-1 block mb-1">身高 (cm)</span>\n                            <input\n                                class="w-full bg-surface-container-low border-none rounded-md px-4 py-4 text-primary focus:ring-2 focus:ring-primary-container transition-all"\n                                placeholder="0.0"'
        ),
        # FHR
        (
            '<div class="relative">\n                        <input\n                            class="w-full bg-surface-container-low border-none rounded-md px-4 py-4 text-primary focus:ring-2 focus:ring-primary-container transition-all"\n                            placeholder="FHR"',
            '<div class="relative">\n                        <span class="text-[10px] text-on-surface-variant uppercase tracking-wider pl-1 block mb-1">胎心率 (bpm)</span>\n                        <input\n                            class="w-full bg-surface-container-low border-none rounded-md px-4 py-4 text-primary focus:ring-2 focus:ring-primary-container transition-all"\n                            placeholder="140"'
        ),
        # Proteinuria
        (
            '<select\n                            class="w-full bg-surface-container-low border-none rounded-md px-4 py-4 text-on-surface-variant focus:ring-2 focus:ring-primary-container appearance-none">\n                            <option value="">蛋白尿 (Proteinuria)</option>',
            '<div>\n                            <span class="text-[10px] text-on-surface-variant uppercase tracking-wider pl-1 block mb-1">蛋白尿 (Proteinuria)</span>\n                            <select\n                                class="w-full bg-surface-container-low border-none rounded-md px-4 py-4 text-on-surface-variant focus:ring-2 focus:ring-primary-container appearance-none">'
        ),
        # Glycosuria
        (
            '<select\n                            class="w-full bg-surface-container-low border-none rounded-md px-4 py-4 text-on-surface-variant focus:ring-2 focus:ring-primary-container appearance-none">\n                            <option value="">尿糖 (Glycosuria)</option>',
            '<div>\n                            <span class="text-[10px] text-on-surface-variant uppercase tracking-wider pl-1 block mb-1">尿糖 (Glycosuria)</span>\n                            <select\n                                class="w-full bg-surface-container-low border-none rounded-md px-4 py-4 text-on-surface-variant focus:ring-2 focus:ring-primary-container appearance-none">'
        ),
        # Edema
        (
            '<select\n                            class="w-full bg-surface-container-low border-none rounded-md px-4 py-4 text-on-surface-variant focus:ring-2 focus:ring-primary-container appearance-none">\n                            <option value="">水腫狀況 (Edema)</option>',
            '<div>\n                            <span class="text-[10px] text-on-surface-variant uppercase tracking-wider pl-1 block mb-1">水腫狀況 (Edema)</span>\n                            <select\n                                class="w-full bg-surface-container-low border-none rounded-md px-4 py-4 text-on-surface-variant focus:ring-2 focus:ring-primary-container appearance-none">'
        )
    ]

    for old_str, new_str in replacements:
        if old_str in content:
            content = content.replace(old_str, new_str)
            # Need to close the <div> we added for selects
            if "<div>" in new_str:
                # Find the end of select and append </div>
                select_end = '</select>'
                # This could be tricky if there are multiple. 
                # Let's do a more robust approach.

    # Actually, a better robust approach for selects:
    # `multi_replace_file_content` block replacement since Python string manipulation for closing tags can be messy.
    pass

if __name__ == "__main__":
    update_labels("The Ethereal Nursery.html")
    update_labels("The Ethereal Nursery_filled.html")
