import os
import glob
import re

directory = r'c:\Users\user\Desktop\專題\UI\UI第二版'

old_padding = "md:px-12 lg:px-[10vw] xl:px-[15vw] 2xl:px-[20vw]"
# New padding: gives breathing room but doesn't squish to the middle too much
new_padding = "md:px-8 lg:px-16 xl:px-32 2xl:px-64"

count = 0
for filepath in glob.glob(os.path.join(directory, '*.html')):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if old_padding in content:
        new_content = content.replace(old_padding, new_padding)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        count += 1

print(f"Updated padding for {count} files.")
