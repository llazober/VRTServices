import re

content = open('templates/dashboard.html', 'r', encoding='utf-8').read()
lines = content.splitlines()

open_stack = []
for idx, line in enumerate(lines[:1783]):
    # find all tags in order
    tags = re.findall(r'(<div[^>]*>|</div>)', line)
    for t in tags:
        if t.startswith('</div>'):
            if open_stack:
                open_stack.pop()
        else:
            open_stack.append((idx + 1, t[:60]))

print("OPEN DIV STACK AT LINE 1783:")
for lnum, tag in open_stack:
    print(f"Line {lnum}: {tag}")
