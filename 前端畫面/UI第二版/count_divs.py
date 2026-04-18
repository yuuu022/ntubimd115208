with open('home_baby.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

div_opened = 0
div_closed = 0

for i, line in enumerate(lines[361:457], 362):
    opened = line.count('<div')
    closed = line.count('</div')
    div_opened += opened
    div_closed += closed
    print(f"Line {i}: +{opened} -{closed} | Total: {div_opened} - {div_closed} = {div_opened - div_closed}")

print(f"END: Opened {div_opened}, Closed {div_closed}")
