import os
import re

directory = r"c:\Users\user\Desktop\專題\UI\UI第二版"
files = [f for f in os.listdir(directory) if f.endswith('.html')]

for file in files:
    path = os.path.join(directory, file)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract the nav block
    nav_match = re.search(r'(<nav[^>]*bottom-0[^>]*>)(.*?)(</nav>)', content, re.DOTALL)
    if not nav_match:
        continue
    
    nav_inner = nav_match.group(2)
    
    # We find all top-level items in nav_inner. They are either <div...> or <a...>
    # We will use regex to find them. Since they just contain <span>s, non-greedy match works well.
    items = re.findall(r'(<(div|a)[^>]*>.*?</\2>)', nav_inner, re.DOTALL)
    
    new_nav_inner = nav_inner
    for item_tuple in items:
        item = item_tuple[0]
        tag = item_tuple[1] # 'div' or 'a'
        
        # Determine the link
        href = "#"
        if "首頁" in item:
            href = "home_mom.html"
        elif "紀錄" in item:
            href = "pregnancyrecord.html"
        elif "成長" in item:
            href = "babyinformation.html"
        elif "知識" in item:
            href = "qa_conversation.html"
        elif "個人" in item:
            href = "userprofile.html"
            
        # Transform <div ... > to <a href="..." ...>
        # Remove old href if any
        new_item = re.sub(r'\s+href="[^"]*"', '', item)
        
        # Replace opening tag
        if new_item.startswith('<div'):
            new_item = new_item.replace('<div', f'<a href="{href}"', 1)
            # Replace closing tag using absolute end match
            new_item = new_item[:new_item.rfind('</div>')] + '</a>' + new_item[new_item.rfind('</div>')+6:]
        elif new_item.startswith('<a'):
            new_item = new_item.replace('<a', f'<a href="{href}"', 1)
            # </a> is already correct
        
        new_nav_inner = new_nav_inner.replace(item, new_item)
        
    content = content.replace(nav_inner, new_nav_inner)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
        
print("Updated nav HTML files successfully.")
