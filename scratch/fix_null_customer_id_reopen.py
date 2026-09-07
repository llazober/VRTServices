import os

filepath = r"d:\VRTServices\templates\dashboard.html"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Ensure loadCustomerChecklist always sets currentChecklistCustomerId from data
old_load_cid = '''                currentChecklistPeriod = data.period;'''
new_load_cid = '''                if (data.customer_id) {
                    currentChecklistCustomerId = data.customer_id;
                }
                currentChecklistPeriod = data.period;'''

if old_load_cid in content:
    content = content.replace(old_load_cid, new_load_cid)
    print("Updated loadCustomerChecklist to always save currentChecklistCustomerId!")

# 2. Update reopenChecklistPeriod JS to resolve cid safely
old_reopen_js = '''        async function reopenChecklistPeriod(event) {
            if (event && event.preventDefault) {
                event.preventDefault();
                event.stopPropagation();
            }
            if (!currentChecklistCustomerId || !currentChecklistPeriod) return;

            let confirmed = false;
            if (typeof showCustomConfirm === 'function') {
                confirmed = await showCustomConfirm('Re-open this period as In Process to make corrections?', 'Re-open Period', 'Yes, Re-open', 'Cancel');
            } else {
                confirmed = confirm('Re-open this period as In Process to make corrections?');
            }
            if (!confirmed) return;

            try {
                const res = await fetch(`/api/customers/${currentChecklistCustomerId}/checklist/reopen`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ period: currentChecklistPeriod, workflow_mode: activeWorkflowTab })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Failed to reopen period');

                if (typeof showAlert === 'function') showAlert('↩️ Period re-opened as In Process!', 'success', 'Period Re-opened');
                else alert('↩️ Period re-opened as In Process!');

                await loadCustomerChecklist(currentChecklistCustomerId, currentChecklistPeriod);
                if (typeof loadComplianceData === 'function') await loadComplianceData();
            } catch (err) {
                alert(`❌ Reopen Error: ${err.message}`);
            }
        }'''

new_reopen_js = '''        async function reopenChecklistPeriod(event) {
            if (event && event.preventDefault) {
                event.preventDefault();
                event.stopPropagation();
            }
            const cid = (currentChecklistCustomerId && currentChecklistCustomerId !== 'null') 
                ? currentChecklistCustomerId 
                : (window.lastChecklistData?.customer_id || null);
            const period = currentChecklistPeriod || document.getElementById('checklistPeriodSelect')?.value;

            if (!cid || cid === 'null' || cid === 'undefined' || !period) {
                alert('❌ Cannot reopen: Customer ID or Period is missing.');
                return;
            }

            let confirmed = false;
            if (typeof showCustomConfirm === 'function') {
                confirmed = await showCustomConfirm('Re-open this period as In Process to make corrections?', 'Re-open Period', 'Yes, Re-open', 'Cancel');
            } else {
                confirmed = confirm('Re-open this period as In Process to make corrections?');
            }
            if (!confirmed) return;

            try {
                const res = await fetch(`/api/customers/${cid}/checklist/reopen`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ period: period, workflow_mode: activeWorkflowTab })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Failed to reopen period');

                if (data.customer_id) {
                    currentChecklistCustomerId = data.customer_id;
                }

                if (typeof showAlert === 'function') showAlert('↩️ Period re-opened as In Process!', 'success', 'Period Re-opened');
                else alert('↩️ Period re-opened as In Process!');

                await loadCustomerChecklist(cid, period);
                if (typeof loadComplianceData === 'function') await loadComplianceData();
            } catch (err) {
                alert(`❌ Reopen Error: ${err.message}`);
            }
        }'''

if old_reopen_js in content:
    content = content.replace(old_reopen_js, new_reopen_js)
    print("Updated reopenChecklistPeriod JS with cid fallback successfully!")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Null customer ID reopen patch complete.")
