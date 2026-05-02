import html
import os
import re

def move_section(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract the Visual Record section
    # We use regex to grab from <!-- Visual Record --> to its closing </section>
    pattern_visual = r'(<!-- Visual Record -->\s*<section class="space-y-4">.*?</section>)'
    match = re.search(pattern_visual, content, re.DOTALL)
    if not match:
        print(f"Could not find Visual Record section in {file_path}")
        return
        
    visual_section = match.group(1)
    
    # Remove it from its original place
    content = content.replace(visual_section, '')
    
    # Extract the Official Check-up section to figure out where to insert
    pattern_official = r'(<!-- Official Check-up Toggle Section -->\s*<section.*?</section>)'
    match_off = re.search(pattern_official, content, re.DOTALL)
    if not match_off:
        print(f"Could not find Official section in {file_path}")
        return
        
    official_section = match_off.group(1)
    
    # Combine putting visual_section exactly below official_section
    new_combined = official_section + '\n        ' + visual_section
    
    content = content.replace(official_section, new_combined)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Successfully moved section in {file_path}")

if __name__ == "__main__":
    move_section("c:\\Users\\user\\Desktop\\專題\\UI\\UI第二版\\The Ethereal Nursery.html")
    move_section("c:\\Users\\user\\Desktop\\專題\\UI\\UI第二版\\The Ethereal Nursery_filled.html")
