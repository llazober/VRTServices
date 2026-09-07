import re

content = open('templates/dashboard.html', 'r', encoding='utf-8').read()
lines = content.splitlines()

modal_ids = [
    'coaModal', 'mappingsModal', 'historyModal', 'supportModal',
    'customerModal', 'billingScheduleModal', 'billingInvoiceModal',
    'billingInvoiceViewModal', 'customAlertModal', 'customConfirmModal'
]

for m_id in modal_ids:
    print(f"\n--- TRACING MODAL: {m_id} ---")
    start_line = None
    for idx, line in enumerate(lines):
        if f'id="{m_id}"' in line:
            start_line = idx + 1
            break
    
    if not start_line:
        print(f"NOT FOUND: {m_id}")
        continue
    
    # Trace stack from start_line
    stack = []
    end_line = None
    for idx in range(start_line - 1, len(lines)):
        line = lines[idx]
        tags = re.findall(r'(<div[^>]*>|</div>)', line)
        for t in tags:
            if t.startswith('</div>'):
                if stack:
                    stack.pop()
                    if len(stack) == 0:
                        end_line = idx + 1
                        break
            else:
                stack.append(t[:40])
        if end_line:
            break
    
    print(f"Modal {m_id}: Starts Line {start_line}, Ends Line {end_line}")
