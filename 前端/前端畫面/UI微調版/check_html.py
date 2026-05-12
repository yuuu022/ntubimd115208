from html.parser import HTMLParser

class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.void_elements = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def handle_starttag(self, tag, attrs):
        if tag not in self.void_elements:
            self.tags.append(tag)

    def handle_endtag(self, tag):
        if tag not in self.void_elements:
            if self.tags and self.tags[-1] == tag:
                self.tags.pop()
            else:
                print(f"Mismatched closing tag: </{tag}>. Expected: </{self.tags[-1] if self.tags else 'NONE'}>")

parser = MyHTMLParser()
with open(r'c:\Users\user\Desktop\專題\UI\UI第二版\home_baby.html', 'r', encoding='utf-8') as f:
    parser.feed(f.read())

if parser.tags:
    print(f"Unclosed tags remaining: {parser.tags}")
else:
    print("ALL TAGS PROPERLY CLOSED.")
