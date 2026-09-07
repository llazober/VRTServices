import os

filepath = r"d:\VRTServices\templates\dashboard.html"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add sync checkbox in complianceModal HTML
old_taxprep_div = '''                    <div>
                        <label style="display: block; font-size: 0.75rem; font-weight: 700; color: #94a3b8; margin-bottom: 6px;">Assigned Tax Prep</label>
                        <select id="complianceModalTaxPrep" style="width: 100%; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); border-radius: 10px; padding: 9px 14px; font-size: 0.88rem; color: #fff; outline: none;"></select>
                    </div>'''

new_taxprep_div = '''                    <div>
                        <label style="display: block; font-size: 0.75rem; font-weight: 700; color: #94a3b8; margin-bottom: 6px;">Assigned Tax Prep</label>
                        <select id="complianceModalTaxPrep" style="width: 100%; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); border-radius: 10px; padding: 9px 14px; font-size: 0.88rem; color: #fff; outline: none;"></select>
                        <div style="margin-top: 6px; display: flex; align-items: center; gap: 6px;">
                            <input type="checkbox" id="complianceModalSyncCustomerTaxPrep" checked style="cursor: pointer; accent-color: #f59e0b;">
                            <label for="complianceModalSyncCustomerTaxPrep" style="font-size: 0.72rem; color: #cbd5e1; cursor: pointer;">
                                Sync to Customer record & all client deadlines
                            </label>
                        </div>
                    </div>'''

if old_taxprep_div in content:
    content = content.replace(old_taxprep_div, new_taxprep_div)
    print("Added Tax Prep sync checkbox to complianceModal HTML!")

# 2. Update saveComplianceEvent JS to include sync_customer_tax_prep
old_save_comp = '''                        assigned_tax_prep: taxPrep,
                        description: desc'''

new_save_comp = '''                        assigned_tax_prep: taxPrep,
                        sync_customer_tax_prep: document.getElementById('complianceModalSyncCustomerTaxPrep')?.checked || false,
                        description: desc'''

if old_save_comp in content:
    content = content.replace(old_save_comp, new_save_comp)
    print("Updated saveComplianceEvent JS to include sync_customer_tax_prep!")

# 3. Update saveCustomerRecord to refresh compliance data
old_save_cust = '''                    if (typeof populateCustomerDropdownForMappings === 'function') await populateCustomerDropdownForMappings();'''

new_save_cust = '''                    if (typeof populateCustomerDropdownForMappings === 'function') await populateCustomerDropdownForMappings();
                    if (typeof loadComplianceData === 'function') await loadComplianceData();'''

if old_save_cust in content:
    content = content.replace(old_save_cust, new_save_cust)
    print("Updated saveCustomerRecord JS to call loadComplianceData!")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Frontend tax prep sync patch complete.")
