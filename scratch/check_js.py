import re

with open(r'd:\VRTServices\templates\dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

script_blocks = []
in_script = False
script_start = 0
current_block = []

for idx, line in enumerate(lines, 1):
    if '<script' in line and not in_script:
        in_script = True
        script_start = idx
        current_block = []
    elif '</script>' in line and in_script:
        in_script = False
        script_blocks.append((script_start, idx, "".join(current_block)))
    elif in_script:
        current_block.append(line)

print(f"Found {len(script_blocks)} script blocks")

for start, end, content in script_blocks:
    open_b = content.count('{')
    close_b = content.count('}')
    open_p = content.count('(')
    close_p = content.count(')')
    print(f"Block L{start}-L{end}: Braces {{:{open_b}, }}:{close_b} | Parens (:{open_p}, ):{close_p}")
