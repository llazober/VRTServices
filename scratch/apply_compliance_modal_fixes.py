import os

filepath = r"d:\VRTServices\templates\dashboard.html"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update Header Buttons
old_buttons = '''                        <button onclick="promptGenerateCompliancePreset()" style="padding: 10px 16px; background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.4); color: #f59e0b; font-family: 'Outfit', sans-serif; font-size: 0.85rem; font-weight: 800; border-radius: 12px; cursor: pointer; transition: all 0.2s ease;" title="Manually generate statutory compliance deadlines for a client">
                            ⚡ Generate Preset Schedule
                        </button>
                        <button onclick="openCreateComplianceModal()" style="padding: 10px 20px; background: linear-gradient(135deg, #f59e0b, #d97706); color: #000; font-family: 'Outfit', sans-serif; font-size: 0.85rem; font-weight: 800; text-transform: uppercase; border: none; border-radius: 12px; cursor: pointer; box-shadow: 0 0 15px rgba(245, 158, 11, 0.35); transition: all 0.2s ease;">
                            ➕ New Deadline
                        </button>'''

new_buttons = '''                        <button type="button" onclick="openPresetComplianceModal(event)" style="padding: 10px 16px; background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.4); color: #f59e0b; font-family: 'Outfit', sans-serif; font-size: 0.85rem; font-weight: 800; border-radius: 12px; cursor: pointer; transition: all 0.2s ease;" title="Manually generate statutory compliance deadlines for a client">
                            ⚡ Generate Preset Schedule
                        </button>
                        <button type="button" onclick="openCreateComplianceModal(event)" style="padding: 10px 20px; background: linear-gradient(135deg, #f59e0b, #d97706); color: #000; font-family: 'Outfit', sans-serif; font-size: 0.85rem; font-weight: 800; text-transform: uppercase; border: none; border-radius: 12px; cursor: pointer; box-shadow: 0 0 15px rgba(245, 158, 11, 0.35); transition: all 0.2s ease;">
                            ➕ New Deadline
                        </button>'''

if old_buttons in content:
    content = content.replace(old_buttons, new_buttons)
    print("Replaced header buttons successfully!")
else:
    print("WARNING: Header buttons target block not found exact match!")

# 2. Replace promptGenerateCompliancePreset & openCreateComplianceModal JS
old_js = '''        async function promptGenerateCompliancePreset() {
            if (currentCustomerList.length === 0 && typeof fetchCustomerRecords === 'function') {
                await fetchCustomerRecords();
            }
            const selectedCid = prompt("Enter Customer ID to generate standard compliance deadlines for (or select from Customer Management):");
            if (!selectedCid) return;
            
            try {
                const res = await fetch(`/api/compliance/generate-preset/${selectedCid}`, { method: 'POST' });
                if (res.ok) {
                    const data = await res.json();
                    if (typeof showAlert === 'function') showAlert(`Generated ${data.count} standard statutory compliance deadlines!`, 'success', 'Schedule Generated');
                    else alert(`Generated ${data.count} compliance deadlines!`);
                    await loadComplianceData();
                } else {
                    const err = await res.json();
                    alert('Error: ' + (err.detail || 'Failed to generate schedule'));
                }
            } catch (err) {
                alert('Error generating preset: ' + err.message);
            }
        }

        function populateComplianceModalDropdowns() {
            const custSelect = document.getElementById('complianceModalCustomer');
            const taxPrepSelect = document.getElementById('complianceModalTaxPrep');
            const filterCust = document.getElementById('complianceFilterCustomer');
            const filterTaxPrep = document.getElementById('complianceFilterTaxPrep');

            if (custSelect) {
                custSelect.innerHTML = `<option value="">Select Customer *</option>` + currentCustomerList.map(c => `<option value="${c.id}">${c.legal_name} (${c.custumer_number || ''})</option>`).join('');
            }
            if (filterCust) {
                filterCust.innerHTML = `<option value="all">All Customers</option>` + currentCustomerList.map(c => `<option value="${c.id}">${c.legal_name}</option>`).join('');
            }
            if (taxPrepSelect) {
                taxPrepSelect.innerHTML = `<option value="">-- Unassigned --</option>` + currentTaxTeamList.map(t => `<option value="${t.name}">${t.name}</option>`).join('');
            }
            if (filterTaxPrep) {
                filterTaxPrep.innerHTML = `<option value="all">All Tax Preps</option>` + currentTaxTeamList.map(t => `<option value="${t.name}">${t.name}</option>`).join('');
            }
        }

        function openCreateComplianceModal() {
            const modal = document.getElementById('complianceModal');
            if (!modal) return;
            populateComplianceModalDropdowns();
            document.getElementById('complianceFormId').value = '';
            document.getElementById('complianceModalTitle').textContent = '➕ Create Compliance Deadline';
            document.getElementById('complianceModalTitleInput').value = '';
            document.getElementById('complianceModalCategory').value = 'Sales Tax';
            document.getElementById('complianceModalDueDate').value = new Date().toISOString().split('T')[0];
            document.getElementById('complianceModalJurisdiction').value = 'Federal';
            document.getElementById('complianceModalFrequency').value = 'One-Off';
            document.getElementById('complianceModalDesc').value = '';
            modal.style.display = 'flex';
        }'''

new_js = '''        async function openPresetComplianceModal(event, preselectedCid = null) {
            if (event && event.preventDefault) {
                event.preventDefault();
                event.stopPropagation();
            }
            if ((!currentCustomerList || currentCustomerList.length === 0) && typeof fetchCustomerRecords === 'function') {
                await fetchCustomerRecords();
            }
            const modal = document.getElementById('presetComplianceModal');
            const select = document.getElementById('presetComplianceCustomerSelect');
            if (!modal || !select) return;

            select.innerHTML = '<option value="">Select Customer *</option>' + (currentCustomerList || []).map(c => 
                `<option value="${c.id}" ${preselectedCid && String(preselectedCid) === String(c.id) ? 'selected' : ''}>${c.legal_name} (${c.custumer_number || 'No ID'}) [${c.customer_type || 'Business'}]</option>`
            ).join('');

            modal.style.display = 'flex';
        }

        function closePresetComplianceModal() {
            const modal = document.getElementById('presetComplianceModal');
            if (modal) modal.style.display = 'none';
        }

        async function submitPresetComplianceForm(event) {
            if (event && event.preventDefault) {
                event.preventDefault();
                event.stopPropagation();
            }
            const select = document.getElementById('presetComplianceCustomerSelect');
            const cid = select ? select.value : null;
            if (!cid) {
                alert('Please select a customer to generate standard compliance deadlines.');
                return;
            }

            try {
                const res = await fetch(`/api/compliance/generate-preset/${cid}`, { method: 'POST' });
                if (res.ok) {
                    const data = await res.json();
                    closePresetComplianceModal();
                    if (typeof showAlert === 'function') {
                        showAlert(`Generated ${data.count} statutory compliance deadlines!`, 'success', 'Schedule Generated');
                    } else {
                        alert(`Generated ${data.count} statutory compliance deadlines!`);
                    }
                    if (typeof loadComplianceData === 'function') {
                        await loadComplianceData();
                    }
                } else {
                    const err = await res.json();
                    alert('Error: ' + (err.detail || 'Failed to generate preset schedule'));
                }
            } catch (err) {
                alert('Error generating preset schedule: ' + err.message);
            }
        }

        function populateComplianceModalDropdowns() {
            const custSelect = document.getElementById('complianceModalCustomer');
            const taxPrepSelect = document.getElementById('complianceModalTaxPrep');
            const filterCust = document.getElementById('complianceFilterCustomer');
            const filterTaxPrep = document.getElementById('complianceFilterTaxPrep');

            if (custSelect) {
                custSelect.innerHTML = `<option value="">Select Customer *</option>` + currentCustomerList.map(c => `<option value="${c.id}">${c.legal_name} (${c.custumer_number || ''})</option>`).join('');
            }
            if (filterCust) {
                filterCust.innerHTML = `<option value="all">All Customers</option>` + currentCustomerList.map(c => `<option value="${c.id}">${c.legal_name}</option>`).join('');
            }
            if (taxPrepSelect) {
                taxPrepSelect.innerHTML = `<option value="">-- Unassigned --</option>` + currentTaxTeamList.map(t => `<option value="${t.name}">${t.name}</option>`).join('');
            }
            if (filterTaxPrep) {
                filterTaxPrep.innerHTML = `<option value="all">All Tax Preps</option>` + currentTaxTeamList.map(t => `<option value="${t.name}">${t.name}</option>`).join('');
            }
        }

        async function openCreateComplianceModal(event) {
            if (event && event.preventDefault) {
                event.preventDefault();
                event.stopPropagation();
            }
            if ((!currentCustomerList || currentCustomerList.length === 0) && typeof fetchCustomerRecords === 'function') {
                await fetchCustomerRecords();
            }
            const modal = document.getElementById('complianceModal');
            if (!modal) return;
            populateComplianceModalDropdowns();
            document.getElementById('complianceFormId').value = '';
            document.getElementById('complianceModalTitle').textContent = '➕ Create Compliance Deadline';
            document.getElementById('complianceModalTitleInput').value = '';
            document.getElementById('complianceModalCategory').value = 'Sales Tax';
            document.getElementById('complianceModalDueDate').value = new Date().toISOString().split('T')[0];
            document.getElementById('complianceModalJurisdiction').value = 'Federal';
            document.getElementById('complianceModalFrequency').value = 'One-Off';
            document.getElementById('complianceModalDesc').value = '';
            modal.style.display = 'flex';
        }'''

if old_js in content:
    content = content.replace(old_js, new_js)
    print("Replaced JS functions successfully!")
else:
    print("WARNING: JS functions target block not found exact match!")

# 3. Add Preset Compliance Modal HTML right before taxTeamModal
old_modal_anchor = '    <!-- ── TAX PREP TEAM MANAGEMENT MODAL ────────────────────────── -->'

preset_modal_html = '''    <!-- ── GENERATE PRESET COMPLIANCE SCHEDULE MODAL ─────────────────── -->
    <div id="presetComplianceModal" style="display: none; position: fixed; inset: 0; background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); z-index: 2000; justify-content: center; align-items: center; padding: 20px;">
        <div style="background: #0f172a; border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 20px; max-width: 520px; width: 100%; display: flex; flex-direction: column; box-shadow: 0 25px 60px rgba(0,0,0,0.9), 0 0 35px rgba(245, 158, 11, 0.2); color: #fff; overflow: hidden;">
            <div style="padding: 20px 24px; border-bottom: 1px solid rgba(255,255,255,0.1); display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.02);">
                <h3 style="font-family: 'Outfit', sans-serif; font-size: 1.25rem; font-weight: 800; color: #fff; margin: 0; display: flex; align-items: center; gap: 8px;">
                    ⚡ Generate Preset Compliance Schedule
                </h3>
                <button type="button" onclick="closePresetComplianceModal()" style="background: transparent; border: none; color: #94a3b8; cursor: pointer; padding: 4px; border-radius: 50%; font-size: 1.2rem;">✖</button>
            </div>
            <form onsubmit="submitPresetComplianceForm(event)" style="padding: 20px 24px; display: flex; flex-direction: column; gap: 16px;">
                <div>
                    <label style="display: block; font-size: 0.78rem; font-weight: 700; color: #94a3b8; margin-bottom: 8px;">Select Customer Record *</label>
                    <select id="presetComplianceCustomerSelect" required style="width: 100%; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); border-radius: 10px; padding: 11px 14px; font-size: 0.9rem; color: #fff; outline: none;"></select>
                </div>
                <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 12px; padding: 14px; font-size: 0.82rem; color: #cbd5e1; line-height: 1.5;">
                    <strong style="color: #f59e0b;">📅 Included Preset Deadlines:</strong>
                    <ul style="margin: 6px 0 0 18px; padding: 0;">
                        <li>Monthly Sales Tax Filings (20th of each month)</li>
                        <li>Quarterly Payroll Form 941 (Federal & State)</li>
                        <li>Quarterly Estimated Tax Deposits</li>
                        <li>Annual Corporate Return & 1099/W-2 Filings</li>
                        <li>Monthly Bookkeeping Close Cycles (15th of each month)</li>
                    </ul>
                </div>
                <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 10px;">
                    <button type="button" onclick="closePresetComplianceModal()" style="padding: 9px 18px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); color: #cbd5e1; font-weight: 700; border-radius: 10px; font-size: 0.85rem; cursor: pointer;">Cancel</button>
                    <button type="submit" style="padding: 9px 24px; background: linear-gradient(135deg, #f59e0b, #d97706); color: #000; font-weight: 800; font-size: 0.85rem; text-transform: uppercase; border: none; border-radius: 10px; cursor: pointer; box-shadow: 0 0 15px rgba(245, 158, 11, 0.35);">⚡ Generate Schedule</button>
                </div>
            </form>
        </div>
    </div>

'''

if old_modal_anchor in content:
    content = content.replace(old_modal_anchor, preset_modal_html + old_modal_anchor)
    print("Added Preset Modal HTML successfully!")
else:
    print("WARNING: Modal anchor target not found!")

# 4. Add TAX CAL button to Customer Table
old_row_btn = '''<button onclick="openCustomerChecklistModal(event, ${c.id}, null, '${(c.customer_type || c.type || 'Business').replace(/'/g, "\\'")}')" style="padding: 4px 8px; background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.35); color: #c084fc; border-radius: 6px; font-size: 0.68rem; font-weight: 700; text-transform: uppercase; cursor: pointer; margin-right: 4px;" title="View & Manage Workflow Checklist">📋 LIST</button>'''

new_row_btn = '''<button type="button" onclick="openPresetComplianceModal(event, ${c.id})" style="padding: 4px 8px; background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.35); color: #f59e0b; border-radius: 6px; font-size: 0.68rem; font-weight: 700; text-transform: uppercase; cursor: pointer; margin-right: 4px;" title="Generate Statutory Tax & Compliance Schedule">📅 TAX CAL</button>
                        <button onclick="openCustomerChecklistModal(event, ${c.id}, null, '${(c.customer_type || c.type || 'Business').replace(/'/g, "\\'")}')" style="padding: 4px 8px; background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.35); color: #c084fc; border-radius: 6px; font-size: 0.68rem; font-weight: 700; text-transform: uppercase; cursor: pointer; margin-right: 4px;" title="View & Manage Workflow Checklist">📋 LIST</button>'''

if old_row_btn in content:
    content = content.replace(old_row_btn, new_row_btn)
    print("Added TAX CAL button to Customer table successfully!")
else:
    print("WARNING: Customer table row button target not found!")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Dashboard.html patch completed.")
