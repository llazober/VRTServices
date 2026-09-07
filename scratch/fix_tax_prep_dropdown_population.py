import os

filepath = r"d:\VRTServices\templates\dashboard.html"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update loadComplianceData to fetch tax team members if list is empty
old_load = '''        async function loadComplianceData() {
            if ((!currentCustomerRecords || currentCustomerRecords.length === 0) && typeof fetchCustomerRecords === 'function') {
                await fetchCustomerRecords();
            }
            currentCustomerList = currentCustomerRecords;
            populateComplianceModalDropdowns();'''

new_load = '''        async function loadComplianceData() {
            if ((!currentCustomerRecords || currentCustomerRecords.length === 0) && typeof fetchCustomerRecords === 'function') {
                await fetchCustomerRecords();
            }
            if ((!currentTaxTeamList || currentTaxTeamList.length === 0) && typeof fetchTaxTeamMembers === 'function') {
                await fetchTaxTeamMembers();
            }
            currentCustomerList = currentCustomerRecords;
            populateComplianceModalDropdowns();'''

if old_load in content:
    content = content.replace(old_load, new_load)
    print("Updated loadComplianceData to await fetchTaxTeamMembers!")

# 2. Update populateComplianceModalDropdowns to properly build Tax Prep options
old_pop = '''        function populateComplianceModalDropdowns() {
            const custSelect = document.getElementById('complianceModalCustomer');
            const taxPrepSelect = document.getElementById('complianceModalTaxPrep');
            const filterCust = document.getElementById('complianceFilterCustomer');
            const filterTaxPrep = document.getElementById('complianceFilterTaxPrep');

            const custs = (typeof currentCustomerRecords !== 'undefined' && currentCustomerRecords.length > 0) 
                ? currentCustomerRecords 
                : (currentCustomerList || []);
            const taxTeam = currentTaxTeamList || [];

            if (custSelect) {
                custSelect.innerHTML = `<option value="">Select Customer *</option>` + custs.map(c => `<option value="${c.id}">${c.legal_name} (${c.custumer_number || ''})</option>`).join('');
            }
            if (filterCust) {
                filterCust.innerHTML = `<option value="all">All Customers</option>` + custs.map(c => `<option value="${c.id}">${c.legal_name}</option>`).join('');
            }
            if (taxPrepSelect) {
                taxPrepSelect.innerHTML = `<option value="">-- Unassigned --</option>` + taxTeam.map(t => `<option value="${t.name}">${t.name}</option>`).join('');
            }
            if (filterTaxPrep) {
                filterTaxPrep.innerHTML = `<option value="all">All Tax Preps</option>` + taxTeam.map(t => `<option value="${t.name}">${t.name}</option>`).join('');
            }
        }'''

new_pop = '''        function populateComplianceModalDropdowns() {
            const custSelect = document.getElementById('complianceModalCustomer');
            const taxPrepSelect = document.getElementById('complianceModalTaxPrep');
            const filterCust = document.getElementById('complianceFilterCustomer');
            const filterTaxPrep = document.getElementById('complianceFilterTaxPrep');

            const custs = (typeof currentCustomerRecords !== 'undefined' && currentCustomerRecords.length > 0) 
                ? currentCustomerRecords 
                : (currentCustomerList || []);
            const taxTeam = (typeof currentTaxTeamList !== 'undefined') ? currentTaxTeamList : [];

            if (custSelect) {
                const cur = custSelect.value;
                custSelect.innerHTML = `<option value="">Select Customer *</option>` + custs.map(c => `<option value="${c.id}">${c.legal_name} (${c.custumer_number || ''})</option>`).join('');
                if (cur) custSelect.value = cur;
            }
            if (filterCust) {
                const cur = filterCust.value;
                filterCust.innerHTML = `<option value="all">All Customers</option>` + custs.map(c => `<option value="${c.id}">${c.legal_name}</option>`).join('');
                if (cur) filterCust.value = cur;
            }
            if (taxPrepSelect) {
                const cur = taxPrepSelect.value;
                taxPrepSelect.innerHTML = `<option value="">-- Unassigned --</option>` + taxTeam.map(t => `<option value="${t.name}">${t.name}</option>`).join('');
                if (cur) taxPrepSelect.value = cur;
            }
            if (filterTaxPrep) {
                const cur = filterTaxPrep.value;
                let taxPrepFilterHtml = `<option value="all">All Tax Preps</option><option value="unassigned">-- Unassigned --</option>`;
                taxTeam.forEach(t => {
                    taxPrepFilterHtml += `<option value="${t.name}">${t.name}</option>`;
                });
                filterTaxPrep.innerHTML = taxPrepFilterHtml;
                if (cur) filterTaxPrep.value = cur;
            }
        }'''

if old_pop in content:
    content = content.replace(old_pop, new_pop)
    print("Updated populateComplianceModalDropdowns successfully!")

# 3. Update populateCustomerTaxPrepDropdowns to also call populateComplianceModalDropdowns
old_pop_cust = '''        function populateCustomerTaxPrepDropdowns() {
            const ids = ['customerPageFormAssignedUserId', 'customerFormAssignedUserId'];
            ids.forEach(id => {
                const select = document.getElementById(id);
                if (!select) return;
                const currentVal = select.value || '';
                let html = `<option value="">-- Unassigned --</option>`;
                currentTaxTeamList.forEach(m => {
                    const valEscaped = m.name.replace(/"/g, '&quot;');
                    html += `<option value="${valEscaped}">${m.name}</option>`;
                });
                select.innerHTML = html;
                if (currentVal) select.value = currentVal;
            });
        }'''

new_pop_cust = '''        function populateCustomerTaxPrepDropdowns() {
            const ids = ['customerPageFormAssignedUserId', 'customerFormAssignedUserId'];
            ids.forEach(id => {
                const select = document.getElementById(id);
                if (!select) return;
                const currentVal = select.value || '';
                let html = `<option value="">-- Unassigned --</option>`;
                currentTaxTeamList.forEach(m => {
                    const valEscaped = m.name.replace(/"/g, '&quot;');
                    html += `<option value="${valEscaped}">${m.name}</option>`;
                });
                select.innerHTML = html;
                if (currentVal) select.value = currentVal;
            });
            if (typeof populateComplianceModalDropdowns === 'function') {
                populateComplianceModalDropdowns();
            }
        }'''

if old_pop_cust in content:
    content = content.replace(old_pop_cust, new_pop_cust)
    print("Updated populateCustomerTaxPrepDropdowns successfully!")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Tax prep dropdown patch complete.")
