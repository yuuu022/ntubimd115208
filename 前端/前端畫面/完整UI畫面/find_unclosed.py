from html.parser import HTMLParser

class LineParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.void_elements = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def handle_starttag(self, tag, attrs):
        if tag not in self.void_elements:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag not in self.void_elements:
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == tag:
                    unclosed = self.stack[i+1:]
                    if unclosed:
                        print(f"Warning: Tag <{tag}> at line {self.getpos()[0]} closed, but left these unclosed: {unclosed}")
                    self.stack = self.stack[:i]
                    break
            else:
                print(f"Error: Encountered </{tag}> at line {self.getpos()[0]} but no matching open tag.")

parser = LineParser()
with open('home_baby.html', 'r', encoding='utf-8') as f:
    parser.feed(f.read())

print("Final unclosed tags in stack:")
for tag, line in parser.stack:
    print(f"<{tag}> opened at line {line}")
