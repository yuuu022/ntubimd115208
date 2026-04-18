import re

def find_mismatched(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    stack = []
    
    for i, line in enumerate(lines, 1):
        # Find all tags on the line
        tags = re.findall(r'<\s*(/?)\s*([a-zA-Z0-9]+)[^>]*>', line)
        for is_close, tag_name in tags:
            tag_name = tag_name.lower()
            if tag_name in ['img', 'br', 'hr', 'input', 'meta', 'link']:
                continue
                
            if not is_close:
                stack.append((tag_name, i))
            else:
                if not stack:
                    print(f"Error: Encountered </{tag_name}> at line {i} but stack is empty!")
                    continue
                    
                # Find matching open tag
                match_idx = -1
                for j in range(len(stack)-1, -1, -1):
                    if stack[j][0] == tag_name:
                        match_idx = j
                        break
                        
                if match_idx == -1:
                    print(f"Error: Encountered </{tag_name}> at line {i} but no opening tag found!")
                else:
                    unclosed = stack[match_idx+1:]
                    if unclosed:
                        print(f"Warning: </{tag_name}> at line {i} implicitly closed tags: {unclosed}")
                    stack = stack[:match_idx]
                    
    print("\nRemaining unclosed tags:")
    for tag, line in stack:
        print(f"<{tag}> opened at line {line}")

find_mismatched('home_baby.html')
