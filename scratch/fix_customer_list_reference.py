import os

filepath = r"d:\VRTServices\templates\dashboard.html"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Global variable declaration fix
old_var_dec = "let currentCustomerRecords = [];"
new_var_dec = "let currentCustomerRecords = [];\n        let currentCustomerList = [];"

if old_var_dec in content:
    content = content.replace(old_var_dec, new_var_dec, 1)
    print("Added global currentCustomerList declaration!")

# 2. Sync inside fetchCustomerRecords
old_fetch_set = "currentCustomerRecords = data.customers || [];"
new_fetch_set = "currentCustomerRecords = data.customers || [];\n                currentCustomerList = currentCustomerRecords;"

if old_fetch_set in content:
    content = content.replace(old_fetch_set, new_fetch_set, 1)
    print("Updated fetchCustomerRecords to sync currentCustomerList!")

# 3. Replace all remaining currentCustomerList references with safer expressions
old_load = """        async function loadComplianceData() {
            if (currentCustomerList.length === 0 && typeof fetchCustomerRecords === 'function') {
                await fetchCustomerRecords();
            }"""

new_load = """        async function loadComplianceData() {
            if ((!currentCustomerRecords || currentCustomerRecords.length === 0) && typeof fetchCustomerRecords === 'function') {
                await fetchCustomerRecords();
            }
            currentCustomerList = currentCustomerRecords;"""

if old_load in content:
    content = content.replace(old_load, new_load)
    print("Updated loadComplianceData customer check!")

old_preset = """        async function openPresetComplianceModal(event, preselectedCid = null) {
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
        }"""

new_preset = """        async function openPresetComplianceModal(event, preselectedCid = null) {
            if (event && event.preventDefault) {
                event.preventDefault();
                event.stopPropagation();
            }
            try {
                if ((!currentCustomerRecords || currentCustomerRecords.length === 0) && typeof fetchCustomerRecords === 'function') {
                    await fetchCustomerRecords();
                }
                currentCustomerList = currentCustomerRecords || [];
                const modal = document.getElementById('presetComplianceModal');
                const select = document.getElementById('presetComplianceCustomerSelect');
                if (!modal || !select) return;

                select.innerHTML = '<option value="">Select Customer *</option>' + currentCustomerList.map(c => 
                    `<option value="${c.id}" ${preselectedCid && String(preselectedCid) === String(c.id) ? 'selected' : ''}>${c.legal_name} (${c.custumer_number || 'No ID'}) [${c.customer_type || 'Business'}]</option>`
                ).join('');

                modal.style.display = 'flex';
            } catch (err) {
                console.error('Error opening preset compliance modal:', err);
                alert('Error opening Preset Schedule modal: ' + err.message);
            }
        }"""

if old_preset in content:
    content = content.replace(old_preset, new_preset)
    print("Updated openPresetComplianceModal!")

old_pop = """        function populateComplianceModalDropdowns() {
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
        }"""

new_pop = """        function populateComplianceModalDropdowns() {
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
        }"""

if old_pop in content:
    content = content.replace(old_pop, new_pop)
    print("Updated populateComplianceModalDropdowns!")

old_create = """        async function openCreateComplianceModal(event) {
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
        }"""

new_create = """        async function openCreateComplianceModal(event) {
            if (event && event.preventDefault) {
                event.preventDefault();
                event.stopPropagation();
            }
            try {
                if ((!currentCustomerRecords || currentCustomerRecords.length === 0) && typeof fetchCustomerRecords === 'function') {
                    await fetchCustomerRecords();
                }
                currentCustomerList = currentCustomerRecords || [];
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
            } catch (err) {
                console.error('Error opening create compliance modal:', err);
                alert('Error opening New Deadline modal: ' + err.message);
            }
        }"""

if old_create in content:
    content = content.replace(old_create, new_create)
    print("Updated openCreateComplianceModal!")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Finished patching customer variables in dashboard.html.")
