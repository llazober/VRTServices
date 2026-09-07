import sys

path = r'd:\VRTServices\templates\dashboard.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add DOMContentLoaded check & populateComplianceModalDropdowns
old_doc_loaded = "document.addEventListener('DOMContentLoaded', () => {\n            fetchTaxTeamMembers();"
new_doc_loaded = "document.addEventListener('DOMContentLoaded', () => {\n            fetchTaxTeamMembers();\n            if ('{{ active_tab }}' === 'compliance') {\n                loadComplianceData();\n            }"

content = content.replace(old_doc_loaded, new_doc_loaded)

# 2. Add Compliance JS logic right before closing </script> before </body>
js_logic = """
        // ── COMPLIANCE CALENDAR MODULE LOGIC ─────────────────────────────
        let complianceCurrentEvents = [];
        let complianceCurrentYear = new Date().getFullYear();
        let complianceCurrentMonth = new Date().getMonth() + 1;
        let complianceViewMode = 'calendar';

        async function loadComplianceData() {
            if (currentCustomerList.length === 0 && typeof fetchCustomerRecords === 'function') {
                await fetchCustomerRecords();
            }
            populateComplianceModalDropdowns();

            const customer = document.getElementById('complianceFilterCustomer')?.value || 'all';
            const category = document.getElementById('complianceFilterCategory')?.value || 'all';
            const status = document.getElementById('complianceFilterStatus')?.value || 'all';
            const taxPrep = document.getElementById('complianceFilterTaxPrep')?.value || 'all';
            const monthInput = document.getElementById('complianceFilterMonth')?.value;

            let year = complianceCurrentYear;
            let month = complianceCurrentMonth;

            if (monthInput) {
                const parts = monthInput.split('-');
                if (parts.length === 2) {
                    year = parseInt(parts[0]);
                    month = parseInt(parts[1]);
                    complianceCurrentYear = year;
                    complianceCurrentMonth = month;
                }
            } else {
                const formattedM = String(complianceCurrentMonth).padStart(2, '0');
                const monthEl = document.getElementById('complianceFilterMonth');
                if (monthEl) monthEl.value = `${complianceCurrentYear}-${formattedM}`;
            }

            const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
            const titleEl = document.getElementById('complianceCurrentMonthTitle');
            if (titleEl) titleEl.textContent = `${monthNames[complianceCurrentMonth - 1]} ${complianceCurrentYear}`;

            try {
                let url = `/api/compliance/events?customer_id=${customer}&category=${encodeURIComponent(category)}&status=${encodeURIComponent(status)}&assigned_tax_prep=${encodeURIComponent(taxPrep)}&year=${year}&month=${month}`;
                const res = await fetch(url);
                if (res.ok) {
                    const data = await res.json();
                    complianceCurrentEvents = data.events || [];
                    renderComplianceSummaryKPIs();
                    if (complianceViewMode === 'calendar') {
                        renderComplianceCalendarGrid();
                    } else {
                        renderComplianceTable();
                    }
                }
            } catch (err) {
                console.error('Error loading compliance events:', err);
            }
        }

        function setComplianceViewMode(mode) {
            complianceViewMode = mode;
            const gridContainer = document.getElementById('complianceCalendarContainer');
            const tableContainer = document.getElementById('complianceTableContainer');
            const btnCal = document.getElementById('complianceBtnViewCalendar');
            const btnTab = document.getElementById('complianceBtnViewTable');

            if (mode === 'calendar') {
                if (gridContainer) gridContainer.style.display = 'block';
                if (tableContainer) tableContainer.style.display = 'none';
                if (btnCal) { btnCal.style.background = 'rgba(245, 158, 11, 0.25)'; btnCal.style.color = '#f59e0b'; }
                if (btnTab) { btnTab.style.background = 'transparent'; btnTab.style.color = '#94a3b8'; }
                renderComplianceCalendarGrid();
            } else {
                if (gridContainer) gridContainer.style.display = 'none';
                if (tableContainer) tableContainer.style.display = 'block';
                if (btnCal) { btnCal.style.background = 'transparent'; btnCal.style.color = '#94a3b8'; }
                if (btnTab) { btnTab.style.background = 'rgba(245, 158, 11, 0.25)'; btnTab.style.color = '#f59e0b'; }
                renderComplianceTable();
            }
        }

        function changeComplianceMonth(delta) {
            complianceCurrentMonth += delta;
            if (complianceCurrentMonth > 12) {
                complianceCurrentMonth = 1;
                complianceCurrentYear += 1;
            } else if (complianceCurrentMonth < 1) {
                complianceCurrentMonth = 12;
                complianceCurrentYear -= 1;
            }
            const formattedM = String(complianceCurrentMonth).padStart(2, '0');
            const monthEl = document.getElementById('complianceFilterMonth');
            if (monthEl) monthEl.value = `${complianceCurrentYear}-${formattedM}`;
            loadComplianceData();
        }

        function renderComplianceSummaryKPIs() {
            const overdue = complianceCurrentEvents.filter(e => e.status === 'Overdue').length;
            const upcoming = complianceCurrentEvents.filter(e => e.status === 'Pending' || e.status === 'In Progress').length;
            const activeMonth = complianceCurrentEvents.length;
            const completed = complianceCurrentEvents.filter(e => e.status === 'Completed').length;
            const pct = activeMonth > 0 ? Math.round((completed / activeMonth) * 100) : 0;

            const elOver = document.getElementById('complianceKpiOverdue');
            const elUp = document.getElementById('complianceKpiUpcoming');
            const elActive = document.getElementById('complianceKpiActiveMonth');
            const elComp = document.getElementById('complianceKpiCompletedMetric');

            if (elOver) elOver.textContent = overdue;
            if (elUp) elUp.textContent = upcoming;
            if (elActive) elActive.textContent = activeMonth;
            if (elComp) elComp.textContent = `${pct}%`;
        }

        function getCategoryColorBadge(cat) {
            switch(cat) {
                case 'Sales Tax': return { bg: 'rgba(168, 85, 247, 0.2)', border: 'rgba(168, 85, 247, 0.5)', color: '#c084fc', icon: '📊' };
                case 'Payroll Tax': return { bg: 'rgba(56, 189, 248, 0.2)', border: 'rgba(56, 189, 248, 0.5)', color: '#38bdf8', icon: '💼' };
                case 'Estimated Tax': return { bg: 'rgba(245, 158, 11, 0.2)', border: 'rgba(245, 158, 11, 0.5)', color: '#facc15', icon: '🏛️' };
                case 'Corporate Tax': return { bg: 'rgba(239, 68, 68, 0.2)', border: 'rgba(239, 68, 68, 0.5)', color: '#f87171', icon: '📑' };
                case '1099/W2': return { bg: 'rgba(236, 72, 153, 0.2)', border: 'rgba(236, 72, 153, 0.5)', color: '#f472b6', icon: '✉️' };
                case 'Franchise Tax': return { bg: 'rgba(14, 165, 233, 0.2)', border: 'rgba(14, 165, 233, 0.5)', color: '#38bdf8', icon: '🏢' };
                case 'Bookkeeping Close': return { bg: 'rgba(34, 197, 94, 0.2)', border: 'rgba(34, 197, 94, 0.5)', color: '#4ade80', icon: '📈' };
                default: return { bg: 'rgba(148, 163, 184, 0.2)', border: 'rgba(148, 163, 184, 0.5)', color: '#cbd5e1', icon: '📌' };
            }
        }

        function renderComplianceCalendarGrid() {
            const gridDaysEl = document.getElementById('complianceGridDays');
            if (!gridDaysEl) return;

            const year = complianceCurrentYear;
            const month = complianceCurrentMonth;
            const firstDayIndex = new Date(year, month - 1, 1).getDay();
            const daysInMonth = new Date(year, month, 0).getDate();

            let html = '';

            for (let i = 0; i < firstDayIndex; i++) {
                html += `<div style="background: rgba(0,0,0,0.2); min-height: 110px; border-bottom: 1px solid var(--border-color);"></div>`;
            }

            const today = new Date();
            for (let day = 1; day <= daysInMonth; day++) {
                const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                const isToday = (today.getFullYear() === year && (today.getMonth() + 1) === month && today.getDate() === day);

                const dayEvents = complianceCurrentEvents.filter(e => e.due_date && e.due_date.startsWith(dateStr));

                let dayBg = 'rgba(15, 23, 42, 0.6)';
                if (isToday) dayBg = 'rgba(245, 158, 11, 0.12)';

                html += `
                    <div style="background: ${dayBg}; border: ${isToday ? '1px solid rgba(245, 158, 11, 0.6)' : '1px solid rgba(255,255,255,0.05)'}; min-height: 110px; padding: 8px; display: flex; flex-direction: column; gap: 6px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-weight: 800; font-size: 0.85rem; color: ${isToday ? '#facc15' : '#cbd5e1'};">${day}</span>
                            ${isToday ? '<span style="font-size: 0.65rem; background: #f59e0b; color: #000; font-weight: 900; padding: 1px 5px; border-radius: 4px;">TODAY</span>' : ''}
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 4px; overflow-y: auto; max-height: 90px;">
                `;

                dayEvents.forEach(ev => {
                    const badge = getCategoryColorBadge(ev.category);
                    const isDone = ev.status === 'Completed';
                    const isOver = ev.status === 'Overdue';

                    html += `
                        <div onclick="editComplianceEvent(event, ${ev.id})" style="background: ${badge.bg}; border: 1px solid ${badge.border}; border-radius: 6px; padding: 3px 6px; font-size: 0.72rem; cursor: pointer; display: flex; align-items: center; justify-content: space-between; gap: 4px;" title="${ev.title} (${ev.customer_legal_name || 'Client'})">
                            <span style="color: ${badge.color}; font-weight: 700; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; text-decoration: ${isDone ? 'line-through' : 'none'};">
                                ${badge.icon} ${ev.customer_legal_name ? ev.customer_legal_name.split(' ')[0] : ''}: ${ev.title}
                            </span>
                            ${isOver ? '🔴' : (isDone ? '✅' : '')}
                        </div>
                    `;
                });

                html += `
                        </div>
                    </div>
                `;
            }

            gridDaysEl.innerHTML = html;
        }

        function renderComplianceTable() {
            const tbody = document.getElementById('complianceEventsTableBody');
            if (!tbody) return;

            if (complianceCurrentEvents.length === 0) {
                tbody.innerHTML = '<tr><td colSpan="7" style="padding: 30px; text-align: center; color: var(--text-muted);">No compliance deadlines found for selected filters. Click ➕ New Deadline or ⚡ Generate Preset Schedule.</td></tr>';
                return;
            }

            tbody.innerHTML = complianceCurrentEvents.map(e => {
                const badge = getCategoryColorBadge(e.category);
                let statusHtml = '';
                if (e.status === 'Completed') statusHtml = '<span style="background: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34, 197, 94, 0.4); color: #4ade80; padding: 3px 8px; border-radius: 6px; font-size: 0.72rem; font-weight: 800;">✅ COMPLETED</span>';
                else if (e.status === 'Overdue') statusHtml = '<span style="background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); color: #f87171; padding: 3px 8px; border-radius: 6px; font-size: 0.72rem; font-weight: 800;">🔴 OVERDUE</span>';
                else statusHtml = '<span style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.4); color: #facc15; padding: 3px 8px; border-radius: 6px; font-size: 0.72rem; font-weight: 800;">🟡 PENDING</span>';

                return `
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); transition: background 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.03)'" onmouseout="this.style.background='transparent'">
                        <td style="padding: 12px 18px; font-family: monospace; font-weight: 700; color: #facc15;">${e.due_date || '—'}</td>
                        <td style="padding: 12px 18px; font-weight: 700; color: #fff;">${e.customer_legal_name || 'Customer #' + e.customer_id}</td>
                        <td style="padding: 12px 18px;">
                            <span style="background: ${badge.bg}; border: 1px solid ${badge.border}; color: ${badge.color}; padding: 3px 8px; border-radius: 6px; font-size: 0.72rem; font-weight: 700;">${badge.icon} ${e.category}</span>
                        </td>
                        <td style="padding: 12px 18px; color: #cbd5e1;">
                            <strong>${e.title}</strong>
                            ${e.description ? `<br><span style="font-size: 0.78rem; color: #94a3b8;">${e.description}</span>` : ''}
                        </td>
                        <td style="padding: 12px 18px; font-family: monospace; color: #c084fc; font-weight: 700;">👤 ${e.assigned_tax_prep || 'Unassigned'}</td>
                        <td style="padding: 12px 18px;">${statusHtml}</td>
                        <td style="padding: 12px 18px; text-align: right;">
                            <button type="button" onclick="toggleComplianceStatus(event, ${e.id}, '${e.status === 'Completed' ? 'Pending' : 'Completed'}')" style="padding: 4px 10px; background: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34, 197, 94, 0.4); color: #4ade80; border-radius: 6px; font-size: 0.72rem; font-weight: 700; cursor: pointer; margin-right: 4px;">${e.status === 'Completed' ? '🔄 RE-OPEN' : '✅ COMPLETE'}</button>
                            <button type="button" onclick="editComplianceEvent(event, ${e.id})" style="padding: 4px 8px; background: rgba(250, 204, 21, 0.15); border: 1px solid rgba(250, 204, 21, 0.4); color: #facc15; border-radius: 6px; font-size: 0.72rem; font-weight: 700; cursor: pointer; margin-right: 4px;">✏️ EDIT</button>
                            <button type="button" onclick="deleteComplianceEvent(event, ${e.id})" style="padding: 4px 8px; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); color: #f87171; border-radius: 6px; font-size: 0.72rem; font-weight: 700; cursor: pointer;">🗑️ DEL</button>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        async function toggleComplianceStatus(event, id, newStatus) {
            if (event && event.preventDefault) {
                event.preventDefault();
                event.stopPropagation();
            }
            try {
                const res = await fetch(`/api/compliance/events/${id}/status`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: newStatus })
                });
                if (res.ok) {
                    await loadComplianceData();
                }
            } catch (err) {
                alert('Error updating status: ' + err.message);
            }
        }

        async function deleteComplianceEvent(event, id) {
            if (event && event.preventDefault) {
                event.preventDefault();
                event.stopPropagation();
            }
            if (!await showCustomConfirm('Are you sure you want to delete this compliance deadline?', 'Delete Deadline', 'Yes, Delete', 'Cancel')) return;
            try {
                const res = await fetch(`/api/compliance/events/${id}`, { method: 'DELETE' });
                if (res.ok) {
                    await loadComplianceData();
                    if (typeof showAlert === 'function') showAlert('Compliance deadline deleted successfully.', 'success', 'Deadline Deleted');
                } else {
                    const err = await res.json();
                    alert('Error: ' + (err.detail || 'Failed to delete'));
                }
            } catch (err) {
                alert('Error deleting compliance deadline: ' + err.message);
            }
        }

        async function promptGenerateCompliancePreset() {
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
        }

        function closeComplianceModal() {
            const modal = document.getElementById('complianceModal');
            if (modal) modal.style.display = 'none';
        }

        function editComplianceEvent(event, id) {
            if (event && event.preventDefault) {
                event.preventDefault();
                event.stopPropagation();
            }
            const ev = complianceCurrentEvents.find(item => item.id == id);
            if (!ev) return;

            openCreateComplianceModal();
            document.getElementById('complianceFormId').value = ev.id;
            document.getElementById('complianceModalTitle').textContent = '✏️ Edit Compliance Deadline';
            document.getElementById('complianceModalCustomer').value = ev.customer_id;
            document.getElementById('complianceModalCategory').value = ev.category;
            document.getElementById('complianceModalTitleInput').value = ev.title;
            document.getElementById('complianceModalDueDate').value = ev.due_date ? ev.due_date.split('T')[0] : '';
            document.getElementById('complianceModalJurisdiction').value = ev.jurisdiction || 'Federal';
            document.getElementById('complianceModalFrequency').value = ev.frequency || 'One-Off';
            document.getElementById('complianceModalTaxPrep').value = ev.assigned_tax_prep || '';
            document.getElementById('complianceModalDesc').value = ev.description || '';
        }

        async function saveComplianceEvent(e) {
            e.preventDefault();
            const id = document.getElementById('complianceFormId').value;
            const cid = document.getElementById('complianceModalCustomer').value;
            const category = document.getElementById('complianceModalCategory').value;
            const title = document.getElementById('complianceModalTitleInput').value.trim();
            const dueDate = document.getElementById('complianceModalDueDate').value;
            const jurisdiction = document.getElementById('complianceModalJurisdiction').value.trim();
            const frequency = document.getElementById('complianceModalFrequency').value;
            const taxPrep = document.getElementById('complianceModalTaxPrep').value;
            const desc = document.getElementById('complianceModalDesc').value.trim();

            if (!cid || !title || !dueDate) {
                return alert('Customer, Title, and Due Date are required.');
            }

            const method = id ? 'PUT' : 'POST';
            const url = id ? `/api/compliance/events/${id}` : '/api/compliance/events';

            try {
                const res = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        customer_id: cid,
                        category: category,
                        title: title,
                        due_date: dueDate,
                        jurisdiction: jurisdiction,
                        frequency: frequency,
                        assigned_tax_prep: taxPrep,
                        description: desc
                    })
                });
                if (res.ok) {
                    closeComplianceModal();
                    await loadComplianceData();
                } else {
                    const err = await res.json();
                    alert('Error saving deadline: ' + (err.detail || 'Failed'));
                }
            } catch (err) {
                alert('Error saving deadline: ' + err.message);
            }
        }
"""

content = content.replace("    </script>\n\n    <!-- ── TAX PREP TEAM MANAGEMENT MODAL", js_logic + "\n    </script>\n\n    <!-- ── TAX PREP TEAM MANAGEMENT MODAL")

# 3. Add complianceModal HTML right after taxTeamModal
modal_html = """
    <!-- ── CREATE / EDIT COMPLIANCE DEADLINE MODAL ─────────────────── -->
    <div id="complianceModal" style="display: none; position: fixed; inset: 0; background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); z-index: 2000; justify-content: center; align-items: center; padding: 20px;">
        <div style="background: #0f172a; border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 20px; max-width: 600px; width: 100%; max-height: 90vh; display: flex; flex-direction: column; box-shadow: 0 25px 60px rgba(0,0,0,0.9), 0 0 35px rgba(245, 158, 11, 0.2); color: #fff; overflow: hidden;">
            <div style="padding: 20px 24px; border-bottom: 1px solid rgba(255,255,255,0.1); display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.02);">
                <h3 id="complianceModalTitle" style="font-family: 'Outfit', sans-serif; font-size: 1.3rem; font-weight: 800; color: #fff; margin: 0;">
                    ➕ Create Compliance Deadline
                </h3>
                <button onclick="closeComplianceModal()" style="background: transparent; border: none; color: #94a3b8; cursor: pointer; padding: 4px; border-radius: 50%; font-size: 1.2rem;">✖</button>
            </div>
            <form onsubmit="saveComplianceEvent(event)" style="padding: 20px 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 16px;">
                <input type="hidden" id="complianceFormId">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;">
                    <div>
                        <label style="display: block; font-size: 0.75rem; font-weight: 700; color: #94a3b8; margin-bottom: 6px;">Customer *</label>
                        <select id="complianceModalCustomer" required style="width: 100%; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); border-radius: 10px; padding: 9px 14px; font-size: 0.88rem; color: #fff; outline: none;"></select>
                    </div>
                    <div>
                        <label style="display: block; font-size: 0.75rem; font-weight: 700; color: #94a3b8; margin-bottom: 6px;">Category *</label>
                        <select id="complianceModalCategory" required style="width: 100%; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); border-radius: 10px; padding: 9px 14px; font-size: 0.88rem; color: #fff; outline: none;">
                            <option value="Sales Tax">📊 Sales Tax</option>
                            <option value="Payroll Tax">💼 Payroll Tax</option>
                            <option value="Estimated Tax">🏛️ Estimated Tax</option>
                            <option value="Corporate Tax">📑 Corporate Tax</option>
                            <option value="1099/W2">✉️ 1099 / W-2</option>
                            <option value="Franchise Tax">🏢 Franchise Tax</option>
                            <option value="Bookkeeping Close">📈 Bookkeeping Close</option>
                            <option value="Custom">📌 Custom</option>
                        </select>
                    </div>
                </div>

                <div>
                    <label style="display: block; font-size: 0.75rem; font-weight: 700; color: #94a3b8; margin-bottom: 6px;">Deadline Title *</label>
                    <input type="text" id="complianceModalTitleInput" required placeholder="e.g. Sales Tax Return - September 2026" style="width: 100%; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); border-radius: 10px; padding: 9px 14px; font-size: 0.88rem; color: #fff; outline: none;">
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;">
                    <div>
                        <label style="display: block; font-size: 0.75rem; font-weight: 700; color: #94a3b8; margin-bottom: 6px;">Due Date *</label>
                        <input type="date" id="complianceModalDueDate" required style="width: 100%; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); border-radius: 10px; padding: 9px 14px; font-size: 0.88rem; color: #fff; outline: none;">
                    </div>
                    <div>
                        <label style="display: block; font-size: 0.75rem; font-weight: 700; color: #94a3b8; margin-bottom: 6px;">Jurisdiction</label>
                        <input type="text" id="complianceModalJurisdiction" placeholder="e.g. Federal, Florida, Local..." style="width: 100%; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); border-radius: 10px; padding: 9px 14px; font-size: 0.88rem; color: #fff; outline: none;">
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;">
                    <div>
                        <label style="display: block; font-size: 0.75rem; font-weight: 700; color: #94a3b8; margin-bottom: 6px;">Frequency</label>
                        <select id="complianceModalFrequency" style="width: 100%; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); border-radius: 10px; padding: 9px 14px; font-size: 0.88rem; color: #fff; outline: none;">
                            <option value="One-Off">One-Off</option>
                            <option value="Monthly">Monthly</option>
                            <option value="Quarterly">Quarterly</option>
                            <option value="Semi-Annual">Semi-Annual</option>
                            <option value="Annual">Annual</option>
                        </select>
                    </div>
                    <div>
                        <label style="display: block; font-size: 0.75rem; font-weight: 700; color: #94a3b8; margin-bottom: 6px;">Assigned Tax Prep</label>
                        <select id="complianceModalTaxPrep" style="width: 100%; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); border-radius: 10px; padding: 9px 14px; font-size: 0.88rem; color: #fff; outline: none;"></select>
                    </div>
                </div>

                <div>
                    <label style="display: block; font-size: 0.75rem; font-weight: 700; color: #94a3b8; margin-bottom: 6px;">Description / Notes</label>
                    <textarea id="complianceModalDesc" rows="2" placeholder="Instructions, form numbers, or filing notes..." style="width: 100%; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); border-radius: 10px; padding: 9px 14px; font-size: 0.88rem; color: #fff; outline: none;"></textarea>
                </div>

                <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 10px;">
                    <button type="button" onclick="closeComplianceModal()" style="padding: 9px 18px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); color: #cbd5e1; font-weight: 700; border-radius: 10px; font-size: 0.85rem; cursor: pointer;">Cancel</button>
                    <button type="submit" style="padding: 9px 24px; background: linear-gradient(135deg, #f59e0b, #d97706); color: #000; font-weight: 800; font-size: 0.85rem; text-transform: uppercase; border: none; border-radius: 10px; cursor: pointer; box-shadow: 0 0 15px rgba(245, 158, 11, 0.35);">Save Deadline</button>
                </div>
            </form>
        </div>
    </div>
"""

content = content.replace("    <!-- ── TAX PREP TEAM MANAGEMENT MODAL", modal_html + "\n    <!-- ── TAX PREP TEAM MANAGEMENT MODAL")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("COMPLIANCE DASHBOARD HTML UPDATED SUCCESSFULLY")
