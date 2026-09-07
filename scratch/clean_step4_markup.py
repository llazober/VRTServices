import os

filepath = r"d:\VRTServices\templates\dashboard.html"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Replace step_accountant_reviewed_card back to simple clean structure identical to steps 1, 2, 3
old_card_code = '''                <!-- Step 4 -->
                <div id="step_accountant_reviewed_card" onclick="if(event.target.tagName !== 'INPUT') { const c = document.getElementById('step_accountant_reviewed'); c.checked = !c.checked; toggleChecklistStep('accountant_reviewed', c.checked); }" style="padding: 14px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); display: flex; align-items: center; justify-content: space-between; transition: all 0.2s; cursor: pointer;">
                    <div style="display: flex; align-items: center; gap: 14px;">
                        <input type="checkbox" id="step_accountant_reviewed" onchange="toggleChecklistStep('accountant_reviewed', this.checked)" onclick="event.stopPropagation()" style="width: 18px; height: 18px; accent-color: #00e676; cursor: pointer;">
                        <div>
                            <h4 style="font-size: 0.95rem; font-weight: 700; color: #f8fafc; margin: 0;">4. Accountant Reviewed & Reconciled</h4>
                            <p style="font-size: 0.73rem; color: #94a3b8; margin: 2px 0 0 0;">Final accountant review completed and ready for export to QBO/Accounting software</p>
                        </div>
                    </div>
                    <span style="font-size: 0.72rem; padding: 3px 10px; border-radius: 20px; font-weight: 700; background: rgba(0,230,118,0.15); color: #00e676; border: 1px solid rgba(0,230,118,0.3);">Step 4</span>
                </div>'''

new_card_code = '''                <!-- Step 4 -->
                <div id="step_accountant_reviewed_card" style="padding: 14px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); display: flex; align-items: center; justify-content: space-between; transition: all 0.2s;">
                    <div style="display: flex; align-items: center; gap: 14px;">
                        <input type="checkbox" id="step_accountant_reviewed" onchange="toggleChecklistStep('accountant_reviewed', this.checked)" style="width: 18px; height: 18px; accent-color: #00e676; cursor: pointer;">
                        <div>
                            <h4 style="font-size: 0.95rem; font-weight: 700; color: #f8fafc; margin: 0;">4. Accountant Reviewed & Reconciled</h4>
                            <p style="font-size: 0.73rem; color: #94a3b8; margin: 2px 0 0 0;">Final accountant review completed and ready for export to QBO/Accounting software</p>
                        </div>
                    </div>
                    <span style="font-size: 0.72rem; padding: 3px 10px; border-radius: 20px; font-weight: 700; background: rgba(0,230,118,0.15); color: #00e676; border: 1px solid rgba(0,230,118,0.3);">Step 4</span>
                </div>'''

if old_card_code in content:
    content = content.replace(old_card_code, new_card_code)
    print("Replaced step_accountant_reviewed_card HTML with clean standard markup!")
else:
    print("WARNING: Target card markup not found exact match!")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Clean step 4 markup complete.")
