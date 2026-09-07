import re
import subprocess

content = open('templates/dashboard.html', 'r', encoding='utf-8').read()
scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)

clean_scripts = []
for i, s in enumerate(scripts):
    s_clean = re.sub(r'\{\{.*?\}\}', '"placeholder"', s)
    s_clean = re.sub(r'\{%.*?%\}', '/* jinja */', s_clean)
    clean_scripts.append(f"// --- SCRIPT {i} ---\n{s_clean}\n")

full_js = "\n".join(clean_scripts)
with open('scratch/temp_dashboard_clean.js', 'w', encoding='utf-8') as f:
    f.write(full_js)

res = subprocess.run(["node", "-c", "scratch/temp_dashboard_clean.js"], capture_output=True, text=True)
print("NODE RETURN CODE:", res.returncode)
print("NODE STDOUT:", res.stdout)
print("NODE STDERR:", res.stderr)
