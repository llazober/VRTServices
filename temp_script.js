
        // ── Custom Glassmorphic Alert & Confirm System ─────────────────────────
        let customAlertCallback = null;
        let customConfirmPromiseResolver = null;

        function safeEscapeHtml(str) {
            if (!str) return '';
            return String(str)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
        }

        function showCustomAlert(msg, type = null, title = null, onConfirm = null) {
            // Handle caller format signature showCustomAlert(title, message, type)
            if (typeof title === 'string' && ['success', 'error', 'warning', 'info'].includes(title.toLowerCase())) {
                const actualTitle = msg;
                const actualMsg = type;
                const actualType = title.toLowerCase();
                msg = actualMsg;
                type = actualType;
                title = actualTitle;
            }

            const formatErrorDetail = (val) => {
                if (!val) return '';
                if (typeof val === 'string') return val;
                if (Array.isArray(val)) return val.map(item => typeof item === 'object' ? (item.msg || item.detail || JSON.stringify(item)) : String(item)).join(', ');
                if (typeof val === 'object') {
                    if (val.detail) return formatErrorDetail(val.detail);
                    if (val.message) return String(val.message);
                    return JSON.stringify(val);
                }
                return String(val);
            };

            let cleanMsg = formatErrorDetail(msg);
            let autoType = formatErrorDetail(type) || null;
            let autoTitle = title;

            if (!autoType) {
                if (cleanMsg.includes('✅') || cleanMsg.toLowerCase().includes('success')) {
                    autoType = 'success';
                } else if (cleanMsg.includes('❌') || cleanMsg.toLowerCase().includes('error') || cleanMsg.toLowerCase().includes('failed')) {
                    autoType = 'error';
                } else if (cleanMsg.includes('⚠️') || cleanMsg.toLowerCase().includes('warning') || cleanMsg.toLowerCase().includes('notice')) {
                    autoType = 'warning';
                } else {
                    autoType = 'info';
                }
            }

            cleanMsg = cleanMsg.replace(/^([✅❌⚠️ℹ️💬⏳🚀]\s*)+/, '').trim();

            if (!autoTitle) {
                if (autoType === 'success') autoTitle = 'Success';
                else if (autoType === 'error') autoTitle = 'Error';
                else if (autoType === 'warning') autoTitle = 'Attention';
                else autoTitle = 'System Notification';
            }

            customAlertCallback = onConfirm;

            let modal = document.getElementById('customAlertModal');
            if (!modal) {
                if (window.nativeAlert) window.nativeAlert(msg);
                else alert(msg);
                if (onConfirm) onConfirm();
                return;
            }

            document.body.appendChild(modal);
            modal.style.zIndex = '2147483647';

            const iconBox = document.getElementById('customAlertIconBox');
            const titleEl = document.getElementById('customAlertTitle');
            const msgEl = document.getElementById('customAlertMessage');
            const okBtn = document.getElementById('customAlertOkBtn');
            const card = document.getElementById('customAlertCard');

            titleEl.textContent = autoTitle;

            const lines = cleanMsg.split('\n').filter(l => l.trim().length > 0);
            msgEl.innerHTML = lines.map(line => {
                if (line.includes(': ')) {
                    const parts = line.split(': ');
                    return `<div style="margin-top: 4px;"><span style="color: #94a3b8; font-size: 0.78rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em;">${safeEscapeHtml(parts[0])}:</span> <span style="color: #38bdf8; font-weight: 600; font-family: monospace; font-size: 0.85rem;">${safeEscapeHtml(parts.slice(1).join(': '))}</span></div>`;
                }
                return `<div style="margin-bottom: 4px;">${safeEscapeHtml(line)}</div>`;
            }).join('');

            if (autoType === 'success') {
                iconBox.innerHTML = '✅';
                iconBox.style.background = 'rgba(16, 185, 129, 0.15)';
                iconBox.style.borderColor = 'rgba(16, 185, 129, 0.4)';
                iconBox.style.color = '#10b981';
                card.style.boxShadow = '0 25px 60px rgba(0, 0, 0, 0.85), 0 0 35px rgba(16, 185, 129, 0.2)';
                okBtn.style.background = 'linear-gradient(135deg, #10b981, #059669)';
                okBtn.style.boxShadow = '0 4px 14px rgba(16, 185, 129, 0.4)';
            } else if (autoType === 'error') {
                iconBox.innerHTML = '❌';
                iconBox.style.background = 'rgba(244, 63, 94, 0.15)';
                iconBox.style.borderColor = 'rgba(244, 63, 94, 0.4)';
                iconBox.style.color = '#f43f5e';
                card.style.boxShadow = '0 25px 60px rgba(0, 0, 0, 0.85), 0 0 35px rgba(244, 63, 94, 0.2)';
                okBtn.style.background = 'linear-gradient(135deg, #f43f5e, #be123c)';
                okBtn.style.boxShadow = '0 4px 14px rgba(244, 63, 94, 0.4)';
            } else if (autoType === 'warning') {
                iconBox.innerHTML = '⚠️';
                iconBox.style.background = 'rgba(245, 158, 11, 0.15)';
                iconBox.style.borderColor = 'rgba(245, 158, 11, 0.4)';
                iconBox.style.color = '#f59e0b';
                card.style.boxShadow = '0 25px 60px rgba(0, 0, 0, 0.85), 0 0 35px rgba(245, 158, 11, 0.2)';
                okBtn.style.background = 'linear-gradient(135deg, #f59e0b, #b45309)';
                okBtn.style.boxShadow = '0 4px 14px rgba(245, 158, 11, 0.4)';
            } else {
                iconBox.innerHTML = '💬';
                iconBox.style.background = 'rgba(59, 130, 246, 0.15)';
                iconBox.style.borderColor = 'rgba(59, 130, 246, 0.4)';
                iconBox.style.color = '#3b82f6';
                card.style.boxShadow = '0 25px 60px rgba(0, 0, 0, 0.85), 0 0 35px rgba(59, 130, 246, 0.2)';
                okBtn.style.background = 'linear-gradient(135deg, #3b82f6, #1d4ed8)';
                okBtn.style.boxShadow = '0 4px 14px rgba(59, 130, 246, 0.4)';
            }

            modal.style.display = 'flex';
            setTimeout(() => { if (okBtn) okBtn.focus(); }, 50);
        }

        function closeCustomAlert() {
            const modal = document.getElementById('customAlertModal');
            if (modal) modal.style.display = 'none';
            if (customAlertCallback) {
                const cb = customAlertCallback;
                customAlertCallback = null;
                cb();
            }
        }

        function showCustomConfirm(msg, title = null, confirmText = null, cancelText = null) {
            return new Promise((resolve) => {
                let cleanMsg = String(msg || '');
                let isDelete = cleanMsg.toLowerCase().includes('delete') || cleanMsg.toLowerCase().includes('remove');
                let autoTitle = title || (isDelete ? 'Confirm Delete' : 'Please Confirm');
                let autoConfirmText = confirmText || (isDelete ? 'Yes, Delete' : 'Confirm');
                let autoCancelText = cancelText || 'Cancel';

                cleanMsg = cleanMsg.replace(/^([⚠️🗑️❓❌]\s*)+/, '').trim();

                let modal = document.getElementById('customConfirmModal');
                if (!modal) {
                    let res = window.nativeConfirm ? window.nativeConfirm(msg) : true;
                    resolve(res);
                    return;
                }

                document.body.appendChild(modal);
                modal.style.zIndex = '2147483647';

                customConfirmPromiseResolver = resolve;

                const iconBox = document.getElementById('customConfirmIconBox');
                const titleEl = document.getElementById('customConfirmTitle');
                const msgEl = document.getElementById('customConfirmMessage');
                const actionBtn = document.getElementById('customConfirmActionBtn');
                const cancelBtn = document.getElementById('customConfirmCancelBtn');
                const card = document.getElementById('customConfirmCard');

                titleEl.textContent = autoTitle;
                actionBtn.textContent = autoConfirmText;
                cancelBtn.textContent = autoCancelText;

                const lines = cleanMsg.split('\n').filter(l => l.trim().length > 0);
                msgEl.innerHTML = lines.map(line => {
                    if (line.includes(': ')) {
                        const parts = line.split(': ');
                        return `<div style="margin-top: 4px;"><span style="color: #94a3b8; font-size: 0.78rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em;">${safeEscapeHtml(parts[0])}:</span> <span style="color: #38bdf8; font-weight: 600; font-family: monospace; font-size: 0.85rem;">${safeEscapeHtml(parts.slice(1).join(': '))}</span></div>`;
                    }
                    return `<div style="margin-bottom: 4px;">${safeEscapeHtml(line)}</div>`;
                }).join('');

                if (isDelete) {
                    iconBox.innerHTML = '🗑️';
                    iconBox.style.background = 'rgba(244, 63, 94, 0.15)';
                    iconBox.style.borderColor = 'rgba(244, 63, 94, 0.4)';
                    iconBox.style.color = '#f43f5e';
                    card.style.borderColor = 'rgba(244, 63, 94, 0.4)';
                    card.style.boxShadow = '0 25px 60px rgba(0, 0, 0, 0.85), 0 0 35px rgba(244, 63, 94, 0.2)';
                    actionBtn.style.background = 'linear-gradient(135deg, #f43f5e, #be123c)';
                    actionBtn.style.boxShadow = '0 4px 14px rgba(244, 63, 94, 0.4)';
                } else {
                    iconBox.innerHTML = '❓';
                    iconBox.style.background = 'rgba(59, 130, 246, 0.15)';
                    iconBox.style.borderColor = 'rgba(59, 130, 246, 0.4)';
                    iconBox.style.color = '#3b82f6';
                    card.style.borderColor = 'rgba(59, 130, 246, 0.4)';
                    card.style.boxShadow = '0 25px 60px rgba(0, 0, 0, 0.85), 0 0 35px rgba(59, 130, 246, 0.2)';
                    actionBtn.style.background = 'linear-gradient(135deg, #3b82f6, #1d4ed8)';
                    actionBtn.style.boxShadow = '0 4px 14px rgba(59, 130, 246, 0.4)';
                }

                modal.style.display = 'flex';
                setTimeout(() => { if (actionBtn) actionBtn.focus(); }, 50);
            });
        }

        function closeCustomConfirm(result) {
            const modal = document.getElementById('customConfirmModal');
            if (modal) modal.style.display = 'none';
            if (customConfirmPromiseResolver) {
                const res = customConfirmPromiseResolver;
                customConfirmPromiseResolver = null;
                res(Boolean(result));
            }
        }

        document.addEventListener('keydown', function(e) {
            const confirmModal = document.getElementById('customConfirmModal');
            if (confirmModal && confirmModal.style.display === 'flex') {
                if (e.key === 'Escape') {
                    e.preventDefault();
                    closeCustomConfirm(false);
                } else if (e.key === 'Enter') {
                    e.preventDefault();
                    closeCustomConfirm(true);
                }
                return;
            }
            const alertModal = document.getElementById('customAlertModal');
            if (alertModal && alertModal.style.display === 'flex') {
                if (e.key === 'Enter' || e.key === 'Escape') {
                    e.preventDefault();
                    closeCustomAlert();
                }
            }
        });

        if (!window.nativeAlert) {
            window.nativeAlert = window.alert;
        }
        window.alert = function(msg) {
            showCustomAlert(msg);
        };

        if (!window.nativeConfirm) {
            window.nativeConfirm = window.confirm;
        }
        window.confirm = function(msg) {
            showCustomConfirm(msg);
            return false;
        };

        const CURRENT_PARENT_NAME = {{ (parent_name or company_name or 'VRT Services') | tojson | safe }};
        const CURRENT_USER_EMAIL = {{ (user_email or username or 'luislazo@datalazo.net') | tojson | safe }};
        const RESEND_REPLY_TO_EMAIL = {{ (resend_reply_to_email or 'notification@vrtservices12.com') | tojson | safe }};

        let currentCoaRecords = [];
        let currentParentMappings = [];
        let currentHistoryRecords = [];
        let historySortKey = 'accountNumber';
        let historySortOrder = 'asc';
        let supportAttachedFile = null;
        var currentUnreadMap = {};

        document.addEventListener('DOMContentLoaded', () => {
            const toggleBtn = document.getElementById('toggleSidebar');
            const body = document.body;

            // Load saved sidebar state
            const isCollapsed = localStorage.getItem('sidebar_collapsed') === 'true';
            if (isCollapsed) {
                body.classList.add('sidebar-collapsed');
            }

            if (toggleBtn) {
                toggleBtn.addEventListener('click', () => {
                    body.classList.toggle('sidebar-collapsed');
                    localStorage.setItem('sidebar_collapsed', body.classList.contains('sidebar-collapsed'));
                });
            }

            const userProfileBadge = document.getElementById('headerUserProfileBadge');
            if (userProfileBadge) {
                userProfileBadge.addEventListener('click', (e) => {
                    if (typeof window.openSecurityModal === 'function') {
                        window.openSecurityModal();
                    }
                });
            }

            syncClientSelectDropdowns();
            loadWorkloadSummary();

            const currentPath = window.location.pathname;
            const currentTab = '{{ active_tab or "" }}';

            if (currentPath === '/customers' || currentTab === 'customers') {
                fetchCustomerRecords(true);
            } else if (currentPath === '/billing' || currentTab === 'billing') {
                initBillingModule();
            } else if (currentPath === '/compliance' || currentTab === 'compliance') {
                loadComplianceData();
            } else if (currentPath.startsWith('/management') || currentPath.startsWith('/tools') || currentTab === 'management') {
                initManagementModule();
            } else {
                fetchCustomerRecords();
            }
        });

        // ── MANAGEMENT & TOOLS HUB CONTROLLER ────────────────────────────────────
        function switchMgmtTab(tabName) {
            const tabs = ['coa', 'mappings', 'rules', 'taxteam', 'audit', 'rag', 'esign'];
            const activeStyles = {
                coa: { border: 'rgba(103, 232, 249, 0.4)', bg: 'rgba(103, 232, 249, 0.15)', color: '#67e8f9' },
                mappings: { border: 'rgba(192, 132, 252, 0.4)', bg: 'rgba(192, 132, 252, 0.15)', color: '#c084fc' },
                rules: { border: 'rgba(110, 231, 183, 0.4)', bg: 'rgba(110, 231, 183, 0.15)', color: '#6ee7b7' },
                taxteam: { border: 'rgba(250, 204, 21, 0.4)', bg: 'rgba(250, 204, 21, 0.15)', color: '#facc15' },
                audit: { border: 'rgba(168, 85, 247, 0.4)', bg: 'rgba(168, 85, 247, 0.15)', color: '#c084fc' },
                rag: { border: 'rgba(236, 72, 153, 0.4)', bg: 'rgba(236, 72, 153, 0.15)', color: '#f472b6' },
                esign: { border: 'rgba(56, 189, 248, 0.4)', bg: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8' }
            };

            tabs.forEach(t => {
                const btn = document.getElementById(`mgmtTabBtn-${t}`);
                const panel = document.getElementById(`mgmtPanel-${t}`);
                if (btn) {
                    if (t === tabName) {
                        btn.classList.add('active');
                        btn.style.background = activeStyles[t].bg;
                        btn.style.borderColor = activeStyles[t].border;
                        btn.style.color = activeStyles[t].color;
                    } else {
                        btn.classList.remove('active');
                        btn.style.background = 'rgba(255,255,255,0.04)';
                        btn.style.borderColor = 'rgba(255,255,255,0.1)';
                        btn.style.color = '#94a3b8';
                    }
                }
                if (panel) {
                    panel.style.display = (t === tabName) ? 'block' : 'none';
                }
            });

            if (tabName === 'coa') {
                fetchCoaRecords();
            } else if (tabName === 'mappings') {
                populateCustomerDropdownForMappings();
                fetchParentMappings();
            } else if (tabName === 'rules') {
                fetchHistoryRecords();
            } else if (tabName === 'taxteam') {
                fetchTaxTeamMembers();
            } else if (tabName === 'audit') {
                loadAuditLogs(auditCurrentPage);
            } else if (tabName === 'rag') {
                fetchKbDocuments();
            } else if (tabName === 'esign') {
                fetchEsignatureRequests();
            }

            if (window.history && window.history.replaceState) {
                const url = new URL(window.location);
                url.searchParams.set('tab', tabName);
                window.history.replaceState({}, '', url);
            }
        }

        async function initManagementModule() {
            console.log("[MANAGEMENT MODULE] Initializing Management Hub...");
            const urlParams = new URLSearchParams(window.location.search);
            const tabParam = urlParams.get('tab') || '{{ sub_tab or "coa" }}';
            const targetTab = ['coa', 'mappings', 'rules', 'taxteam', 'audit', 'rag', 'esign'].includes(tabParam) ? tabParam : 'coa';
            
            switchMgmtTab(targetTab);

            try {
                await Promise.all([
                    syncClientSelectDropdowns(),
                    populateCustomerDropdownForMappings(),
                    fetchCoaRecords(),
                    fetchParentMappings(),
                    fetchHistoryRecords(),
                    fetchTaxTeamMembers(),
                    fetchKbDocuments(),
                    fetchEsignatureRequests()
                ]);
            } catch (err) {
                console.error("Notice initializing Management Hub data:", err);
            }
        }

        // ── VRT KNOWLEDGE BASE & RAG CONTROLLER ──────────────────────────────────────
        function escapeHtml(str) {
            if (str === null || str === undefined) return '';
            return String(str)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
        }

        let kbDocumentsList = [];

        async function fetchKbDocuments() {
            try {
                const resp = await fetch('/api/kb/documents');
                if (!resp.ok) throw new Error("Failed to fetch KB documents");
                const data = await resp.json();
                kbDocumentsList = data.documents || [];
                renderKbDocumentsTable();
            } catch (err) {
                console.error("Error fetching KB documents:", err);
                const tbody = document.getElementById('kbDocumentsTableBody');
                if (tbody) {
                    tbody.innerHTML = `<tr><td colSpan="3" style="padding: 16px; text-align: center; color: #f87171;">Failed to load documents: ${err.message}</td></tr>`;
                }
            }
        }

        function renderKbDocumentsTable() {
            const tbody = document.getElementById('kbDocumentsTableBody');
            const badge = document.getElementById('kbDocCountBadge');
            if (badge) {
                badge.textContent = `${kbDocumentsList.length} Document${kbDocumentsList.length === 1 ? '' : 's'}`;
            }
            if (!tbody) return;

            if (kbDocumentsList.length === 0) {
                tbody.innerHTML = `<tr><td colSpan="3" style="padding: 24px; text-align: center; color: #94a3b8;">No documents uploaded to VRT DB yet. Upload a file above to begin!</td></tr>`;
                return;
            }

            tbody.innerHTML = kbDocumentsList.map(doc => {
                const sizeKb = (doc.file_size / 1024).toFixed(1);
                return `
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); transition: background 0.2s ease;">
                        <td style="padding: 10px 12px;">
                            <div style="font-weight: 700; color: #fff; line-height: 1.3;">${escapeHtml(doc.title)}</div>
                            <div style="font-size: 0.7rem; color: #94a3b8; margin-top: 2px;">
                                <span style="color: #ec4899; font-weight: 600;">${escapeHtml(doc.category)}</span> • ${doc.file_type.toUpperCase()} • ${sizeKb} KB
                            </div>
                        </td>
                        <td style="padding: 10px 12px; font-weight: 700; color: #38bdf8;">
                            ${doc.chunk_count || 0} chunks
                        </td>
                        <td style="padding: 10px 12px; text-align: right;">
                            <button onclick="deleteKbDocument(${doc.id})" title="Delete Document from VRT DB" style="background: rgba(239, 68, 68, 0.2); border: 1px solid rgba(239, 68, 68, 0.5); color: #fca5a5; font-weight: 800; border-radius: 8px; padding: 6px 12px; font-size: 0.78rem; cursor: pointer; transition: all 0.2s ease; display: inline-flex; align-items: center; gap: 4px;">
                                🗑️ Delete
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        async function handleKbUpload(event) {
            event.preventDefault();
            const fileInput = document.getElementById('kbFileInput');
            const titleInput = document.getElementById('kbTitleInput');
            const categoryInput = document.getElementById('kbCategoryInput');
            const tagsInput = document.getElementById('kbTagsInput');
            const statusEl = document.getElementById('kbUploadStatus');
            const submitBtn = document.getElementById('kbUploadBtn');

            if (!fileInput.files || fileInput.files.length === 0) {
                alert("Please select a file to upload.");
                return;
            }

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('title', titleInput.value.trim());
            formData.append('category', categoryInput.value.trim());
            formData.append('tags', tagsInput.value.trim());

            submitBtn.disabled = true;
            submitBtn.innerHTML = "⏳ Parsing & Chunking into VRT DB...";
            statusEl.style.display = "block";
            statusEl.style.background = "rgba(56, 189, 248, 0.15)";
            statusEl.style.color = "#38bdf8";
            statusEl.textContent = "Processing document and generating vector embeddings...";

            try {
                const resp = await fetch('/api/kb/upload', {
                    method: 'POST',
                    body: formData
                });
                const res = await resp.json();

                if (!resp.ok) {
                    throw new Error(res.detail || "Upload failed");
                }

                statusEl.style.background = "rgba(16, 185, 129, 0.15)";
                statusEl.style.color = "#34d399";
                statusEl.textContent = `✅ ${res.message}`;

                fileInput.value = "";
                titleInput.value = "";
                tagsInput.value = "";
                await fetchKbDocuments();
            } catch (err) {
                console.error("Upload error:", err);
                statusEl.style.background = "rgba(239, 68, 68, 0.15)";
                statusEl.style.color = "#f87171";
                statusEl.textContent = `❌ ${err.message}`;
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = "⚡ Upload & Extract Chunks to VRT DB";
            }
        }

        async function deleteKbDocument(docId) {
            if (!confirm("Are you sure you want to delete this document and all its text chunks from the VRT Database?")) {
                return;
            }
            try {
                const resp = await fetch(`/api/kb/documents/${docId}`, { method: 'DELETE' });
                const data = await resp.json();
                if (!resp.ok) throw new Error(data.detail || "Failed to delete");
                await fetchKbDocuments();
            } catch (err) {
                alert("Error deleting document: " + err.message);
            }
        }

        function setKbPrompt(promptText) {
            const input = document.getElementById('kbQueryInput');
            if (input) {
                input.value = promptText;
                input.focus();
            }
        }

        async function submitKbRagQuery() {
            const input = document.getElementById('kbQueryInput');
            const submitBtn = document.getElementById('kbQuerySubmitBtn');
            const responseBox = document.getElementById('kbQueryResponseBox');
            const citationsBox = document.getElementById('kbCitationsBox');
            const citationsList = document.getElementById('kbCitationsList');
            const chunkCountLabel = document.getElementById('kbChunkCountLabel');

            const query = input.value.trim();
            if (!query) {
                alert("Please enter a query question first.");
                return;
            }

            submitBtn.disabled = true;
            submitBtn.innerHTML = "<span>⏳</span><span>Searching...</span>";
            responseBox.innerHTML = `
                <div style="text-align: center; padding: 30px; color: #38bdf8;">
                    <div style="font-size: 1.8rem; animation: spin 1s linear infinite; display: inline-block;">⚙️</div>
                    <div style="font-weight: 700; margin-top: 10px;">Retrieving context from VRT Database & Querying GPT-4o Mini...</div>
                </div>
            `;

            try {
                const resp = await fetch('/api/kb/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query })
                });
                const res = await resp.json();

                if (!resp.ok) {
                    throw new Error(res.detail || "Failed to query RAG engine");
                }

                let formattedAnswer = escapeHtml(res.answer || "");
                formattedAnswer = formattedAnswer
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/### (.*?)\n/g, '<h3 style="color:#fff; font-size:1.05rem; margin:12px 0 6px 0;">$1</h3>')
                    .replace(/\[Source (\d+)\]/g, '<span style="background:rgba(236,72,153,0.2); border:1px solid rgba(236,72,153,0.4); color:#f472b6; padding:2px 6px; border-radius:6px; font-size:0.75rem; font-weight:700;">Source $1</span>')
                    .replace(/\n/g, '<br>');

                responseBox.innerHTML = `
                    <div style="font-family: inherit;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 8px;">
                            <span style="font-weight: 800; color: #f472b6; font-size: 0.82rem; text-transform: uppercase;">Answer from GPT-4o Mini</span>
                            <span style="font-size: 0.72rem; color: #94a3b8;">${res.retrieved_chunks ? res.retrieved_chunks.length : 0} Sources Retrieved</span>
                        </div>
                        <div>${formattedAnswer}</div>
                    </div>
                `;

                if (res.citations && res.citations.length > 0) {
                    citationsBox.style.display = "block";
                    chunkCountLabel.textContent = `${res.citations.length} retrieved chunks`;
                    citationsList.innerHTML = res.citations.map(c => `
                        <div style="background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.06); border-radius: 6px; padding: 8px; font-size: 0.75rem;">
                            <div style="font-weight: 700; color: #38bdf8; display: flex; justify-content: space-between;">
                                <span>[Source ${c.source_id}] ${escapeHtml(c.title)}</span>
                                <span style="color: #ec4899;">Score: ${c.score}</span>
                            </div>
                            <div style="color: #cbd5e1; margin-top: 4px; font-style: italic;">"${escapeHtml(c.snippet)}"</div>
                        </div>
                    `).join('');
                } else {
                    citationsBox.style.display = "none";
                }

            } catch (err) {
                console.error("RAG Query Error:", err);
                responseBox.innerHTML = `<div style="color: #f87171; font-weight: 700;">❌ Query Error: ${escapeHtml(err.message)}</div>`;
                citationsBox.style.display = "none";
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = "<span>🔍</span><span>Ask AI</span>";
            }
        }

        // ── RAG ASSISTANT MODAL CONTROLLER ──────────────────────────────────────────
        function openRagAssistantModal() {
            console.log("[RAG MODAL] Opening RAG assistant modal...");
            const modal = document.getElementById('ragAssistantModal');
            if (!modal) {
                console.error("[RAG MODAL] ragAssistantModal element not found in DOM!");
                return;
            }
            modal.style.display = 'flex';
            modal.style.opacity = '1';
            modal.style.visibility = 'visible';
            modal.style.zIndex = '2147483647';
            const content = modal.firstElementChild;
            if (content) {
                content.style.transform = 'scale(1)';
                content.style.opacity = '1';
            }
        }

        function closeRagAssistantModal() {
            const modal = document.getElementById('ragAssistantModal');
            if (!modal) return;
            modal.style.opacity = '0';
            const content = modal.firstElementChild;
            if (content) content.style.transform = 'scale(0.95)';
            setTimeout(() => {
                modal.style.display = 'none';
            }, 300);
        }

        function setKbModalPrompt(text) {
            const input = document.getElementById('kbModalQueryInput');
            if (input) {
                input.value = text;
                input.focus();
            }
        }

        async function submitKbModalRagQuery() {
            const input = document.getElementById('kbModalQueryInput');
            const submitBtn = document.getElementById('kbModalQuerySubmitBtn');
            const responseBox = document.getElementById('kbModalQueryResponseBox');
            const citationsBox = document.getElementById('kbModalCitationsBox');
            const citationsList = document.getElementById('kbModalCitationsList');
            const chunkCountLabel = document.getElementById('kbModalChunkCountLabel');

            const query = input ? input.value.trim() : '';
            if (!query) {
                alert("Please enter a query question first.");
                return;
            }

            submitBtn.disabled = true;
            submitBtn.innerHTML = "<span style='font-size:1rem;'>⏳</span><span>Searching</span>";
            responseBox.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #38bdf8;">
                    <div style="font-size: 2rem; animation: spin 1s linear infinite; display: inline-block;">⚙️</div>
                    <div style="font-weight: 700; margin-top: 12px; font-size: 0.95rem;">Retrieving context from VRT Database & Querying GPT-4o Mini...</div>
                </div>
            `;

            try {
                const resp = await fetch('/api/kb/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query })
                });
                const res = await resp.json();

                if (!resp.ok) {
                    throw new Error(res.detail || "Failed to query RAG engine");
                }

                let formattedAnswer = escapeHtml(res.answer || "");
                formattedAnswer = formattedAnswer
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/### (.*?)\n/g, '<h3 style="color:#fff; font-size:1.05rem; margin:12px 0 6px 0;">$1</h3>')
                    .replace(/\[Source (\d+)\]/g, '<span style="background:rgba(236,72,153,0.2); border:1px solid rgba(236,72,153,0.4); color:#f472b6; padding:2px 6px; border-radius:6px; font-size:0.75rem; font-weight:700;">Source $1</span>')
                    .replace(/\n/g, '<br>');

                responseBox.innerHTML = `
                    <div style="font-family: inherit;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 8px;">
                            <span style="font-weight: 800; color: #f472b6; font-size: 0.85rem; text-transform: uppercase;">Answer from GPT-4o Mini</span>
                            <span style="font-size: 0.75rem; color: #94a3b8;">${res.retrieved_chunks ? res.retrieved_chunks.length : 0} Sources Retrieved</span>
                        </div>
                        <div>${formattedAnswer}</div>
                    </div>
                `;

                if (res.citations && res.citations.length > 0) {
                    citationsBox.style.display = "block";
                    chunkCountLabel.textContent = `${res.citations.length} retrieved chunks`;
                    citationsList.innerHTML = res.citations.map(c => `
                        <div style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 8px 12px; font-size: 0.78rem;">
                            <div style="font-weight: 700; color: #38bdf8; display: flex; justify-content: space-between;">
                                <span>[Source ${c.source_id}] ${escapeHtml(c.title)}</span>
                                <span style="color: #ec4899;">Score: ${c.score}</span>
                            </div>
                            <div style="color: #cbd5e1; margin-top: 4px; font-style: italic;">"${escapeHtml(c.snippet)}"</div>
                        </div>
                    `).join('');
                } else {
                    citationsBox.style.display = "none";
                }

            } catch (err) {
                console.error("Modal RAG Query Error:", err);
                responseBox.innerHTML = `<div style="color: #f87171; font-weight: 700;">❌ Query Error: ${escapeHtml(err.message)}</div>`;
                citationsBox.style.display = "none";
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = "<span style='font-size: 1.1rem;'>🔍</span><span>ASK AI</span>";
            }
        }

        // ── SYSTEM AUDIT LOGS CONTROLLER ───────────────────────────────────────────
        let auditCurrentPage = 1;
        let auditTotalPages = 1;

        async function loadAuditLogs(page = 1) {
            auditCurrentPage = page;
            const tableBody = document.getElementById('auditTableBody');
            if (tableBody) {
                tableBody.innerHTML = `<tr><td colSpan="6" style="padding: 30px; text-align: center; color: var(--text-muted);">Loading audit log records...</td></tr>`;
            }

            const search = document.getElementById('auditSearchInput')?.value || '';
            const action = document.getElementById('auditActionFilter')?.value || '';
            const startDate = document.getElementById('auditStartDate')?.value || '';
            const endDate = document.getElementById('auditEndDate')?.value || '';

            const params = new URLSearchParams({
                page: auditCurrentPage,
                limit: 25,
                search: search,
                action: action,
                start_date: startDate,
                end_date: endDate
            });

            try {
                const response = await fetch(`/api/audit-logs?${params.toString()}`);
                const data = await response.json();

                if (!data.success) {
                    throw new Error(data.error || 'Failed to fetch audit logs');
                }

                auditTotalPages = data.pages || 1;
                renderAuditLogsTable(data.logs || []);

                const curPageElem = document.getElementById('auditCurrentPageNum');
                const totPageElem = document.getElementById('auditTotalPagesNum');
                const totRecElem = document.getElementById('auditTotalRecordsNum');
                const prevBtn = document.getElementById('auditPrevBtn');
                const nextBtn = document.getElementById('auditNextBtn');

                if (curPageElem) curPageElem.innerText = data.page || 1;
                if (totPageElem) totPageElem.innerText = auditTotalPages;
                if (totRecElem) totRecElem.innerText = data.total || 0;

                if (prevBtn) {
                    prevBtn.disabled = (data.page <= 1);
                    prevBtn.style.opacity = (data.page <= 1) ? '0.4' : '1';
                }
                if (nextBtn) {
                    nextBtn.disabled = (data.page >= auditTotalPages);
                    nextBtn.style.opacity = (data.page >= auditTotalPages) ? '0.4' : '1';
                }

            } catch (err) {
                console.error("[AUDIT LOG ERROR]", err);
                if (tableBody) {
                    tableBody.innerHTML = `<tr><td colSpan="6" style="padding: 30px; text-align: center; color: #ef4444;">Failed to load audit logs: ${err.message}</td></tr>`;
                }
            }
        }

        function renderAuditLogsTable(logs) {
            const tableBody = document.getElementById('auditTableBody');
            if (!tableBody) return;

            if (logs.length === 0) {
                tableBody.innerHTML = `<tr><td colSpan="6" style="padding: 30px; text-align: center; color: var(--text-muted);">No audit log events found matching your filter criteria.</td></tr>`;
                return;
            }

            const getActionBadge = (act) => {
                const a = (act || '').toUpperCase();
                if (a.includes('LOGIN') && !a.includes('FAILED')) {
                    return `<span style="padding: 3px 8px; border-radius: 6px; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.35); color: #38bdf8; font-weight: 700; font-size: 0.75rem;">🔑 ${act}</span>`;
                } else if (a.includes('FAILED') || a.includes('DELETE')) {
                    return `<span style="padding: 3px 8px; border-radius: 6px; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.35); color: #f87171; font-weight: 700; font-size: 0.75rem;">⚠️ ${act}</span>`;
                } else if (a.includes('CREATE') || a.includes('GENERATE')) {
                    return `<span style="padding: 3px 8px; border-radius: 6px; background: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34, 197, 94, 0.35); color: #4ade80; font-weight: 700; font-size: 0.75rem;">✨ ${act}</span>`;
                } else if (a.includes('UPDATE') || a.includes('MOVE')) {
                    return `<span style="padding: 3px 8px; border-radius: 6px; background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.35); color: #fbbf24; font-weight: 700; font-size: 0.75rem;">📝 ${act}</span>`;
                } else if (a.includes('EMAIL')) {
                    return `<span style="padding: 3px 8px; border-radius: 6px; background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.35); color: #c084fc; font-weight: 700; font-size: 0.75rem;">✉️ ${act}</span>`;
                }
                return `<span style="padding: 3px 8px; border-radius: 6px; background: rgba(148, 163, 184, 0.15); border: 1px solid rgba(148, 163, 184, 0.35); color: #cbd5e1; font-weight: 700; font-size: 0.75rem;">📌 ${act}</span>`;
            };

            tableBody.innerHTML = logs.map(l => {
                let detailsStr = '-';
                if (l.details) {
                    try {
                        const parsed = typeof l.details === 'string' ? JSON.parse(l.details) : l.details;
                        detailsStr = `<code style="background: rgba(0,0,0,0.4); padding: 3px 6px; border-radius: 4px; color: #a7f3d0; font-size: 0.76rem;">${JSON.stringify(parsed)}</code>`;
                    } catch(e) {
                        detailsStr = `<span style="color: #cbd5e1; font-size: 0.78rem;">${l.details}</span>`;
                    }
                }

                const entityStr = (l.entity_type || l.entity_id) 
                    ? `<span style="color: #94a3b8; font-size: 0.78rem;">${l.entity_type || ''}</span> ${l.entity_id ? `<strong style="color: #38bdf8;">#${l.entity_id}</strong>` : ''}`
                    : '-';

                return `
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); transition: background 0.15s ease;" onmouseover="this.style.background='rgba(255,255,255,0.02)'" onmouseout="this.style.background='transparent'">
                        <td style="padding: 10px 16px; color: #94a3b8; white-space: nowrap; font-family: monospace; font-size: 0.78rem;">${l.timestamp}</td>
                        <td style="padding: 10px 16px; font-weight: 700; color: #fff;">👤 ${l.username || 'SYSTEM'}</td>
                        <td style="padding: 10px 16px;">${getActionBadge(l.action)}</td>
                        <td style="padding: 10px 16px;">${entityStr}</td>
                        <td style="padding: 10px 16px; color: #64748b; font-family: monospace; font-size: 0.76rem;">${l.ip_address || '-'}</td>
                        <td style="padding: 10px 16px; max-width: 320px; overflow: hidden; text-overflow: ellipsis;">${detailsStr}</td>
                    </tr>
                `;
            }).join('');
        }

        function changeAuditPage(delta) {
            const newPage = auditCurrentPage + delta;
            if (newPage >= 1 && newPage <= auditTotalPages) {
                loadAuditLogs(newPage);
            }
        }

        function resetAuditFilters() {
            if (document.getElementById('auditSearchInput')) document.getElementById('auditSearchInput').value = '';
            if (document.getElementById('auditActionFilter')) document.getElementById('auditActionFilter').value = '';
            if (document.getElementById('auditStartDate')) document.getElementById('auditStartDate').value = '';
            if (document.getElementById('auditEndDate')) document.getElementById('auditEndDate').value = '';
            loadAuditLogs(1);
        }

        function exportAuditLogsCsv() {
            const search = document.getElementById('auditSearchInput')?.value || '';
            const action = document.getElementById('auditActionFilter')?.value || '';
            const startDate = document.getElementById('auditStartDate')?.value || '';
            const endDate = document.getElementById('auditEndDate')?.value || '';

            const params = new URLSearchParams({
                search: search,
                action: action,
                start_date: startDate,
                end_date: endDate
            });

            window.open(`/api/audit-logs/export?${params.toString()}`, '_blank');
        }

        // --- Helper to close all open app modals ---
        function closeAllAppModals() {
            ['coaModal', 'mappingsModal', 'historyModal', 'supportModal', 'customerModal', 'customerStorageModal', 'pdfViewerModal', 'customerChecklistModal', 'billingScheduleModal', 'billingInvoiceModal', 'billingInvoiceViewModal'].forEach(id => {
                const modal = document.getElementById(id);
                if (modal) {
                    modal.style.display = 'none';
                    modal.style.opacity = '0';
                }
            });
        }

        // ── BILLING MODULE CONTROLLER ──────────────────────────────────────────
        let billingAllInvoices = [];
        let billingAllSchedules = [];
        let billingActiveSubTab = 'invoices';

        async function initBillingModule() {
            console.log("[BILLING MODULE] Initializing Billing Dashboard...");
            await Promise.all([
                loadBillingOverview(),
                loadBillingInvoices(),
                loadBillingSchedules(),
                populateBillingCustomerDropdowns()
            ]);
        }

        async function loadBillingOverview() {
            try {
                const res = await fetch('/api/billing/overview');
                if (res.ok) {
                    const data = await res.json();
                    const mrrElem = document.getElementById('billingKpiMrr');
                    const subElem = document.getElementById('billingKpiSubscribers');
                    const colElem = document.getElementById('billingKpiCollected');
                    const outElem = document.getElementById('billingKpiOutstanding');

                    if (mrrElem) mrrElem.innerHTML = `$${(data.mrr || 0).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})} <span style="font-size: 0.85rem; color: #94a3b8; font-weight: 400;">/ mo</span>`;
                    if (subElem) subElem.innerText = data.active_subscribers || 0;
                    if (colElem) colElem.innerText = `$${(data.total_collected || 0).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                    if (outElem) outElem.innerText = `$${(data.total_outstanding || 0).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                }
            } catch (err) {
                console.error("[BILLING OVERVIEW ERROR]:", err);
            }
        }

        async function populateBillingCustomerDropdowns() {
            try {
                const res = await fetch('/api/customers?business_only=true');
                if (res.ok) {
                    const data = await res.json();
                    const customers = data.customers || [];
                    const optionsHtml = '<option value="">-- Select Client / Customer --</option>' +
                        customers.map(c => {
                            const name = c.legal_name || c.display_name || ('Customer #' + c.id);
                            const num = c.custumer_number || ('CUST-' + c.id);
                            return `<option value="${c.id}">${name} (${num})</option>`;
                        }).join('');
                    
                    const schedSelect = document.getElementById('scheduleCustomerSelect');
                    const invSelect = document.getElementById('invoiceCustomerSelect');
                    if (schedSelect) schedSelect.innerHTML = optionsHtml;
                    if (invSelect) invSelect.innerHTML = optionsHtml;
                }
            } catch (err) {
                console.error("[BILLING CUSTOMER DROPDOWN ERROR]:", err);
            }
        }

        function switchBillingSubTab(tabName) {
            billingActiveSubTab = tabName;
            const invBtn = document.getElementById('billingTabBtnInvoices');
            const schedBtn = document.getElementById('billingTabBtnSchedules');
            const invSec = document.getElementById('billingInvoicesSection');
            const schedSec = document.getElementById('billingSchedulesSection');
            const filters = document.getElementById('billingInvoiceFilters');

            if (tabName === 'invoices') {
                if (invBtn) { invBtn.style.background = 'var(--primary-grad)'; invBtn.style.color = '#fff'; }
                if (schedBtn) { schedBtn.style.background = 'transparent'; schedBtn.style.color = '#94a3b8'; }
                if (invSec) invSec.style.display = 'block';
                if (schedSec) schedSec.style.display = 'none';
                if (filters) filters.style.display = 'flex';
            } else {
                if (schedBtn) { schedBtn.style.background = 'linear-gradient(135deg, #c084fc, #9333ea)'; schedBtn.style.color = '#fff'; }
                if (invBtn) { invBtn.style.background = 'transparent'; invBtn.style.color = '#94a3b8'; }
                if (schedSec) schedSec.style.display = 'block';
                if (invSec) invSec.style.display = 'none';
                if (filters) filters.style.display = 'none';
            }
        }

        async function loadBillingInvoices() {
            const filterElem = document.getElementById('billingStatusFilterSelect');
            const statusFilter = filterElem ? filterElem.value : 'ALL';
            try {
                const res = await fetch(`/api/billing/invoices?status=${statusFilter}`);
                if (res.ok) {
                    const data = await res.json();
                    billingAllInvoices = Array.isArray(data) ? data : (data.invoices || data.data || []);
                    const cntElem = document.getElementById('billingInvoicesCount');
                    if (cntElem) cntElem.innerText = billingAllInvoices.length;
                    renderBillingInvoicesTable(billingAllInvoices);
                }
            } catch (err) {
                console.error("[LOAD INVOICES ERROR]:", err);
            }
        }

        function renderBillingInvoicesTable(invoices) {
            const tbody = document.getElementById('billingInvoicesTableBody');
            if (!tbody) return;

            if (!invoices || invoices.length === 0) {
                tbody.innerHTML = `<tr><td colSpan="8" style="padding: 30px; text-align: center; color: var(--text-muted);">No invoices found. Click <strong>+ Create Invoice</strong> to generate one.</td></tr>`;
                return;
            }

            tbody.innerHTML = invoices.map(inv => {
                let badgeStyle = "background: rgba(148, 163, 184, 0.15); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.3);";
                if (inv.status === 'PAID') badgeStyle = "background: rgba(74, 222, 128, 0.15); color: #4ade80; border: 1px solid rgba(74, 222, 128, 0.4);";
                else if (inv.status === 'SENT') badgeStyle = "background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4);";
                else if (inv.status === 'OVERDUE') badgeStyle = "background: rgba(248, 113, 113, 0.15); color: #f87171; border: 1px solid rgba(248, 113, 113, 0.4);";
                else if (inv.status === 'CANCELLED') badgeStyle = "background: rgba(100, 116, 139, 0.2); color: #64748b; border: 1px solid rgba(100, 116, 139, 0.3);";

                return `
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.04); transition: background 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.02)'" onmouseout="this.style.background='transparent'">
                        <td style="padding: 14px 18px; font-weight: 700; color: #38bdf8; font-family: monospace;">${inv.invoice_number}</td>
                        <td style="padding: 14px 18px;">
                            <strong style="color: #fff; display: block;">${inv.legal_name || 'Client #' + inv.customer_id}</strong>
                            <span style="font-size: 0.78rem; color: #94a3b8;">${inv.email || ''}</span>
                        </td>
                        <td style="padding: 14px 18px; color: #cbd5e1;">${formatDateMMDDYYYY(inv.issue_date)}</td>
                        <td style="padding: 14px 18px; color: #f87171; font-weight: 600;">${formatDateMMDDYYYY(inv.due_date)}</td>
                        <td style="padding: 14px 18px; color: #94a3b8; max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${inv.description || ''}</td>
                        <td style="padding: 14px 18px; font-weight: 800; color: #fff; font-size: 0.95rem;">$${parseFloat(inv.total_amount || 0).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        <td style="padding: 14px 18px;">
                            <span style="padding: 4px 10px; border-radius: 8px; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.5px; ${badgeStyle}">${inv.status}</span>
                        </td>
                        <td style="padding: 14px 18px; text-align: right;">
                            <div style="display: flex; gap: 6px; justify-content: flex-end;">
                                <button onclick="viewInvoiceHtml('${inv.id}', '${inv.invoice_number}')" title="View / Print Invoice HTML" style="padding: 6px 10px; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); color: #38bdf8; border-radius: 8px; cursor: pointer; font-size: 0.78rem; font-weight: 700;">📄 View</button>
                                ${inv.status !== 'PAID' && inv.status !== 'CANCELLED' ? `<button onclick="markInvoiceStatus('${inv.id}', 'PAID')" title="Mark as Paid" style="padding: 6px 10px; background: rgba(74, 222, 128, 0.15); border: 1px solid rgba(74, 222, 128, 0.3); color: #4ade80; border-radius: 8px; cursor: pointer; font-size: 0.78rem; font-weight: 700;">✅ Paid</button>` : ''}
                                ${inv.status !== 'CANCELLED' ? `<button onclick="sendInvoiceEmail('${inv.id}')" title="Send Resend Email to Client" style="padding: 6px 10px; background: rgba(192, 132, 252, 0.15); border: 1px solid rgba(192, 132, 252, 0.3); color: #c084fc; border-radius: 8px; cursor: pointer; font-size: 0.78rem; font-weight: 700;">✉️ Email</button>` : ''}
                                ${inv.status !== 'CANCELLED' ? `<button onclick="voidInvoice('${inv.id}', '${inv.invoice_number}')" title="Void Invoice & Revert Schedule Date" style="padding: 6px 10px; background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3); color: #f59e0b; border-radius: 8px; cursor: pointer; font-size: 0.78rem; font-weight: 700;">🚫 Void</button>` : ''}
                                <button onclick="deleteInvoice('${inv.id}')" title="Delete Invoice Record" style="padding: 6px 10px; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); color: #f87171; border-radius: 8px; cursor: pointer; font-size: 0.78rem; font-weight: 700;">🗑️</button>
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        async function loadBillingSchedules() {
            try {
                const res = await fetch('/api/billing/schedules');
                if (res.ok) {
                    const data = await res.json();
                    billingAllSchedules = Array.isArray(data) ? data : (data.schedules || data.data || []);
                    const cntElem = document.getElementById('billingSchedulesCount');
                    if (cntElem) cntElem.innerText = billingAllSchedules.length;
                    renderBillingSchedulesTable(billingAllSchedules);
                }
            } catch (err) {
                console.error("[LOAD SCHEDULES ERROR]:", err);
            }
        }

        function renderBillingSchedulesTable(schedules) {
            const tbody = document.getElementById('billingSchedulesTableBody');
            if (!tbody) return;

            if (!schedules || schedules.length === 0) {
                tbody.innerHTML = `<tr><td colSpan="8" style="padding: 30px; text-align: center; color: var(--text-muted);">No recurring billing schedules configured. Click <strong onclick="openCreateScheduleModal()" style="cursor: pointer; color: #c084fc; text-decoration: underline;">+ New Schedule</strong> to create one.</td></tr>`;
                return;
            }

            tbody.innerHTML = schedules.map(s => `
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.04); transition: background 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.02)'" onmouseout="this.style.background='transparent'">
                    <td style="padding: 14px 18px;">
                        <strong style="color: #fff; display: block;">${s.legal_name || 'Client #' + s.customer_id}</strong>
                        <span style="font-size: 0.78rem; color: #94a3b8;">${s.custumer_number || ''}</span>
                    </td>
                    <td style="padding: 14px 18px; font-weight: 800; color: #c084fc; font-size: 0.95rem;">$${parseFloat(s.billing_amount || 0).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})} / mo</td>
                    <td style="padding: 14px 18px; color: #38bdf8; font-weight: 700;">Day ${s.billing_day} of month</td>
                    <td style="padding: 14px 18px; color: #cbd5e1;">${(s.payment_terms_days === 0) ? 'Due Upon Receipt' : ('Net ' + (s.payment_terms_days ?? 30) + ' Days')}</td>
                    <td style="padding: 14px 18px;">
                        ${s.auto_send ? `<span style="color: #4ade80; font-weight: 700;">✓ Enabled</span>` : `<span style="color: #64748b;">Disabled</span>`}
                    </td>
                    <td style="padding: 14px 18px; color: #94a3b8;">${s.last_billed_at ? new Date(s.last_billed_at).toLocaleDateString() : 'Never'}</td>
                    <td style="padding: 14px 18px;">
                        <span style="padding: 4px 10px; border-radius: 8px; font-size: 0.75rem; font-weight: 800; background: rgba(74, 222, 128, 0.15); color: #4ade80; border: 1px solid rgba(74, 222, 128, 0.4);">${s.status || 'Active'}</span>
                    </td>
                    <td style="padding: 14px 18px; text-align: right; white-space: nowrap;">
                        <button onclick="editSchedule('${s.id}')" title="Edit Recurring Schedule" style="padding: 6px 12px; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); color: #38bdf8; border-radius: 8px; cursor: pointer; font-size: 0.78rem; font-weight: 700; margin-right: 6px;">✏️ Edit</button>
                        <button onclick="deleteSchedule('${s.id}')" title="Delete Recurring Schedule" style="padding: 6px 12px; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); color: #f87171; border-radius: 8px; cursor: pointer; font-size: 0.78rem; font-weight: 700;">🗑️ Delete</button>
                    </td>
                </tr>
            `).join('');
        }

        function filterBillingTable() {
            const input = document.getElementById('billingSearchInput');
            const query = (input ? input.value : '').toLowerCase().trim();
            if (billingActiveSubTab === 'invoices') {
                const filtered = billingAllInvoices.filter(inv => 
                    (inv.invoice_number || '').toLowerCase().includes(query) ||
                    (inv.legal_name || '').toLowerCase().includes(query) ||
                    (inv.description || '').toLowerCase().includes(query)
                );
                renderBillingInvoicesTable(filtered);
            } else {
                const filtered = billingAllSchedules.filter(s => 
                    (s.legal_name || '').toLowerCase().includes(query) ||
                    (s.custumer_number || '').toLowerCase().includes(query) ||
                    (s.description || '').toLowerCase().includes(query)
                );
                renderBillingSchedulesTable(filtered);
            }
        }

        // --- Modals Control Functions ---
        function openCreateScheduleModal() {
            closeAllAppModals();
            populateBillingCustomerDropdowns();
            const idElem = document.getElementById('scheduleFormId');
            if (idElem) idElem.value = '';
            const titleElem = document.getElementById('scheduleModalTitleText');
            if (titleElem) titleElem.innerText = '🔄 New Recurring Billing Schedule';
            const submitBtn = document.getElementById('scheduleSubmitBtn');
            if (submitBtn) submitBtn.innerText = 'Create Schedule';
            const modal = document.getElementById('billingScheduleModal');
            if (modal) {
                modal.style.display = 'flex';
                modal.style.opacity = '1';
            }
        }

        async function editSchedule(scheduleId) {
            closeAllAppModals();
            await populateBillingCustomerDropdowns();
            const sched = billingAllSchedules.find(s => String(s.id) === String(scheduleId));
            if (!sched) return;

            const idElem = document.getElementById('scheduleFormId');
            if (idElem) idElem.value = scheduleId;

            const custSelect = document.getElementById('scheduleCustomerSelect');
            if (custSelect) custSelect.value = sched.customer_id;

            const amtInput = document.getElementById('scheduleAmountInput');
            if (amtInput) amtInput.value = sched.billing_amount;

            const dayInput = document.getElementById('scheduleDayInput');
            if (dayInput) dayInput.value = sched.billing_day || 1;

            const descInput = document.getElementById('scheduleDescInput');
            if (descInput) descInput.value = sched.description || '';

            const termsSelect = document.getElementById('scheduleTermsSelect');
            if (termsSelect) termsSelect.value = (sched.payment_terms_days !== undefined && sched.payment_terms_days !== null) ? sched.payment_terms_days : 30;

            const autoCheck = document.getElementById('scheduleAutoSendCheck');
            if (autoCheck) autoCheck.checked = !!sched.auto_send;

            const titleElem = document.getElementById('scheduleModalTitleText');
            if (titleElem) titleElem.innerText = '✏️ Edit Recurring Billing Schedule';

            const submitBtn = document.getElementById('scheduleSubmitBtn');
            if (submitBtn) submitBtn.innerText = 'Save Schedule';

            const modal = document.getElementById('billingScheduleModal');
            if (modal) {
                modal.style.display = 'flex';
                modal.style.opacity = '1';
            }
        }

        function closeCreateScheduleModal() {
            const modal = document.getElementById('billingScheduleModal');
            if (modal) {
                modal.style.display = 'none';
            }
        }

        async function submitCreateSchedule(event) {
            event.preventDefault();
            const scheduleId = document.getElementById('scheduleFormId').value;
            const custVal = document.getElementById('scheduleCustomerSelect').value;
            const amtVal = document.getElementById('scheduleAmountInput').value;
            if (!custVal || !amtVal) {
                showCustomAlert("Input Error", "Please select a client and enter a valid monthly fee.", "error");
                return;
            }

            const payload = {
                customer_id: parseInt(custVal),
                billing_amount: parseFloat(amtVal),
                billing_day: parseInt(document.getElementById('scheduleDayInput').value || '1'),
                description: document.getElementById('scheduleDescInput').value || '',
                payment_terms_days: document.getElementById('scheduleTermsSelect').value !== "" ? parseInt(document.getElementById('scheduleTermsSelect').value) : 30,
                auto_send: document.getElementById('scheduleAutoSendCheck').checked
            };

            const isEdit = !!scheduleId;
            const url = isEdit ? `/api/billing/schedules/${scheduleId}` : '/api/billing/schedules';
            const method = isEdit ? 'PUT' : 'POST';

            try {
                const res = await fetch(url, {
                    method: method,
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                if (res.ok) {
                    closeCreateScheduleModal();
                    showCustomAlert("Success", isEdit ? "Recurring billing schedule updated!" : "Recurring billing schedule created successfully!", "success");
                    loadBillingOverview();
                    loadBillingSchedules();
                } else {
                    const err = await res.json();
                    showCustomAlert("Error", err.detail || "Failed to save schedule.", "error");
                }
            } catch (e) {
                showCustomAlert("Error", "Server error saving schedule.", "error");
            }
        }

        function openCreateInvoiceModal() {
            closeAllAppModals();
            populateBillingCustomerDropdowns();
            const modal = document.getElementById('billingInvoiceModal');
            if (modal) {
                const defaultDue = new Date();
                defaultDue.setDate(defaultDue.getDate() + 15);
                const dueElem = document.getElementById('invoiceDueDateInput');
                if (dueElem) dueElem.value = defaultDue.toISOString().split('T')[0];
                modal.style.display = 'flex';
                modal.style.opacity = '1';
            }
        }

        function closeCreateInvoiceModal() {
            const modal = document.getElementById('billingInvoiceModal');
            if (modal) {
                modal.style.display = 'none';
            }
        }

        async function submitCreateInvoice(event) {
            event.preventDefault();
            const custVal = document.getElementById('invoiceCustomerSelect').value;
            const amtVal = document.getElementById('invoiceAmountInput').value;
            if (!custVal || !amtVal) {
                showCustomAlert("Input Error", "Please select a client and enter a valid total amount.", "error");
                return;
            }

            const payload = {
                customer_id: parseInt(custVal),
                amount: parseFloat(amtVal),
                due_date: document.getElementById('invoiceDueDateInput').value,
                description: document.getElementById('invoiceDescInput').value || '',
                send_now: document.getElementById('invoiceSendNowCheck').checked
            };

            try {
                const res = await fetch('/api/billing/invoices', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                if (res.ok) {
                    const data = await res.json();
                    closeCreateInvoiceModal();
                    showCustomAlert("Success", `Invoice #${data.invoice_number} created successfully!`, "success");
                    loadBillingOverview();
                    loadBillingInvoices();
                } else {
                    const err = await res.json();
                    showCustomAlert("Error", err.detail || "Failed to create invoice.", "error");
                }
            } catch (e) {
                showCustomAlert("Error", "Server error creating invoice.", "error");
            }
        }

        async function sendInvoiceEmail(invoiceId) {
            if (!invoiceId) {
                showCustomAlert("Error", "Invalid invoice selection.", "error");
                return;
            }
            try {
                const res = await fetch(`/api/billing/invoices/${encodeURIComponent(invoiceId)}/send`, {method: 'POST'});
                let data = {};
                try { data = await res.json(); } catch (_) {}
                if (res.ok) {
                    showCustomAlert("Email Sent", data.message || "Invoice email sent successfully via Resend!", "success");
                    loadBillingOverview();
                    loadBillingInvoices();
                } else {
                    let errorMsg = "Failed to send invoice email.";
                    if (typeof data.detail === 'string') errorMsg = data.detail;
                    else if (Array.isArray(data.detail)) errorMsg = data.detail.map(d => typeof d === 'object' ? (d.msg || d.detail || JSON.stringify(d)) : String(d)).join(', ');
                    else if (data.message) errorMsg = data.message;
                    else if (res.statusText) errorMsg = `HTTP Error ${res.status}: ${res.statusText}`;
                    showCustomAlert("Error", errorMsg, "error");
                }
            } catch (e) {
                showCustomAlert("Error", e.message || "Server error sending email.", "error");
            }
        }

        async function markInvoiceStatus(invoiceId, newStatus) {
            try {
                const res = await fetch(`/api/billing/invoices/${invoiceId}/status`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({status: newStatus})
                });
                if (res.ok) {
                    showCustomAlert("Updated", `Invoice status set to ${newStatus}!`, "success");
                    loadBillingOverview();
                    loadBillingInvoices();
                } else {
                    let errorMsg = "Failed to update status.";
                    try {
                        const err = await res.json();
                        if (typeof err.detail === 'string') errorMsg = err.detail;
                        else if (Array.isArray(err.detail)) errorMsg = err.detail.map(d => d.msg || d.detail || JSON.stringify(d)).join(', ');
                        else if (err.message) errorMsg = err.message;
                    } catch (_) {}
                    showCustomAlert("Error", errorMsg, "error");
                }
            } catch (e) {
                showCustomAlert("Error", "Server error updating status.", "error");
            }
        }

        function viewInvoiceHtml(invoiceId, invoiceNumber) {
            closeAllAppModals();
            const modal = document.getElementById('billingInvoiceViewModal');
            const iframe = document.getElementById('invoiceViewIframe');
            const titleElem = document.getElementById('invoiceViewTitleText');
            if (titleElem) titleElem.innerText = `Invoice Preview (${invoiceNumber})`;
            if (iframe) iframe.src = `/api/billing/invoices/${invoiceId}/view`;
            if (modal) {
                modal.style.display = 'flex';
                modal.offsetHeight;
                modal.style.opacity = '1';
            }
        }

        function closeInvoiceViewModal() {
            const modal = document.getElementById('billingInvoiceViewModal');
            if (modal) {
                modal.style.opacity = '0';
                setTimeout(() => modal.style.display = 'none', 300);
            }
        }

        function printInvoiceFrame() {
            const iframe = document.getElementById('invoiceViewIframe');
            if (iframe && iframe.contentWindow) {
                iframe.contentWindow.focus();
                iframe.contentWindow.print();
            }
        }

        async function voidInvoice(invoiceId, invoiceNumber) {
            const confirmed = await showCustomConfirm(`Are you sure you want to VOID Invoice #${invoiceNumber}? This will mark the invoice as CANCELLED and automatically revert the recurring schedule's last billing date so it can be caught up.`, "Void Invoice", "Yes, Void Invoice", "Cancel");
            if (!confirmed) return;
            try {
                const res = await fetch(`/api/billing/invoices/${invoiceId}/status`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ status: 'CANCELLED', notes: `Voided by admin on ${new Date().toLocaleDateString()}` })
                });
                if (res.ok) {
                    showCustomAlert("Invoice Voided", `Invoice #${invoiceNumber} has been voided and the recurring schedule billing date was reverted.`, "success");
                    loadBillingOverview();
                    loadBillingInvoices();
                    if (typeof loadBillingSchedules === 'function') loadBillingSchedules();
                } else {
                    let errorMsg = "Failed to void invoice.";
                    try {
                        const err = await res.json();
                        errorMsg = err.detail || err.message || errorMsg;
                    } catch (_) {}
                    showCustomAlert("Error", errorMsg, "error");
                }
            } catch (e) {
                showCustomAlert("Error", "Server error voiding invoice.", "error");
            }
        }

        async function deleteInvoice(invoiceId) {
            const confirmed = await showCustomConfirm("Are you sure you want to permanently delete this invoice record? (Associated recurring schedule billing date will be automatically reverted)", "Delete Invoice", "Yes, Delete", "Cancel");
            if (!confirmed) return;
            try {
                const res = await fetch(`/api/billing/invoices/${invoiceId}`, {method: 'DELETE'});
                if (res.ok) {
                    showCustomAlert("Deleted", "Invoice deleted successfully and schedule billing date reverted.", "success");
                    loadBillingOverview();
                    loadBillingInvoices();
                    if (typeof loadBillingSchedules === 'function') loadBillingSchedules();
                } else {
                    let errorMsg = "Failed to delete invoice.";
                    try {
                        const err = await res.json();
                        if (typeof err.detail === 'string') errorMsg = err.detail;
                        else if (Array.isArray(err.detail)) errorMsg = err.detail.map(d => d.msg || d.detail || JSON.stringify(d)).join(', ');
                        else if (err.message) errorMsg = err.message;
                    } catch (_) {}
                    showCustomAlert("Error", errorMsg, "error");
                }
            } catch (e) {
                showCustomAlert("Error", "Server error deleting invoice.", "error");
            }
        }

        async function deleteSchedule(scheduleId) {
            const confirmed = await showCustomConfirm("Are you sure you want to delete this recurring billing schedule?", "Delete Schedule", "Yes, Delete", "Cancel");
            if (!confirmed) return;
            try {
                const res = await fetch(`/api/billing/schedules/${scheduleId}`, {method: 'DELETE'});
                if (res.ok) {
                    showCustomAlert("Deleted", "Recurring schedule deleted successfully.", "success");
                    loadBillingOverview();
                    loadBillingSchedules();
                } else {
                    let errorMsg = "Failed to delete schedule.";
                    try {
                        const err = await res.json();
                        if (typeof err.detail === 'string') errorMsg = err.detail;
                        else if (Array.isArray(err.detail)) errorMsg = err.detail.map(d => d.msg || d.detail || JSON.stringify(d)).join(', ');
                        else if (err.message) errorMsg = err.message;
                    } catch (_) {}
                    showCustomAlert("Error", errorMsg, "error");
                }
            } catch (e) {
                showCustomAlert("Error", "Server error deleting schedule.", "error");
            }
        }

        async function triggerDailyBillingJob() {
            try {
                const res = await fetch('/api/billing/run-scheduler', {method: 'POST'});
                if (res.ok) {
                    const data = await res.json();
                    if (data.status === "error") {
                        showCustomAlert("Scheduler Error", data.message || "Failed to run billing job.", "error");
                        return;
                    }
                    showCustomAlert("Scheduler Triggered", `Generated ${data.generated_count || 0} recurring invoice(s) (including past-due catch-up for actual date and earlier days in current month).`, "success");
                    loadBillingOverview();
                    loadBillingInvoices();
                } else {
                    let errorMsg = "Failed to run billing job.";
                    try {
                        const err = await res.json();
                        errorMsg = err.detail || err.message || errorMsg;
                    } catch (_) {}
                    showCustomAlert("Error", errorMsg, "error");
                }
            } catch (e) {
                showCustomAlert("Error", "Server error running billing job.", "error");
            }
        }

        // --- Support Modal Logic ---
        function openSupportModal() {
            closeAllAppModals();
            const modal = document.getElementById('supportModal');
            if (!modal) return;
            if (modal.parentElement !== document.body) document.body.appendChild(modal);
            modal.style.display = 'flex';
            modal.offsetHeight;
            modal.style.opacity = '1';
            if (document.getElementById('supportModalContent')) {
                document.getElementById('supportModalContent').style.transform = 'scale(1)';
            }
        }

        function closeSupportModal() {
            const modal = document.getElementById('supportModal');
            if (!modal) return;
            modal.style.opacity = '0';
            if (document.getElementById('supportModalContent')) {
                document.getElementById('supportModalContent').style.transform = 'scale(0.9)';
            }
            setTimeout(() => { modal.style.display = 'none'; }, 300);
        }

        const supportAttachmentArea = document.getElementById('supportAttachmentArea');
        const supportFileInput = document.getElementById('supportFileInput');
        if (supportAttachmentArea && supportFileInput) {
            supportAttachmentArea.addEventListener('click', () => supportFileInput.click());
            supportFileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    supportAttachedFile = e.target.files[0];
                    document.getElementById('supportFileText').textContent = supportAttachedFile.name;
                }
            });
        }

        async function sendSupportEmail() {
            const msgVal = document.getElementById('supportMessage').value.trim();
            if (!msgVal) {
                alert('Please enter a message.');
                return;
            }
            const btn = document.getElementById('sendSupportBtn');
            btn.disabled = true;
            btn.textContent = 'Sending...';

            const formData = new FormData();
            formData.append('message', msgVal);
            if (supportAttachedFile) {
                formData.append('file', supportAttachedFile);
            }

            try {
                const response = await fetch('/support', { method: 'POST', body: formData });
                if (response.ok) {
                    alert('Support email sent successfully!');
                    closeSupportModal();
                } else {
                    const errText = await response.text();
                    alert('Failed to send support email: ' + errText);
                }
            } catch (error) {
                alert('Error sending support email: ' + error.message);
            } finally {
                btn.disabled = false;
                btn.textContent = 'Send Email';
            }
        }

        // --- Dropdown Sync ---
        async function syncClientSelectDropdowns() {
            try {
                const [mapRes, custRes] = await Promise.all([
                    fetch(`/api/clients/parent-mappings?parentName=${encodeURIComponent(CURRENT_PARENT_NAME)}`).catch(() => null),
                    fetch('/api/customers?business_only=true').catch(() => null)
                ]);

                let clientList = [];

                if (mapRes && mapRes.ok) {
                    const data = await mapRes.json();
                    currentParentMappings = data.mappings || [];
                    clientList.push(...currentParentMappings.map(m => m.clientName.trim()));
                }

                if (custRes && custRes.ok) {
                    const custData = await custRes.json();
                    const customers = custData.customers || [];
                    clientList.push(...customers.map(c => (c.legal_name || '').trim()).filter(Boolean));
                }

                clientList = Array.from(new Set(clientList)).filter(Boolean);
                if (clientList.length === 0) clientList = [CURRENT_PARENT_NAME];

                ['coaClientSelect', 'historyClientSelect'].forEach(id => {
                    const sel = document.getElementById(id);
                    if (sel) {
                        const curVal = sel.value;
                        sel.innerHTML = clientList.map(n => `<option value="${n}">${n}</option>`).join('');
                        if (curVal && clientList.includes(curVal)) sel.value = curVal;
                        else sel.value = clientList[0];
                    }
                });
            } catch (err) {
                console.error('Error syncing client dropdowns:', err);
            }
        }

        // --- COA Modal Functions ---
        async function openCoaModal() {
            closeAllAppModals();
            const modal = document.getElementById('coaModal');
            if (!modal) return;
            if (modal.parentElement !== document.body) document.body.appendChild(modal);
            modal.style.display = 'flex';
            modal.offsetHeight;
            modal.style.opacity = '1';
            if (modal.children[0]) modal.children[0].style.transform = 'scale(1)';
            await syncClientSelectDropdowns();
            await fetchCoaRecords();
        }

        function closeCoaModal() {
            const modal = document.getElementById('coaModal');
            if (!modal) return;
            modal.style.opacity = '0';
            if (modal.children[0]) modal.children[0].style.transform = 'scale(0.95)';
            setTimeout(() => { modal.style.display = 'none'; }, 300);
        }

        async function fetchCoaRecords() {
            const clientSelect = document.getElementById('coaClientSelect');
            const clientName = clientSelect ? clientSelect.value.trim() : CURRENT_PARENT_NAME;
            const tbody = document.getElementById('coaTableBody');
            if (tbody) tbody.innerHTML = '<tr><td colSpan="5" style="padding: 24px; text-align: center; color: #94a3b8;">Loading accounts...</td></tr>';
            try {
                const res = await fetch(`/api/clients/coa?clientName=${encodeURIComponent(clientName)}&parentName=${encodeURIComponent(CURRENT_PARENT_NAME)}`);
                const data = await res.json();
                currentCoaRecords = data.accounts || [];
                renderCoaTable();
            } catch (err) {
                console.error('Error fetching COA:', err);
                if (tbody) tbody.innerHTML = '<tr><td colSpan="5" style="padding: 24px; text-align: center; color: #ff5252;">Failed to load accounts.</td></tr>';
            }
        }

        function renderCoaTable() {
            const query = (document.getElementById('coaSearchInput')?.value || '').toLowerCase();
            const tbody = document.getElementById('coaTableBody');
            const totalCount = document.getElementById('coaTotalCount');
            if (!tbody) return;

            const filtered = currentCoaRecords.filter(a =>
                (a.accountNumber || '').toLowerCase().includes(query) ||
                (a.accountName || '').toLowerCase().includes(query) ||
                (a.type || '').toLowerCase().includes(query)
            );
            if (totalCount) totalCount.textContent = filtered.length;

            if (filtered.length === 0) {
                tbody.innerHTML = '<tr><td colSpan="5" style="padding: 24px; text-align: center; color: #64748b;">No accounts found. Click ➕ Add Account or Upload CSV.</td></tr>';
                return;
            }

            tbody.innerHTML = filtered.map(acct => `
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); transition: background 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.03)'" onmouseout="this.style.background='transparent'">
                    <td style="padding: 10px 16px; font-weight: 700; color: #67e8f9;">${acct.parentName || CURRENT_PARENT_NAME}</td>
                    <td style="padding: 10px 16px; font-family: monospace; font-weight: 700; color: #22d3ee;">${acct.accountNumber}</td>
                    <td style="padding: 10px 16px; font-weight: 700; color: #fff;">${acct.accountName}</td>
                    <td style="padding: 10px 16px;">
                        <span style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); padding: 2px 8px; border-radius: 4px; font-size: 0.68rem; text-transform: uppercase; font-weight: 700; color: #cbd5e1;">${acct.type || 'Expense'}</span>
                    </td>
                    <td style="padding: 10px 16px; text-align: right;">
                        <button onclick="editCoaRecord('${acct.id || ''}', '${acct.accountNumber.replace(/'/g, "\\'")}', '${acct.accountName.replace(/'/g, "\\'")}', '${(acct.type || 'Expense').replace(/'/g, "\\'")}')" style="padding: 4px 10px; background: rgba(6,182,212,0.15); border: 1px solid rgba(6,182,212,0.3); color: #67e8f9; border-radius: 6px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; cursor: pointer; margin-right: 6px;">Edit</button>
                        <button onclick="deleteCoaRecord('${acct.id || ''}')" style="padding: 4px 10px; background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.3); color: #f87171; border-radius: 6px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; cursor: pointer;">Delete</button>
                    </td>
                </tr>
            `).join('');
        }

        function toggleCoaForm() {
            const form = document.getElementById('coaForm');
            const btn = document.getElementById('toggleCoaFormBtn');
            if (!form) return;
            if (form.style.display === 'none' || !form.style.display) {
                document.getElementById('coaFormId').value = '';
                document.getElementById('coaFormNumber').value = '';
                document.getElementById('coaFormName').value = '';
                document.getElementById('coaFormType').value = 'Expense';
                document.getElementById('coaFormSubmitBtn').textContent = 'Save Account';
                form.style.display = 'grid';
                if (btn) btn.textContent = 'Cancel';
            } else {
                form.style.display = 'none';
                if (btn) btn.textContent = '➕ Add Account';
            }
        }

        function editCoaRecord(id, number, name, type) {
            const form = document.getElementById('coaForm');
            const btn = document.getElementById('toggleCoaFormBtn');
            if (!form) return;
            document.getElementById('coaFormId').value = id;
            document.getElementById('coaFormNumber').value = number;
            document.getElementById('coaFormName').value = name;
            document.getElementById('coaFormType').value = type || 'Expense';
            document.getElementById('coaFormSubmitBtn').textContent = 'Update Account';
            form.style.display = 'grid';
            if (btn) btn.textContent = 'Cancel';
        }

        async function saveCoaRecord(e) {
            e.preventDefault();
            const id = document.getElementById('coaFormId').value;
            const clientSelect = document.getElementById('coaClientSelect');
            const clientName = clientSelect ? clientSelect.value.trim() : CURRENT_PARENT_NAME;
            const accountNumber = document.getElementById('coaFormNumber').value.trim();
            const accountName = document.getElementById('coaFormName').value.trim();
            const type = document.getElementById('coaFormType').value;

            try {
                const method = id ? 'PUT' : 'POST';
                const res = await fetch('/api/clients/coa', {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id, clientName, parentName: CURRENT_PARENT_NAME, accountNumber, accountName, type })
                });
                if (res.ok) {
                    toggleCoaForm();
                    fetchCoaRecords();
                } else {
                    const err = await res.json();
                    alert('Error saving COA: ' + (err.detail || err.error || 'Failed'));
                }
            } catch (err) {
                alert('Error saving COA: ' + err.message);
            }
        }

        async function deleteCoaRecord(id) {
            if (!id) return;
            if (!await showCustomConfirm('Are you sure you want to delete this account?')) return;
            try {
                const res = await fetch(`/api/clients/coa?id=${encodeURIComponent(id)}`, { method: 'DELETE' });
                if (res.ok) fetchCoaRecords();
                else alert('Failed to delete account.');
            } catch (err) {
                alert('Error deleting account: ' + err.message);
            }
        }

        async function handleCoaCsvUpload(input) {
            const file = input.files?.[0];
            if (!file) return;
            const clientSelect = document.getElementById('coaClientSelect');
            const clientName = clientSelect ? clientSelect.value.trim() : CURRENT_PARENT_NAME;
            const formData = new FormData();
            formData.append('clientName', clientName);
            formData.append('parentName', CURRENT_PARENT_NAME);
            formData.append('file', file);

            try {
                const res = await fetch('/api/clients/upload-coa', { method: 'POST', body: formData });
                const data = await res.json();
                if (res.ok) {
                    alert(data.message || 'COA uploaded successfully!');
                    fetchCoaRecords();
                } else {
                    alert('Error uploading COA CSV: ' + (data.detail || data.error || 'Failed'));
                }
            } catch (err) {
                alert('Error uploading file: ' + err.message);
            } finally {
                input.value = '';
            }
        }

        // --- Parent Mappings Modal Functions ---
        async function openMappingsModal() {
            closeAllAppModals();
            const modal = document.getElementById('mappingsModal');
            if (!modal) return;
            if (modal.parentElement !== document.body) document.body.appendChild(modal);
            modal.style.display = 'flex';
            modal.offsetHeight;
            modal.style.opacity = '1';
            if (modal.children[0]) modal.children[0].style.transform = 'scale(1)';
            await populateCustomerDropdownForMappings();
            fetchParentMappings();
        }

        function closeMappingsModal() {
            const modal = document.getElementById('mappingsModal');
            if (!modal) return;
            modal.style.opacity = '0';
            if (modal.children[0]) modal.children[0].style.transform = 'scale(0.95)';
            setTimeout(() => { modal.style.display = 'none'; }, 300);
        }

        async function populateCustomerDropdownForMappings() {
            const selectEl = document.getElementById('mapFormClientSelect');
            const customEl = document.getElementById('mapFormClientCustom');
            if (!selectEl) return;

            selectEl.innerHTML = '<option value="" disabled selected>Loading customers from CRM...</option>';
            try {
                const res = await fetch('/api/customers?business_only=true');
                const data = await res.json();
                const customers = data.customers || [];

                let optionsHtml = '<option value="" disabled selected>-- Select a Customer --</option>';
                customers.forEach(c => {
                    const name = (c.legal_name || '').trim();
                    if (!name) return;
                    optionsHtml += `<option value="${name.replace(/"/g, '&quot;')}">${name} (${c.custumer_number})</option>`;
                });
                optionsHtml += '<option value="__custom__">✍️ Enter Custom Client Name...</option>';
                selectEl.innerHTML = optionsHtml;

                if (customers.length === 0) {
                    selectEl.value = '__custom__';
                    onMapFormClientSelectChange();
                } else {
                    if (customEl) customEl.style.display = 'none';
                }
            } catch (err) {
                console.error('Error loading customers for dropdown:', err);
                selectEl.innerHTML = '<option value="__custom__" selected>✍️ Enter Custom Client Name...</option>';
                onMapFormClientSelectChange();
            }
        }

        function onMapFormClientSelectChange() {
            const selectEl = document.getElementById('mapFormClientSelect');
            const customEl = document.getElementById('mapFormClientCustom');
            if (!selectEl || !customEl) return;

            if (selectEl.value === '__custom__') {
                customEl.style.display = 'block';
                customEl.required = true;
                customEl.focus();
            } else {
                customEl.style.display = 'none';
                customEl.required = false;
            }
        }

        async function fetchParentMappings() {
            const tbody = document.getElementById('mappingsTableBody');
            if (tbody) tbody.innerHTML = '<tr><td colSpan="3" style="padding: 24px; text-align: center; color: #94a3b8;">Loading mappings...</td></tr>';
            try {
                const res = await fetch(`/api/clients/parent-mappings?parentName=${encodeURIComponent(CURRENT_PARENT_NAME)}`);
                const data = await res.json();
                currentParentMappings = (data.mappings || []).filter(m =>
                    (m.parentName || '').trim().toLowerCase() === CURRENT_PARENT_NAME.trim().toLowerCase()
                );
                renderMappingsTable();
            } catch (err) {
                console.error('Error fetching mappings:', err);
                if (tbody) tbody.innerHTML = '<tr><td colSpan="3" style="padding: 24px; text-align: center; color: #ff5252;">Failed to load mappings.</td></tr>';
            }
        }

        function renderMappingsTable() {
            const tbody = document.getElementById('mappingsTableBody');
            const totalCount = document.getElementById('mappingsTotalCount');
            if (!tbody) return;
            if (totalCount) totalCount.textContent = currentParentMappings.length;

            if (currentParentMappings.length === 0) {
                tbody.innerHTML = '<tr><td colSpan="2" style="padding: 24px; text-align: center; color: #64748b;">No client mappings found.</td></tr>';
                return;
            }

            tbody.innerHTML = currentParentMappings.map(m => `
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); transition: background 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.03)'" onmouseout="this.style.background='transparent'">
                    <td style="padding: 10px 16px; font-weight: 700; color: #c084fc;">${m.parentName}</td>
                    <td style="padding: 10px 16px; font-weight: 700; color: #fff;">${m.clientName}</td>
                </tr>
            `).join('');
        }

        async function saveParentMappingRecord(e) {
            e.preventDefault();
            const parentName = document.getElementById('mapFormParent').value.trim() || CURRENT_PARENT_NAME;
            const selectEl = document.getElementById('mapFormClientSelect');
            const customEl = document.getElementById('mapFormClientCustom');
            const clientName = (selectEl.value === '__custom__') ? customEl.value.trim() : selectEl.value.trim();

            if (!clientName) {
                alert('Please select or enter a client name.');
                return;
            }

            try {
                const res = await fetch('/api/clients/parent-mappings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ parentName, clientName })
                });
                if (res.ok) {
                    selectEl.value = '';
                    if (customEl) customEl.value = '';
                    await fetchParentMappings();
                    await syncClientSelectDropdowns();
                } else {
                    const err = await res.json();
                    alert('Error saving mapping: ' + (err.detail || err.error || 'Failed'));
                }
            } catch (err) {
                alert('Error saving mapping: ' + err.message);
            }
        }

        async function deleteParentMappingRecord(id) {
            if (!id) return;
            if (!await showCustomConfirm('Are you sure you want to delete this mapping?')) return;
            try {
                const res = await fetch(`/api/clients/parent-mappings?id=${encodeURIComponent(id)}`, { method: 'DELETE' });
                if (res.ok) {
                    await fetchParentMappings();
                    await syncClientSelectDropdowns();
                } else alert('Failed to delete mapping.');
            } catch (err) {
                alert('Error deleting mapping: ' + err.message);
            }
        }

        // --- History Rules Modal Functions ---
        async function openHistoryModal() {
            closeAllAppModals();
            const modal = document.getElementById('historyModal');
            if (!modal) return;
            if (modal.parentElement !== document.body) document.body.appendChild(modal);
            modal.style.display = 'flex';
            modal.offsetHeight;
            modal.style.opacity = '1';
            if (modal.children[0]) modal.children[0].style.transform = 'scale(1)';
            await syncClientSelectDropdowns();
            fetchHistoryRecords();
        }

        function closeHistoryModal() {
            const modal = document.getElementById('historyModal');
            if (!modal) return;
            modal.style.opacity = '0';
            if (modal.children[0]) modal.children[0].style.transform = 'scale(0.95)';
            setTimeout(() => { modal.style.display = 'none'; }, 300);
        }

        async function fetchHistoryRecords() {
            const clientSelect = document.getElementById('historyClientSelect');
            const clientName = clientSelect ? clientSelect.value.trim() : CURRENT_PARENT_NAME;
            const tbody = document.getElementById('historyTableBody');
            if (tbody) tbody.innerHTML = '<tr><td colSpan="6" style="padding: 24px; text-align: center; color: #94a3b8;">Loading history rules...</td></tr>';
            try {
                const res = await fetch(`/api/clients/history?clientName=${encodeURIComponent(clientName)}&parentName=${encodeURIComponent(CURRENT_PARENT_NAME)}`);
                const data = await res.json();
                currentHistoryRecords = data.historyRules || [];
                renderHistoryTable();
            } catch (err) {
                console.error('Error fetching history rules:', err);
                if (tbody) tbody.innerHTML = '<tr><td colSpan="6" style="padding: 24px; text-align: center; color: #ff5252;">Failed to load history rules.</td></tr>';
            }
        }

        function handleHistorySort(key) {
            if (historySortKey === key) {
                historySortOrder = historySortOrder === 'asc' ? 'desc' : 'asc';
            } else {
                historySortKey = key;
                historySortOrder = 'asc';
            }
            renderHistoryTable();
        }

        function renderHistoryTable() {
            const query = (document.getElementById('historySearchInput')?.value || '').toLowerCase();
            const tbody = document.getElementById('historyTableBody');
            const totalCount = document.getElementById('historyTotalCount');
            if (!tbody) return;

            let filtered = currentHistoryRecords.filter(r =>
                (r.pattern || '').toLowerCase().includes(query) ||
                (r.description || '').toLowerCase().includes(query) ||
                (r.accountNumber || '').toLowerCase().includes(query) ||
                (r.accountName || '').toLowerCase().includes(query)
            );

            if (historySortKey) {
                filtered.sort((a, b) => {
                    const valA = (a[historySortKey] || '').toString();
                    const valB = (b[historySortKey] || '').toString();
                    let cmp = valA.localeCompare(valB, undefined, { numeric: true, sensitivity: 'base' });
                    return historySortOrder === 'asc' ? cmp : -cmp;
                });
            }

            if (totalCount) totalCount.textContent = filtered.length;

            ['Pattern', 'Account', 'Name', 'Desc'].forEach(col => {
                const el = document.getElementById(`sort${col}Arrow`);
                if (el) el.textContent = '↕';
            });
            if (historySortKey === 'pattern' && document.getElementById('sortPatternArrow')) {
                document.getElementById('sortPatternArrow').textContent = historySortOrder === 'asc' ? '▲' : '▼';
            } else if (historySortKey === 'accountNumber' && document.getElementById('sortAccountArrow')) {
                document.getElementById('sortAccountArrow').textContent = historySortOrder === 'asc' ? '▲' : '▼';
            } else if (historySortKey === 'accountName' && document.getElementById('sortNameArrow')) {
                document.getElementById('sortNameArrow').textContent = historySortOrder === 'asc' ? '▲' : '▼';
            } else if (historySortKey === 'description' && document.getElementById('sortDescArrow')) {
                document.getElementById('sortDescArrow').textContent = historySortOrder === 'asc' ? '▲' : '▼';
            }

            if (filtered.length === 0) {
                tbody.innerHTML = '<tr><td colSpan="7" style="padding: 24px; text-align: center; color: #64748b;">No transaction rules found. Click ➕ Add Rule or Upload CSV.</td></tr>';
                return;
            }

            tbody.innerHTML = filtered.map(rule => `
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); transition: background 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.03)'" onmouseout="this.style.background='transparent'">
                    <td style="padding: 10px 16px; font-weight: 700; color: #6ee7b7;">${rule.parentName || CURRENT_PARENT_NAME}</td>
                    <td style="padding: 10px 16px; font-family: monospace; font-weight: 700; color: #34d399; text-transform: uppercase;">${rule.pattern}</td>
                    <td style="padding: 10px 16px; font-family: monospace; font-weight: 700; color: #22d3ee;">${rule.accountNumber}</td>
                    <td style="padding: 10px 16px; font-weight: 700; color: #fff;">${rule.accountName || '—'}</td>
                    <td style="padding: 10px 16px; color: #cbd5e1;">${rule.description || '—'}</td>
                    <td style="padding: 10px 16px;">
                        <span style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); padding: 2px 8px; border-radius: 4px; font-size: 0.68rem; text-transform: uppercase; font-weight: 700; color: #cbd5e1;">${rule.transactionType || 'ALL'}</span>
                    </td>
                    <td style="padding: 10px 16px; text-align: right;">
                        <button onclick="editHistoryRecord('${rule.id || ''}', '${(rule.pattern || '').replace(/'/g, "\\'")}', '${(rule.accountNumber || '').replace(/'/g, "\\'")}', '${(rule.accountName || '').replace(/'/g, "\\'")}', '${(rule.transactionType || 'ALL').replace(/'/g, "\\'")}', '${(rule.description || '').replace(/'/g, "\\'")}')" style="padding: 4px 10px; background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.3); color: #6ee7b7; border-radius: 6px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; cursor: pointer; margin-right: 6px;">Edit</button>
                        <button onclick="deleteHistoryRecord('${rule.id || ''}')" style="padding: 4px 10px; background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.3); color: #f87171; border-radius: 6px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; cursor: pointer;">Delete</button>
                    </td>
                </tr>
            `).join('');
        }

        function toggleHistoryForm() {
            const form = document.getElementById('historyForm');
            const btn = document.getElementById('toggleHistoryFormBtn');
            if (!form) return;
            if (form.style.display === 'none' || !form.style.display) {
                document.getElementById('historyFormId').value = '';
                document.getElementById('historyFormPattern').value = '';
                document.getElementById('historyFormNumber').value = '';
                document.getElementById('historyFormName').value = '';
                if (document.getElementById('historyFormDescription')) document.getElementById('historyFormDescription').value = '';
                document.getElementById('historyFormTxType').value = 'ALL';
                document.getElementById('historyFormSubmitBtn').textContent = 'Save Rule';
                form.style.display = 'grid';
                if (btn) btn.textContent = 'Cancel';
            } else {
                form.style.display = 'none';
                if (btn) btn.textContent = '➕ Add Rule';
            }
        }

        function editHistoryRecord(id, pattern, number, name, txType, description) {
            const form = document.getElementById('historyForm');
            const btn = document.getElementById('toggleHistoryFormBtn');
            if (!form) return;
            document.getElementById('historyFormId').value = id;
            document.getElementById('historyFormPattern').value = pattern;
            document.getElementById('historyFormNumber').value = number;
            document.getElementById('historyFormName').value = name || '';
            if (document.getElementById('historyFormDescription')) document.getElementById('historyFormDescription').value = description || '';
            document.getElementById('historyFormTxType').value = txType || 'ALL';
            document.getElementById('historyFormSubmitBtn').textContent = 'Update Rule';
            form.style.display = 'grid';
            if (btn) btn.textContent = 'Cancel';
        }

        async function saveHistoryRecord(e) {
            e.preventDefault();
            const id = document.getElementById('historyFormId').value;
            const clientSelect = document.getElementById('historyClientSelect');
            const clientName = clientSelect ? clientSelect.value.trim() : CURRENT_PARENT_NAME;
            const pattern = document.getElementById('historyFormPattern').value.trim();
            const accountNumber = document.getElementById('historyFormNumber').value.trim();
            const accountName = document.getElementById('historyFormName').value.trim();
            const description = document.getElementById('historyFormDescription') ? document.getElementById('historyFormDescription').value.trim() : '';
            const transactionType = document.getElementById('historyFormTxType').value;

            try {
                const method = id ? 'PUT' : 'POST';
                const res = await fetch('/api/clients/history', {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id, clientName, parentName: CURRENT_PARENT_NAME, pattern, accountNumber, accountName, transactionType, description })
                });
                if (res.ok) {
                    toggleHistoryForm();
                    fetchHistoryRecords();
                } else {
                    const err = await res.json();
                    alert('Error saving history rule: ' + (err.detail || err.error || 'Failed'));
                }
            } catch (err) {
                alert('Error saving history rule: ' + err.message);
            }
        }

        async function deleteHistoryRecord(id) {
            if (!id) return;
            if (!await showCustomConfirm('Are you sure you want to delete this rule?')) return;
            try {
                const res = await fetch(`/api/clients/history?id=${encodeURIComponent(id)}`, { method: 'DELETE' });
                if (res.ok) fetchHistoryRecords();
                else alert('Failed to delete rule.');
            } catch (err) {
                alert('Error deleting rule: ' + err.message);
            }
        }

        async function handleHistoryCsvUpload(input) {
            const file = input.files?.[0];
            if (!file) return;
            const clientSelect = document.getElementById('historyClientSelect');
            const clientName = clientSelect ? clientSelect.value.trim() : CURRENT_PARENT_NAME;
            const formData = new FormData();
            formData.append('clientName', clientName);
            formData.append('parentName', CURRENT_PARENT_NAME);
            formData.append('file', file);

            try {
                const res = await fetch('/api/clients/upload-history', { method: 'POST', body: formData });
                const data = await res.json();
                if (res.ok) {
                    alert(data.message || 'History rules uploaded successfully!');
                    fetchHistoryRecords();
                } else {
                    alert('Error uploading history CSV: ' + (data.detail || data.error || 'Failed'));
                }
            } catch (err) {
                alert('Error uploading file: ' + err.message);
            } finally {
                input.value = '';
            }
        }

        // --- Customer Management Functions ---
        let currentCustomerRecords = [];
        let currentCustomerList = [];

        async function openCustomerModal() {
            closeAllAppModals();
            const modal = document.getElementById('customerModal');
            if (!modal) return;
            modal.style.display = 'flex';
            modal.offsetHeight;
            modal.style.opacity = '1';
            if (modal.children[0]) modal.children[0].style.transform = 'scale(1)';
            fetchCustomerRecords();
        }

        function closeCustomerModal() {
            const modal = document.getElementById('customerModal');
            if (!modal) return;
            modal.style.opacity = '0';
            if (modal.children[0]) modal.children[0].style.transform = 'scale(0.95)';
            setTimeout(() => { modal.style.display = 'none'; }, 300);
        }

        async function fetchCustomerRecords(isPage = false) {
            const searchInput = isPage ? document.getElementById('customerPageSearchInput') : document.getElementById('customerSearchInput');
            const query = searchInput?.value || '';
            
            const modalTbody = document.getElementById('customerTableBody');
            const pageTbody = document.getElementById('customerPageTableBody');
            
            if (modalTbody) modalTbody.innerHTML = '<tr><td colSpan="8" style="padding: 24px; text-align: center; color: #94a3b8;">Loading customers...</td></tr>';
            if (pageTbody) pageTbody.innerHTML = '<tr><td colSpan="8" style="padding: 24px; text-align: center; color: #94a3b8;">Loading customers...</td></tr>';

            try {
                const parentName = typeof CURRENT_PARENT_NAME !== 'undefined' ? CURRENT_PARENT_NAME : (window.parentName || '');
                const res = await fetch(`/api/customers?query=${encodeURIComponent(query)}&parentName=${encodeURIComponent(parentName)}`);
                const data = await res.json();
                currentCustomerRecords = data.customers || [];
                currentCustomerList = currentCustomerRecords;
                updateCustomerPageUserDropdown();
                renderCustomerTable();
            } catch (err) {
                console.error('Error fetching customers:', err);
                if (modalTbody) modalTbody.innerHTML = '<tr><td colSpan="7" style="padding: 24px; text-align: center; color: #ff5252;">Failed to load customers.</td></tr>';
                if (pageTbody) pageTbody.innerHTML = '<tr><td colSpan="7" style="padding: 24px; text-align: center; color: #ff5252;">Failed to load customers.</td></tr>';
            }
        }

        function updateCustomerPageUserDropdown() {
            const select = document.getElementById('customerPageAssignedUserSelect');
            if (!select) return;
            const currentVal = select.value || 'all';
            const usersSet = new Set();
            (currentCustomerRecords || []).forEach(c => {
                const uStr = c.assigned_user_id ? String(c.assigned_user_id).trim() : '';
                if (uStr) {
                    usersSet.add(uStr);
                }
            });
            const sortedUsers = Array.from(usersSet).sort((a, b) => a.localeCompare(b));
            let html = `<option value="all" style="background: #0f172a; color: #fff;">All Tax Preps</option>`;
            html += `<option value="unassigned" style="background: #0f172a; color: #fff;">Unassigned</option>`;
            sortedUsers.forEach(u => {
                const escaped = u.replace(/"/g, '&quot;');
                html += `<option value="${escaped}" style="background: #0f172a; color: #fff;">${u}</option>`;
            });
            select.innerHTML = html;
            if (Array.from(select.options).some(o => o.value === currentVal)) {
                select.value = currentVal;
            } else {
                select.value = 'all';
            }
        }

        function onCustomerStatusFilterChange(sourceVal) {
            const pageSel = document.getElementById('customerPageStatusSelect');
            const modalSel = document.getElementById('customerModalStatusSelect');
            if (pageSel && pageSel.value !== sourceVal) pageSel.value = sourceVal;
            if (modalSel && modalSel.value !== sourceVal) modalSel.value = sourceVal;
            renderCustomerTable();
        }

        function renderCustomerTable() {
            const modalTbody = document.getElementById('customerTableBody');
            const pageTbody = document.getElementById('customerPageTableBody');
            const modalCount = document.getElementById('customerTotalCount');
            const pageCount = document.getElementById('customerPageTotalCount');

            let recordsToDisplay = currentCustomerRecords || [];

            // Filter by Status (Default: Active)
            const pageStatusSel = document.getElementById('customerPageStatusSelect');
            const modalStatusSel = document.getElementById('customerModalStatusSelect');
            const selectedStatus = (pageStatusSel ? pageStatusSel.value : null) || (modalStatusSel ? modalStatusSel.value : 'Active');

            if (selectedStatus === 'Active') {
                recordsToDisplay = recordsToDisplay.filter(c => String(c.status || 'Active').trim().toLowerCase() === 'active');
            } else if (selectedStatus === 'Inactive') {
                recordsToDisplay = recordsToDisplay.filter(c => String(c.status || '').trim().toLowerCase() !== 'active');
            }

            // Tax Prep Filter
            const userFilterSelect = document.getElementById('customerPageAssignedUserSelect');
            const selectedUserFilter = userFilterSelect ? userFilterSelect.value : 'all';

            if (selectedUserFilter === 'unassigned') {
                recordsToDisplay = recordsToDisplay.filter(c => !c.assigned_user_id || !String(c.assigned_user_id).trim());
            } else if (selectedUserFilter && selectedUserFilter !== 'all') {
                recordsToDisplay = recordsToDisplay.filter(c => String(c.assigned_user_id || '').trim().toLowerCase() === selectedUserFilter.trim().toLowerCase());
            }

            if (modalCount) modalCount.textContent = recordsToDisplay.length;
            if (pageCount) pageCount.textContent = recordsToDisplay.length;

            const emptyRows = '<tr><td colSpan="7" style="padding: 24px; text-align: center; color: #64748b;">No customer records found. Click ➕ Add New Customer.</td></tr>';

            if (recordsToDisplay.length === 0) {
                if (modalTbody) modalTbody.innerHTML = emptyRows;
                if (pageTbody) pageTbody.innerHTML = emptyRows;
                return;
            }

            const rowsHtml = recordsToDisplay.map(c => `
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); transition: background 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.03)'" onmouseout="this.style.background='transparent'">
                    <td style="padding: 12px 16px; font-family: monospace; font-weight: 700; color: #e100ff;">
                        ${c.custumer_number}
                        <br><span class="unread-reply-dot" id="unreadDot-${c.id}" data-cid="${c.id}" style="display: ${ (window.currentUnreadMap && window.currentUnreadMap[c.id] && window.currentUnreadMap[c.id].unread_count > 0) ? 'inline-block' : 'none'}; background: rgba(34, 197, 94, 0.18); border: 1px solid rgba(34, 197, 94, 0.5); color: #4ade80; font-size: 0.64rem; padding: 2px 8px; border-radius: 10px; margin-top: 4px; font-weight: 800; font-family: sans-serif; box-shadow: 0 0 10px rgba(34, 197, 94, 0.4);" title="New unread reply received!">🟢 ${window.currentUnreadMap && window.currentUnreadMap[c.id] ? window.currentUnreadMap[c.id].unread_count : 0} NEW</span>
                    </td>
                    <td style="padding: 12px 16px;">
                        <span style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; color: #cbd5e1;">${c.customer_type || 'Business'}</span>
                    </td>
                    <td style="padding: 12px 16px; font-weight: 700; color: #fff;">
                        ${c.legal_name}
                    </td>
                    <td style="padding: 12px 16px; font-family: monospace; color: #c084fc; font-weight: 700;">${c.assigned_user_id || '—'}</td>
                    <td style="padding: 12px 16px; color: #cbd5e1; font-size: 0.8rem;">
                        ${c.phone ? `<a href="tel:${c.phone.replace(/[^0-9+]/g, '')}" style="color: #38bdf8; text-decoration: underline; font-weight: 600;" title="Click to call ${c.phone}">📞 ${c.phone}</a><br>` : ''}
                        ${c.email ? `✉️ ${c.email}` : ''}
                        ${!c.phone && !c.email ? '—' : ''}
                    </td>
                    <td style="padding: 12px 16px;">
                        <span style="background: ${c.status === 'Active' ? 'rgba(0, 230, 118, 0.15)' : 'rgba(255, 179, 0, 0.15)'}; border: 1px solid ${c.status === 'Active' ? 'rgba(0, 230, 118, 0.35)' : 'rgba(255, 179, 0, 0.35)'}; color: ${c.status === 'Active' ? '#00e676' : '#ffb300'}; padding: 2px 10px; border-radius: 12px; font-size: 0.72rem; font-weight: 700;">${c.status}</span>
                    </td>
                    <td style="padding: 10px 12px; text-align: right; white-space: nowrap; position: relative;">
                        <button onclick="openCustomerStorageModal(event, ${c.id})" style="padding: 5px 10px; background: rgba(0, 230, 118, 0.15); border: 1px solid rgba(0, 230, 118, 0.35); color: #00e676; border-radius: 6px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; cursor: pointer; margin-right: 6px;" title="Open customer storage file manager">📂 FOLDER</button>
                        <div style="display: inline-block; position: relative;">
                            <button onclick="toggleCustomerActionMenu(event, ${c.id})" style="padding: 5px 10px; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.2); color: #e2e8f0; border-radius: 6px; font-size: 0.72rem; font-weight: 800; cursor: pointer;" title="More Actions">•••</button>
                            <div id="custActionMenu-${c.id}" class="cust-action-dropdown-menu" style="display: none; position: absolute; right: 0; top: 100%; margin-top: 6px; z-index: 1000; background: #0f172a; border: 1px solid rgba(255,255,255,0.15); border-radius: 10px; box-shadow: 0 10px 25px rgba(0,0,0,0.6); min-width: 195px; text-align: left; padding: 6px 0; backdrop-filter: blur(12px);">
                                <a href="#" onclick="handleVerifyIdentityAction(${c.id}); return false;" style="display: block; padding: 8px 14px; color: ${c.identity_verified ? '#34d399' : '#fbbf24'}; font-size: 0.78rem; font-weight: 600; text-decoration: none; border-bottom: 1px solid rgba(255,255,255,0.05);" onmouseover="this.style.background='rgba(255,255,255,0.06)'" onmouseout="this.style.background='transparent'">
                                    🛡️ ${c.identity_verified ? 'ID Verified' : 'Verify Photo ID'}
                                </a>
                                ${c.phone ? `<a href="tel:${c.phone.replace(/[^0-9+]/g, '')}" onclick="document.querySelectorAll('.cust-action-dropdown-menu').forEach(m => m.style.display = 'none');" style="display: block; padding: 8px 14px; color: #38bdf8; font-size: 0.78rem; font-weight: 600; text-decoration: none; border-bottom: 1px solid rgba(255,255,255,0.05);" onmouseover="this.style.background='rgba(255,255,255,0.06)'" onmouseout="this.style.background='transparent'">📞 Call Customer</a>` : ''}
                                <a href="#" onclick="handleCustomerChecklistAction(event, ${c.id}); return false;" style="display: block; padding: 8px 14px; color: #c084fc; font-size: 0.78rem; font-weight: 600; text-decoration: none; border-bottom: 1px solid rgba(255,255,255,0.05);" onmouseover="this.style.background='rgba(255,255,255,0.06)'" onmouseout="this.style.background='transparent'">
                                    📋 Workflow Checklist
                                </a>
                                <a href="#" onclick="handleSendEmailAction(event, ${c.id}); return false;" style="display: block; padding: 8px 14px; color: #38bdf8; font-size: 0.78rem; font-weight: 600; text-decoration: none; border-bottom: 1px solid rgba(255,255,255,0.05);" onmouseover="this.style.background='rgba(255,255,255,0.06)'" onmouseout="this.style.background='transparent'">
                                    ✉️ Send Email
                                </a>
                                <a href="#" onclick="handleCommsHistoryAction(${c.id}); return false;" style="display: block; padding: 8px 14px; color: #c084fc; font-size: 0.78rem; font-weight: 600; text-decoration: none; border-bottom: 1px solid rgba(255,255,255,0.05);" onmouseover="this.style.background='rgba(255,255,255,0.06)'" onmouseout="this.style.background='transparent'">
                                    💬 Comms History ${(window.currentUnreadMap && window.currentUnreadMap[c.id] && window.currentUnreadMap[c.id].unread_count > 0) ? `<span class="unread-history-badge" id="unreadHistoryDot-${c.id}" data-cid="${c.id}" style="background: #22c55e; color: #000; font-size: 0.62rem; padding: 1px 5px; border-radius: 8px; font-weight: 900; margin-left: 4px;">${window.currentUnreadMap[c.id].unread_count} NEW</span>` : ''}
                                </a>
                                <a href="#" onclick="handleInitStorageAction(event, ${c.id}); return false;" style="display: block; padding: 8px 14px; color: #38bdf8; font-size: 0.78rem; font-weight: 600; text-decoration: none; border-bottom: 1px solid rgba(255,255,255,0.05);" onmouseover="this.style.background='rgba(255,255,255,0.06)'" onmouseout="this.style.background='transparent'">
                                    ${c.do_storage_status === 'Initialized' ? '⚡ Re-Init Storage' : '☁️ Init Storage'}
                                </a>
                                <a href="#" onclick="handleEditCustomerAction(${c.id}); return false;" style="display: block; padding: 8px 14px; color: #e100ff; font-size: 0.78rem; font-weight: 600; text-decoration: none; border-bottom: 1px solid rgba(255,255,255,0.05);" onmouseover="this.style.background='rgba(255,255,255,0.06)'" onmouseout="this.style.background='transparent'">
                                    ✏️ Edit Account
                                </a>
                                <a href="#" onclick="handleDeleteCustomerAction(event, ${c.id}); return false;" style="display: block; padding: 8px 14px; color: #f87171; font-size: 0.78rem; font-weight: 600; text-decoration: none;" onmouseover="this.style.background='rgba(239,68,68,0.15)'" onmouseout="this.style.background='transparent'">
                                    🗑️ Delete Customer
                                </a>
                            </div>
                        </div>
                    </td>
                </tr>
            `).join('');

            if (modalTbody) modalTbody.innerHTML = rowsHtml;
            if (pageTbody) pageTbody.innerHTML = rowsHtml;
            if (typeof checkUnreadCommunicationsAlerts === 'function') {
                checkUnreadCommunicationsAlerts();
            }
        }

        function handleVerifyIdentityAction(customerId) {
            document.querySelectorAll('.cust-action-dropdown-menu').forEach(m => m.style.display = 'none');
            const c = (currentCustomerRecords || []).find(x => Number(x.id) === Number(customerId));
            openVerifyIdentityModal(customerId, c ? c.legal_name : '');
        }

        function handleCustomerChecklistAction(event, customerId) {
            document.querySelectorAll('.cust-action-dropdown-menu').forEach(m => m.style.display = 'none');
            const c = (currentCustomerRecords || []).find(x => Number(x.id) === Number(customerId));
            const cType = c ? (c.customer_type || c.type || 'Business') : 'Business';
            openCustomerChecklistModal(event, customerId, null, cType);
        }

        function handleSendEmailAction(event, customerId) {
            document.querySelectorAll('.cust-action-dropdown-menu').forEach(m => m.style.display = 'none');
            openSendCustomerEmailModal(event, customerId);
        }

        function handleCommsHistoryAction(customerId) {
            document.querySelectorAll('.cust-action-dropdown-menu').forEach(m => m.style.display = 'none');
            openCustomerCommsHistoryModal(customerId);
        }

        function handleInitStorageAction(event, customerId) {
            document.querySelectorAll('.cust-action-dropdown-menu').forEach(m => m.style.display = 'none');
            initCustomerStorage(event, customerId);
        }

        function handleEditCustomerAction(customerId) {
            document.querySelectorAll('.cust-action-dropdown-menu').forEach(m => m.style.display = 'none');
            editCustomerRecord(customerId);
        }

        function handleDeleteCustomerAction(event, customerId) {
            document.querySelectorAll('.cust-action-dropdown-menu').forEach(m => m.style.display = 'none');
            const c = (currentCustomerRecords || []).find(x => Number(x.id) === Number(customerId));
            deleteCustomerRecord(event, customerId, c ? (c.custumer_number || '') : '', c ? (c.legal_name || '') : '');
        }

        function toggleCustomerActionMenu(event, customerId) {
            if (event) event.stopPropagation();
            const btn = event ? event.currentTarget : null;
            const targetMenu = document.getElementById(`custActionMenu-${customerId}`);
            const isVisible = targetMenu && targetMenu.style.display !== 'none';
            document.querySelectorAll('.cust-action-dropdown-menu').forEach(m => m.style.display = 'none');
            if (targetMenu && !isVisible) {
                targetMenu.style.display = 'block';
                targetMenu.style.position = 'fixed';
                targetMenu.style.zIndex = '99999';
                if (btn) {
                    const rect = btn.getBoundingClientRect();
                    targetMenu.style.top = (rect.bottom + 4) + 'px';
                    targetMenu.style.left = 'auto';
                    targetMenu.style.right = (window.innerWidth - rect.right) + 'px';
                    
                    const menuHeight = targetMenu.offsetHeight || 280;
                    if (rect.bottom + 4 + menuHeight > window.innerHeight) {
                        targetMenu.style.top = Math.max(10, rect.top - menuHeight - 4) + 'px';
                    }
                }
            }
        }

        document.addEventListener('click', function(e) {
            if (!e.target.closest('.cust-action-dropdown-menu') && !e.target.closest('button[title="More Actions"]')) {
                document.querySelectorAll('.cust-action-dropdown-menu').forEach(m => m.style.display = 'none');
            }
        });
        window.addEventListener('scroll', function() {
            document.querySelectorAll('.cust-action-dropdown-menu').forEach(m => m.style.display = 'none');
        }, true);

        async function initCustomerStorage(event, customerId) {
            if (event) event.stopPropagation();
            const btn = event ? event.currentTarget : null;
            const originalText = btn ? btn.textContent : '';
            if (btn) {
                btn.disabled = true;
                btn.textContent = '⏳ Initializing...';
            }

            try {
                const res = await fetch(`/api/customers/${customerId}/init-storage`, { method: 'POST' });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || data.message || 'Failed to initialize storage');
                
                if (data.success) {
                    const openNow = await showCustomConfirm(`✅ Customer Storage initialized successfully!\n\nFolder Path:\n${data.path}\n\nFolders Created:\n` + (data.folders || []).join('\n') + `\n\nWould you like to open this customer's folder now?`, 'Storage Initialized', 'Open Folder Now', 'Dismiss');
                    if (openNow) {
                        openCustomerStorageModal(null, customerId);
                    }
                } else {
                    alert(`⚠️ Storage Initialization Notice:\n${data.message}`);
                }
                await fetchCustomerRecords();
            } catch (err) {
                alert(`❌ Storage Error: ${err.message}`);
                if (btn) {
                    btn.disabled = false;
                    btn.textContent = originalText;
                }
            }
        }

        // --- Customer Storage File Explorer Modal Logic ---
        let currentStorageCustomerId = null;
        let currentStorageCustomerName = '';
        let currentStorageRootFolder = '';
        let currentStoragePrefix = '';
        let currentStorageData = null;

        async function openCustomerStorageModal(event, customerId) {
            if (event) {
                event.stopPropagation();
                if (event.preventDefault) event.preventDefault();
            }
            currentStorageCustomerId = customerId;
            currentStoragePrefix = '';

            // Get or find the modal — it is appended to body at page load
            let modal = document.getElementById('customerStorageModal');
            if (!modal) {
                console.error('customerStorageModal not found in DOM');
                alert('Storage modal not found. Please refresh the page (Ctrl+F5).');
                return;
            }

            // Ensure it is a direct child of body for correct stacking
            if (modal.parentElement !== document.body) {
                document.body.appendChild(modal);
            }

            modal.style.display = 'flex';
            modal.style.opacity = '1';

            await loadStorageFolder(customerId, '');
        }

        function closeCustomerStorageModal() {
            const modal = document.getElementById('customerStorageModal');
            if (!modal) return;
            modal.style.opacity = '0';
            setTimeout(() => { modal.style.display = 'none'; }, 150);
            currentStorageCustomerId = null;
            currentStorageData = null;
            const spinner = document.getElementById('storageLoadingSpinner');
            if (spinner) spinner.style.display = 'none';
        }

        async function loadStorageFolder(customerId, prefix) {
            if (prefix && typeof prefix === 'string' && prefix.includes('%')) {
                try { prefix = decodeURIComponent(prefix); } catch (e) {}
            }
            const spinner = document.getElementById('storageLoadingSpinner');
            const tbody = document.getElementById('storageFilesTbody');
            if (spinner) spinner.style.display = 'block';
            if (tbody) tbody.innerHTML = '';

            try {
                const url = `/api/customers/${customerId}/storage/files` + (prefix ? `?prefix=${encodeURIComponent(prefix)}` : '');
                const res = await fetch(url);
                const data = await res.json();

                if (!res.ok) throw new Error(data.detail || 'Failed to fetch storage files');

                currentStorageCustomerName = data.customer_name;
                currentStorageRootFolder = data.root_folder;
                currentStoragePrefix = data.current_prefix;
                currentStorageData = data;

                const titleEl = document.getElementById('storageModalTitle');
                const subtitleEl = document.getElementById('storageModalSubtitle');
                const parentBadge = data.parent_name ? `<span style="font-size:0.75rem; background:rgba(168,85,247,0.2); border:1px solid rgba(168,85,247,0.4); color:#c084fc; padding:2px 8px; border-radius:4px; font-weight:700; margin-right:8px;">🏢 ${data.parent_name}</span>` : '';
                if (titleEl) titleEl.innerHTML = `${parentBadge}📂 ${data.customer_name} — Storage`;
                if (subtitleEl) subtitleEl.textContent = `Parent: ${data.parent_name || 'VRT Services'} | Bucket: ${data.bucket} | Path: ${data.current_prefix}`;

                renderStorageBreadcrumbs();
                renderStorageItems(data.subfolders, data.files);

            } catch (err) {
                if (tbody) {
                    tbody.innerHTML = `<tr><td colspan="4" style="padding: 24px; text-align: center; color: #f87171;">⚠️ ${err.message}<br><button onclick="reinitStorageFromModal()" style="margin-top: 12px; padding: 6px 14px; background: #38bdf8; border: none; color: #000; font-weight: 700; border-radius: 6px; cursor: pointer;">⚡ Initialize Storage Folders</button></td></tr>`;
                }
            } finally {
                if (spinner) spinner.style.display = 'none';
            }
        }

        function renderStorageBreadcrumbs() {
            const container = document.getElementById('storageBreadcrumbs');
            if (!container || !currentStorageData) return;

            const root = currentStorageRootFolder;
            const current = currentStoragePrefix;
            const cid = currentStorageCustomerId;

            let relativePath = current.startsWith(root) ? current.substring(root.length) : '';
            const parts = relativePath.split('/').filter(Boolean);

            const pLabel = currentStorageData.parent_name ? `${currentStorageData.parent_name} / ` : '';
            // Use data-prefix attributes — no inline onclick string injection
            let html = `<span class="breadcrumb-nav" data-prefix="${root.replace(/"/g, '&quot;')}" data-cid="${cid}" style="cursor: pointer; color: #38bdf8; text-decoration: underline; font-weight: 700;">🏠 ${pLabel}${currentStorageCustomerName}</span>`;

            let accumulated = root;
            parts.forEach((part, idx) => {
                accumulated += part + '/';
                const isLast = idx === parts.length - 1;
                html += ` <span style="color: #64748b;">/</span> `;
                if (isLast) {
                    html += `<span style="color: #fff; font-weight: 700;">${part}</span>`;
                } else {
                    html += `<span class="breadcrumb-nav" data-prefix="${accumulated.replace(/"/g, '&quot;')}" data-cid="${cid}" style="cursor: pointer; color: #38bdf8; text-decoration: underline;">${part}</span>`;
                }
            });

            container.innerHTML = html;

            // Attach click events to breadcrumb spans
            container.querySelectorAll('.breadcrumb-nav').forEach(el => {
                el.addEventListener('click', () => {
                    const p = el.getAttribute('data-prefix');
                    const c = parseInt(el.getAttribute('data-cid'), 10);
                    if (p && c) loadStorageFolder(c, p);
                });
            });
        }

        function formatBytes(bytes, decimals = 1) {
            if (!bytes || bytes === 0) return '0 B';
            const k = 1024;
            const dm = decimals < 0 ? 0 : decimals;
            const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
        }

        function getFileIcon(filename) {
            const ext = filename.split('.').pop().toLowerCase();
            if (['pdf'].includes(ext)) return '📄';
            if (['csv', 'xlsx', 'xls'].includes(ext)) return '📊';
            if (['png', 'jpg', 'jpeg', 'webp', 'gif'].includes(ext)) return '🖼️';
            if (['json', 'txt', 'log'].includes(ext)) return '📝';
            return '📎';
        }

        function renderStorageItems(subfolders = [], files = []) {
            const tbody = document.getElementById('storageFilesTbody');
            const stats = document.getElementById('storageFileStats');
            if (!tbody) return;

            let rowsHtml = '';
            const cid = currentStorageCustomerId;

            // If not at root, show '..' go up folder row
            if (currentStoragePrefix !== currentStorageRootFolder) {
                const cleanPrefix = currentStoragePrefix.endsWith('/') ? currentStoragePrefix.slice(0, -1) : currentStoragePrefix;
                const parts = cleanPrefix.split('/');
                parts.pop();
                let upPrefix = parts.join('/') + '/';
                if (!upPrefix.startsWith(currentStorageRootFolder)) upPrefix = currentStorageRootFolder;

                rowsHtml += `<tr class="storage-nav-row" data-prefix="${upPrefix.replace(/"/g, '&quot;')}" data-cid="${cid}" style="border-bottom: 1px solid rgba(255,255,255,0.05); cursor: pointer;" onmouseover="this.style.background='rgba(255,255,255,0.04)'" onmouseout="this.style.background='transparent'">
                    <td style="padding: 10px 12px; font-weight: 700; color: #38bdf8;" colspan="4">
                        📁 .. <span style="font-weight: 400; color: #94a3b8; font-size: 0.75rem;">(Go up to parent folder)</span>
                    </td>
                </tr>`;
            }

            if (subfolders.length === 0 && files.length === 0) {
                rowsHtml += `<tr><td colspan="4" style="padding: 30px; text-align: center; color: #64748b;">No files or subfolders found in this directory. Click <strong>Upload File</strong> above to add files.</td></tr>`;
            } else {
                // Render Subfolders — use data-prefix to avoid inline escaping issues
                subfolders.forEach(sf => {
                    const deleteBtnHtml = `<button class="storage-delete-folder-btn" data-prefix="${sf.prefix.replace(/"/g, '&quot;')}" data-name="${sf.name.replace(/"/g, '&quot;')}" data-cid="${cid}" style="padding: 4px 8px; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); color: #f87171; border-radius: 6px; font-size: 0.7rem; font-weight: 700; cursor: pointer;" title="Delete folder and all its contents">🗑️</button>`;

                    rowsHtml += `<tr class="storage-item-row storage-nav-row" data-prefix="${sf.prefix.replace(/"/g, '&quot;')}" data-cid="${cid}" data-name="${sf.name.toLowerCase().replace(/"/g, '&quot;')}" style="border-bottom: 1px solid rgba(255,255,255,0.05); transition: background 0.15s; cursor: pointer;" onmouseover="this.style.background='rgba(255,255,255,0.04)'" onmouseout="this.style.background='transparent'">
                        <td style="padding: 10px 12px; font-weight: 700; color: #38bdf8; display: flex; align-items: center; gap: 8px;">
                            <span style="font-size: 1.1rem;">📁</span> ${sf.name}/
                        </td>
                        <td style="padding: 10px 12px; color: #64748b; font-family: monospace;">—</td>
                        <td style="padding: 10px 12px; color: #64748b;">Folder</td>
                        <td style="padding: 10px 12px; text-align: right; white-space: nowrap;">
                            <button class="storage-open-btn" data-prefix="${sf.prefix.replace(/"/g, '&quot;')}" data-cid="${cid}" style="padding: 4px 10px; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.35); color: #38bdf8; border-radius: 6px; font-size: 0.7rem; font-weight: 700; cursor: pointer; margin-right: 6px;">Open ↗</button>
                            ${deleteBtnHtml}
                        </td>
                    </tr>`;
                });

                // Render Files
                files.forEach(f => {
                    const icon = getFileIcon(f.name);
                    const dateStr = f.last_modified ? new Date(f.last_modified).toLocaleString() : '—';
                    const isPdf = f.name.toLowerCase().endsWith('.pdf');
                    const attrKey = (f.key || '').replace(/"/g, '&quot;');
                    const attrName = (f.name || '').replace(/"/g, '&quot;');
                    const attrUrl = (f.url || '').replace(/"/g, '&quot;');

                    rowsHtml += `
                        <tr class="storage-item-row ${isPdf ? 'storage-pdf-row' : ''}" data-key="${attrKey}" data-name="${attrName}" data-url="${attrUrl}" data-name-search="${f.name.toLowerCase().replace(/"/g, '&quot;')}" style="border-bottom: 1px solid rgba(255,255,255,0.05); transition: background 0.15s;" onmouseover="this.style.background='rgba(255,255,255,0.03)'" onmouseout="this.style.background='transparent'">
                            <td style="padding: 10px 12px; font-weight: 600; color: #f1f5f9; display: flex; align-items: center; gap: 8px; word-break: break-all; ${isPdf ? 'cursor: pointer;' : ''}">
                                <input type="checkbox" class="storage-item-select-chk" data-key="${attrKey}" data-name="${attrName}" onchange="updateStorageBatchSelectionState()" onclick="event.stopPropagation()" style="cursor: pointer; accent-color: #38bdf8; width: 15px; height: 15px; margin-right: 4px;">
                                <span style="font-size: 1.1rem;">${icon}</span> ${f.name}
                            </td>
                            <td style="padding: 10px 12px; color: #94a3b8; font-family: monospace; white-space: nowrap;">${formatBytes(f.size)}</td>
                            <td style="padding: 10px 12px; color: #94a3b8; font-size: 0.75rem; white-space: nowrap;">${dateStr}</td>
                            <td style="padding: 10px 12px; text-align: right; white-space: nowrap;">
                                ${isPdf ? `<button class="storage-preview-pdf-btn" data-key="${attrKey}" data-name="${attrName}" data-url="${attrUrl}" style="padding: 4px 10px; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.35); color: #38bdf8; border-radius: 6px; font-size: 0.7rem; font-weight: 700; cursor: pointer; margin-right: 6px;" title="Preview PDF inside modal window">👁️ Preview</button>` : `<button class="storage-convert-file-pdf-btn" data-key="${attrKey}" data-name="${attrName}" style="padding: 4px 8px; background: rgba(168, 85, 247, 0.2); border: 1px solid rgba(168, 85, 247, 0.45); color: #c084fc; border-radius: 6px; font-size: 0.7rem; font-weight: 700; cursor: pointer; margin-right: 6px;" title="Convert file to PDF (Moves original to Raw_Originals/)">📄 -> PDF</button>`}
                                <button class="storage-rename-file-btn" data-key="${attrKey}" data-name="${attrName}" style="padding: 4px 8px; background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.35); color: #c084fc; border-radius: 6px; font-size: 0.7rem; font-weight: 700; cursor: pointer; margin-right: 6px;" title="Rename file">✏️ Rename</button>
                                <button class="storage-move-file-btn" data-key="${attrKey}" data-name="${attrName}" style="padding: 4px 8px; background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.35); color: #fbbf24; border-radius: 6px; font-size: 0.7rem; font-weight: 700; cursor: pointer; margin-right: 6px;" title="Move file to another folder">🚚 Move</button>
                                <a href="/api/storage/download?key=${encodeURIComponent(attrKey)}" target="_blank" download style="padding: 4px 10px; background: rgba(0, 230, 118, 0.15); border: 1px solid rgba(0, 230, 118, 0.35); color: #00e676; border-radius: 6px; font-size: 0.7rem; font-weight: 700; text-decoration: none; margin-right: 6px; display: inline-block;">📥 Download</a>
                                <button class="storage-delete-file-btn" data-key="${attrKey}" data-name="${attrName}" style="padding: 4px 8px; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); color: #f87171; border-radius: 6px; font-size: 0.7rem; font-weight: 700; cursor: pointer;" title="Delete file">🗑️</button>
                            </td>
                        </tr>
                    `;
                });
            }

            tbody.innerHTML = rowsHtml;

            // Delegated event handler: navigate on row/button click using data-prefix
            tbody.querySelectorAll('.storage-nav-row').forEach(row => {
                row.addEventListener('click', (e) => {
                    if (e.target.closest('.storage-open-btn') || e.target.closest('.storage-delete-folder-btn')) return;
                    const p = row.getAttribute('data-prefix');
                    const c = parseInt(row.getAttribute('data-cid'), 10);
                    if (p && c) loadStorageFolder(c, p);
                });
            });
            tbody.querySelectorAll('.storage-open-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const p = btn.getAttribute('data-prefix');
                    const c = parseInt(btn.getAttribute('data-cid'), 10);
                    if (p && c) loadStorageFolder(c, p);
                });
            });
            tbody.querySelectorAll('.storage-delete-folder-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const p = btn.getAttribute('data-prefix');
                    const n = btn.getAttribute('data-name');
                    const c = parseInt(btn.getAttribute('data-cid'), 10);
                    deleteStorageFolder(p, n, c);
                });
            });
            tbody.querySelectorAll('.storage-pdf-row').forEach(row => {
                row.querySelector('td')?.addEventListener('click', (e) => {
                    if (e.target.closest('.storage-item-select-chk')) return;
                    const key = row.getAttribute('data-key');
                    const name = row.getAttribute('data-name');
                    const url = row.getAttribute('data-url');
                    openPdfViewerModal(e, key, name, url);
                });
            });
            tbody.querySelectorAll('.storage-preview-pdf-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const key = btn.getAttribute('data-key');
                    const name = btn.getAttribute('data-name');
                    const url = btn.getAttribute('data-url');
                    openPdfViewerModal(e, key, name, url);
                });
            });
            tbody.querySelectorAll('.storage-convert-file-pdf-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const key = btn.getAttribute('data-key');
                    convertSingleStorageFileToPdf(key);
                });
            });
            tbody.querySelectorAll('.storage-rename-file-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const key = btn.getAttribute('data-key');
                    const name = btn.getAttribute('data-name');
                    renameStorageFile(e, key, name);
                });
            });
            tbody.querySelectorAll('.storage-move-file-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const key = btn.getAttribute('data-key');
                    const name = btn.getAttribute('data-name');
                    openMoveFileModal(e, key, name);
                });
            });
            tbody.querySelectorAll('.storage-delete-file-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const key = btn.getAttribute('data-key');
                    const name = btn.getAttribute('data-name');
                    deleteStorageFile(e, key, name);
                });
            });

            if (stats) stats.textContent = `${subfolders.length} folder(s), ${files.length} file(s)`;
            updateStorageBatchSelectionState();
        }

        function updateStorageBatchSelectionState() {
            const chks = document.querySelectorAll('.storage-item-select-chk:checked');
            const mergeBtn = document.getElementById('storageMergePdfBtn');
            const moveBtn = document.getElementById('storageBatchMoveBtn');
            const selectAllChk = document.getElementById('storageSelectAllChk');
            const allChks = document.querySelectorAll('.storage-item-select-chk');

            if (mergeBtn) {
                if (chks.length > 0) {
                    mergeBtn.style.display = 'inline-block';
                    mergeBtn.innerHTML = `📑 Merge Selected (${chks.length}) -> PDF`;
                } else {
                    mergeBtn.style.display = 'none';
                }
            }
            if (moveBtn) {
                if (chks.length > 0) {
                    moveBtn.style.display = 'inline-block';
                    moveBtn.innerHTML = `🚚 Move Selected (${chks.length})`;
                } else {
                    moveBtn.style.display = 'none';
                }
            }
            if (selectAllChk && allChks.length > 0) {
                selectAllChk.checked = (chks.length === allChks.length);
            }
        }

        async function moveSelectedStorageFiles() {
            const chks = Array.from(document.querySelectorAll('.storage-item-select-chk:checked'));
            if (!chks.length) {
                alert('Please select at least one file to move.');
                return;
            }
            const keys = chks.map(c => c.getAttribute('data-key')).filter(Boolean);
            if (!keys.length) return;

            openMoveFileModal(null, null, null, keys);
        }

        async function convertSingleStorageFileToPdf(key) {
            if (!key) return;
            const filename = key.split('/').pop();
            try {
                if (typeof showToast === 'function') showToast(`Converting '${filename}' to PDF...`, 'info');
                const res = await fetch('/api/storage/convert-to-pdf', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ key: key })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Conversion failed');
                if (typeof showToast === 'function') showToast(data.message || 'File converted to PDF successfully!', 'success');
                if (currentStorageCustomerId && currentStoragePrefix) {
                    refreshCurrentStorageFolder();
                }
            } catch (err) {
                alert('PDF Conversion Error: ' + err.message);
            }
        }

        async function batchConvertInboxToPdf() {
            if (!currentStoragePrefix) return;
            const folderName = currentStoragePrefix.split('/').filter(Boolean).pop() || 'folder';
            if (!confirm(`Convert all non-PDF files in '${folderName}' to PDF?\n\nRaw original files will be moved into a 'Raw_Originals' subfolder.`)) return;

            try {
                if (typeof showToast === 'function') showToast(`Converting files in '${folderName}' to PDF...`, 'info');
                const res = await fetch('/api/storage/batch-convert-inbox', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prefix: currentStoragePrefix })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Batch conversion failed');
                if (typeof showToast === 'function') showToast(data.message || 'Batch PDF conversion complete!', 'success');
                refreshCurrentStorageFolder();
            } catch (err) {
                alert('Batch PDF Conversion Error: ' + err.message);
            }
        }

        async function mergeSelectedStorageImagesToPdf() {
            const checkedBoxes = Array.from(document.querySelectorAll('.storage-item-select-chk:checked'));
            if (checkedBoxes.length < 1) {
                alert('Please select at least 1 image file to merge into PDF.');
                return;
            }

            const keys = checkedBoxes.map(cb => cb.getAttribute('data-key'));
            const defaultName = `Merged_Document_${new Date().toISOString().slice(0,10)}.pdf`;
            const outName = prompt(`Enter a name for the merged PDF document:`, defaultName);
            if (!outName) return;

            try {
                if (typeof showToast === 'function') showToast(`Merging ${keys.length} file(s) into '${outName}'...`, 'info');
                const res = await fetch('/api/storage/merge-to-pdf', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ keys: keys, output_filename: outName })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Merge failed');
                if (typeof showToast === 'function') showToast(data.message || 'Merged PDF created successfully!', 'success');
                refreshCurrentStorageFolder();
            } catch (err) {
                alert('PDF Merge Error: ' + err.message);
            }
        }

        function filterStorageItems() {
            const q = (document.getElementById('storageFileSearchInput')?.value || '').toLowerCase().trim();
            const rows = document.querySelectorAll('.storage-item-row');
            rows.forEach(r => {
                const name = r.getAttribute('data-name-search') || r.getAttribute('data-name') || '';
                r.style.display = name.includes(q) ? '' : 'none';
            });
        }

        async function handleStorageFileUpload(event) {
            const files = event.target.files;
            if (!files || files.length === 0) return;

            const targetPrefix = currentStoragePrefix || currentStorageRootFolder;
            const fileList = Array.from(files);
            let successCount = 0;
            let errors = [];

            if (typeof showToast === 'function') {
                showToast(`Uploading ${fileList.length} file(s)...`, 'info');
            }

            const spinner = document.getElementById('storageLoadingSpinner');
            if (spinner) {
                spinner.style.display = 'block';
                spinner.innerHTML = `<div style="font-size: 1.8rem; margin-bottom: 10px;">⏳</div>Uploading 1 of ${fileList.length} file(s)...<br><span style="font-size:0.9rem;opacity:0.8;">Processing OCR, please wait...</span>`;
            }

            for (let i = 0; i < fileList.length; i++) {
                const file = fileList[i];
                if (spinner) {
                    spinner.innerHTML = `<div style="font-size: 1.8rem; margin-bottom: 10px;">⏳</div>Uploading ${i + 1} of ${fileList.length} file(s)...<br><span style="font-size:0.9rem;opacity:0.8;">Processing OCR for ${file.name}, please wait...</span>`;
                }
                
                // Force browser to repaint the DOM so it doesn't look frozen
                await new Promise(resolve => setTimeout(resolve, 50));

                const formData = new FormData();
                formData.append('file', file);
                formData.append('target_prefix', targetPrefix);

                try {
                    const res = await fetch(`/api/customers/${currentStorageCustomerId}/storage/upload`, {
                        method: 'POST',
                        body: formData
                    });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || data.message || `Failed to upload ${file.name}`);
                    successCount++;
                } catch (err) {
                    errors.push(`${file.name}: ${err.message}`);
                }
            }

            event.target.value = '';
            await refreshCurrentStorageFolder();
            const taxCid1 = currentStorageCustomerId || currentChecklistCustomerId;
            if (typeof loadTaxDocTracking === 'function' && taxCid1) {
                loadTaxDocTracking(taxCid1);
            }

            if (errors.length === 0) {
                if (typeof showToast === 'function') {
                    showToast(`✅ ${fileList.length === 1 ? `File "${fileList[0].name}"` : `All ${successCount} files`} uploaded successfully!`, 'success');
                } else {
                    alert(`✅ Uploaded ${successCount} file(s) successfully!`);
                }
            } else {
                alert(`⚠️ Uploaded ${successCount} of ${fileList.length} files.\n\nErrors:\n` + errors.join('\n'));
            }
        }

        async function deleteStorageFile(event, key, name) {
            if (event) {
                event.stopPropagation();
                if (event.preventDefault) event.preventDefault();
            }
            if (!key || !name) return;

            if (!await showCustomConfirm(`Are you sure you want to delete file "${name}"?`)) return;

            try {
                const res = await fetch(`/api/customers/${currentStorageCustomerId}/storage/file?key=${encodeURIComponent(key)}`, {
                    method: 'DELETE'
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Delete failed');
                await refreshCurrentStorageFolder();
            } catch (err) {
                alert(`❌ Delete Error: ${err.message}`);
            }
        }

        async function renameStorageFile(event, oldKey, oldName) {
            if (event) {
                event.stopPropagation();
                if (event.preventDefault) event.preventDefault();
            }
            if (!oldKey || !oldName) return;

            const newName = prompt(`Rename file '${oldName}' to:`, oldName);
            if (newName === null) return; // user cancelled
            const trimmed = newName.trim();
            if (!trimmed || trimmed === oldName) return;

            const spinner = document.getElementById('storageLoadingSpinner');
            if (spinner) {
                spinner.style.display = 'block';
                spinner.innerHTML = `<div style="font-size: 1.8rem; margin-bottom: 10px;">⏳</div>Renaming file to '${trimmed}'...<br><span style="font-size:0.9rem;opacity:0.8;">Processing OCR, please wait...</span>`;
            }
            
            // Force browser to repaint the DOM
            await new Promise(resolve => setTimeout(resolve, 50));

            try {
                const res = await fetch(`/api/customers/${currentStorageCustomerId}/storage/rename-file`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ old_key: oldKey, new_name: trimmed })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || data.message || 'Rename failed');

                await refreshCurrentStorageFolder();
                const taxCid2 = currentStorageCustomerId || currentChecklistCustomerId;
                if (typeof loadTaxDocTracking === 'function' && taxCid2) {
                    loadTaxDocTracking(taxCid2);
                }
            } catch (err) {
                alert(`❌ Rename Error: ${err.message}`);
            } finally {
                const spinner = document.getElementById('storageLoadingSpinner');
                if (spinner) spinner.style.display = 'none';
            }
        }

        let pendingMoveSourceKey = null;
        let pendingMoveFileName = null;
        let pendingBatchMoveKeys = null;

        async function openMoveFileModal(event, sourceKey, fileName, batchKeys = null) {
            if (event) {
                event.stopPropagation();
                if (event.preventDefault) event.preventDefault();
            }
            if (!currentStorageCustomerId) return;

            const titleEl = document.getElementById('moveFileModalTitle');
            const labelEl = document.getElementById('moveFileTargetLabel');
            const nameEl = document.getElementById('moveFileTargetName');
            const submitBtn = document.getElementById('submitMoveFileBtn');

            if (batchKeys && batchKeys.length) {
                pendingMoveSourceKey = null;
                pendingMoveFileName = null;
                pendingBatchMoveKeys = batchKeys;

                if (titleEl) titleEl.textContent = `Move ${batchKeys.length} Selected File(s)`;
                if (labelEl) labelEl.textContent = `FILES TO MOVE (${batchKeys.length}):`;
                
                const fileNamesStr = batchKeys.map(k => k.split('/').pop()).filter(Boolean).join(', ');
                if (nameEl) nameEl.textContent = fileNamesStr || `${batchKeys.length} files selected`;
                if (submitBtn) submitBtn.textContent = `🚚 Move ${batchKeys.length} File(s) Now`;
            } else if (sourceKey && fileName) {
                pendingMoveSourceKey = sourceKey;
                pendingMoveFileName = fileName;
                pendingBatchMoveKeys = null;

                if (titleEl) titleEl.textContent = 'Move File to Folder';
                if (labelEl) labelEl.textContent = 'FILE TO MOVE:';
                if (nameEl) nameEl.textContent = fileName;
                if (submitBtn) submitBtn.textContent = '🚚 Move File Now';
            } else {
                return;
            }

            const selectEl = document.getElementById('moveFileFolderSelect');
            if (selectEl) {
                selectEl.innerHTML = `<option value="">⌛ Loading available folders...</option>`;
            }

            const customGroup = document.getElementById('moveFileCustomGroup');
            if (customGroup) customGroup.style.display = 'none';

            let modal = document.getElementById('moveFileModal');
            if (modal) {
                document.body.appendChild(modal);
                modal.style.zIndex = '2147483649';
                modal.style.display = 'flex';
            }

            try {
                const res = await fetch(`/api/customers/${currentStorageCustomerId}/storage/folders`);
                const data = await res.json();
                if (res.ok && selectEl) {
                    let optionsHtml = `<option value="">🏠 Customer Root (${data.parent_name ? data.parent_name + ' / ' : ''}${data.customer_name || ''})</option>`;
                    
                    const taxYearFolder = `Tax Documents/Tax Year ${_taxDocCurrentYear || 2025}/`;
                    const suggestedFolders = ['Inbox/', 'Tax Documents/', taxYearFolder, 'Bank Statements/', 'Check Images/', 'Raw_Originals/'];
                    const existingFolders = data.folders || [];

                    const folderList = [];
                    existingFolders.forEach(f => { if (!folderList.includes(f)) folderList.push(f); });
                    suggestedFolders.forEach(f => { if (!folderList.includes(f)) folderList.push(f); });

                    folderList.forEach(fPath => {
                        let icon = '📁';
                        const lower = fPath.toLowerCase();
                        if (lower.startsWith('inbox')) icon = '📥';
                        else if (lower.startsWith('tax')) icon = '📂';
                        else if (lower.startsWith('bank')) icon = '📊';
                        else if (lower.startsWith('check')) icon = '🧾';
                        else if (lower.startsWith('raw')) icon = '📦';

                        optionsHtml += `<option value="${fPath}">${icon} ${fPath}</option>`;
                    });
                    optionsHtml += `<option value="custom">✏️ Enter Custom Folder Path...</option>`;
                    selectEl.innerHTML = optionsHtml;

                    if (folderList.includes(taxYearFolder)) {
                        selectEl.value = taxYearFolder;
                    } else if (folderList.includes('Inbox/')) {
                        selectEl.value = 'Inbox/';
                    } else if (folderList.length > 0) {
                        selectEl.value = folderList[0];
                    }
                }
            } catch (err) {
                console.error("Error fetching folders for move modal:", err);
            }
        }

        function closeMoveFileModal() {
            let modal = document.getElementById('moveFileModal');
            if (modal) modal.style.display = 'none';
            pendingMoveSourceKey = null;
            pendingMoveFileName = null;
            pendingBatchMoveKeys = null;
        }

        function handleMoveFolderSelectChange(val) {
            const customGroup = document.getElementById('moveFileCustomGroup');
            if (customGroup) {
                customGroup.style.display = (val === 'custom') ? 'block' : 'none';
            }
        }

        async function confirmSubmitMoveFile() {
            if ((!pendingMoveSourceKey && (!pendingBatchMoveKeys || !pendingBatchMoveKeys.length)) || !currentStorageCustomerId) return;

            const selectEl = document.getElementById('moveFileFolderSelect');
            const customInputEl = document.getElementById('moveFileCustomInput');
            let chosenFolder = selectEl ? selectEl.value : '';

            if (chosenFolder === 'custom') {
                chosenFolder = customInputEl ? customInputEl.value.trim() : '';
                if (!chosenFolder) {
                    alert('Please enter a custom folder path');
                    return;
                }
            }

            if (!chosenFolder) {
                alert('Please select a destination folder');
                return;
            }
            if (!chosenFolder.endsWith('/')) chosenFolder += '/';

            const rootPath = (currentStorageRootFolder || '').replace(/\/$/, '') + '/';
            let targetFolderKey = chosenFolder;
            if (!chosenFolder.startsWith(rootPath) && rootPath) {
                targetFolderKey = rootPath + chosenFolder.replace(/^\//, '');
            }

            const submitBtn = document.getElementById('submitMoveFileBtn');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = '🚚 Moving...';
            }

            try {
                if (pendingMoveSourceKey) {
                    const res = await fetch(`/api/customers/${currentStorageCustomerId}/storage/move-file`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ source_key: pendingMoveSourceKey, target_folder_key: targetFolderKey })
                    });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || data.message || 'Move file failed');
                    if (typeof showToast === 'function') showToast(data.message || 'File moved successfully!', 'success');
                } else if (pendingBatchMoveKeys && pendingBatchMoveKeys.length) {
                    const res = await fetch('/api/storage/batch-move', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            keys: pendingBatchMoveKeys, 
                            destination_prefix: targetFolderKey,
                            customer_id: currentStorageCustomerId
                        })
                    });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || data.message || 'Batch move failed');
                    if (typeof showToast === 'function') showToast(data.message || 'Files moved successfully!', 'success');
                }

                closeMoveFileModal();
                await refreshCurrentStorageFolder();
                const taxCid3 = currentStorageCustomerId || currentChecklistCustomerId;
                if (typeof loadTaxDocTracking === 'function' && taxCid3) {
                    loadTaxDocTracking(taxCid3);
                }
            } catch (err) {
                alert(`❌ Move Error: ${err.message}`);
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = (pendingBatchMoveKeys && pendingBatchMoveKeys.length) ? `🚚 Move ${pendingBatchMoveKeys.length} File(s) Now` : '🚚 Move File Now';
                }
            }
        }

        async function refreshCurrentStorageFolder() {
            if (currentStorageCustomerId) {
                await loadStorageFolder(currentStorageCustomerId, currentStoragePrefix);
            }
        }

        async function reinitStorageFromModal() {
            if (!currentStorageCustomerId) return;
            try {
                const res = await fetch(`/api/customers/${currentStorageCustomerId}/init-storage`, { method: 'POST' });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Init failed');
                alert(`✅ Storage initialized successfully!\n\nFolder Path: ${data.path}`);
                await refreshCurrentStorageFolder();
            } catch (err) {
                alert(`❌ Storage Init Error: ${err.message}`);
            }
        }

        async function createStorageFolder() {
            if (!currentStorageCustomerId) return;

            const folderName = prompt('Enter the name for the new folder:', '');
            if (folderName === null) return; // user cancelled
            const trimmed = folderName.trim();
            if (!trimmed) {
                alert('Folder name cannot be empty.');
                return;
            }

            const parentPrefix = currentStoragePrefix || currentStorageRootFolder;

            try {
                const res = await fetch(`/api/customers/${currentStorageCustomerId}/storage/mkdir`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ folder_name: trimmed, parent_prefix: parentPrefix })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Failed to create folder');
                await refreshCurrentStorageFolder();
            } catch (err) {
                alert(`❌ Create Folder Error: ${err.message}`);
            }
        }

        async function deleteStorageFolder(prefix, folderName, customerId) {
            const cid = customerId || currentStorageCustomerId;
            if (!cid || !prefix) return;

            if (!await showCustomConfirm(`⚠️ Delete folder "${folderName}"?\n\nThis will permanently delete the folder and ALL files inside it. This cannot be undone.`)) return;

            try {
                const res = await fetch(`/api/customers/${cid}/storage/folder?prefix=${encodeURIComponent(prefix)}`, {
                    method: 'DELETE'
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Delete failed');
                await refreshCurrentStorageFolder();
            } catch (err) {
                alert(`❌ Delete Folder Error: ${err.message}`);
            }
        }

        function getNextCustomerNumber() {
            let maxNum = 1000;
            if (typeof currentCustomerRecords !== 'undefined' && Array.isArray(currentCustomerRecords)) {
                currentCustomerRecords.forEach(c => {
                    const numStr = (c.custumer_number || '').toString();
                    const match = numStr.match(/\d+/);
                    if (match) {
                        const val = parseInt(match[0], 10);
                        if (!isNaN(val) && val > maxNum && val < 999999) {
                            maxNum = val;
                        }
                    }
                });
            }
            return 'CUST-' + (maxNum + 1);
        }

        function setLegalNameReadOnly(prefix, isReadOnly) {
            const el = document.getElementById(`${prefix}LegalName`);
            if (!el) return;
            el.readOnly = isReadOnly;
            if (isReadOnly) {
                el.style.background = 'rgba(255,255,255,0.03)';
                el.style.color = '#94a3b8';
                el.style.cursor = 'not-allowed';
                el.title = 'Legal Name cannot be modified when updating an existing customer.';
            } else {
                el.style.background = 'rgba(255,255,255,0.05)';
                el.style.color = '#ffffff';
                el.style.cursor = 'text';
                el.title = '';
            }
        }

        function setForm8879SelectValue(target, val) {
            const el = typeof target === 'string' ? document.getElementById(target) : target;
            if (!el) return;
            const str = String(val || '').toLowerCase().trim();
            if (!str) {
                el.value = "Form 8879 (Individual 1040)";
                return;
            }
            for (let i = 0; i < el.options.length; i++) {
                if (el.options[i].value === val) {
                    el.value = val;
                    return;
                }
            }
            if (str.includes('8879j') || str.includes('8879-j') || (str.includes('8879') && str.includes('joint'))) {
                el.value = "Form 8879J (Joint Account 1040)";
            } else if (str.includes('8879-c') || (str.includes('1120') && !str.includes('1120-s')) || str.includes('corp')) {
                el.value = "Form 8879-C (Corporation 1120)";
            } else if (str.includes('8879-s') || str.includes('1120-s') || str.includes('s-corp')) {
                el.value = "Form 8879-S (S-Corporation 1120-S)";
            } else if (str.includes('8879-pe') || str.includes('1065') || str.includes('partner')) {
                el.value = "Form 8879-PE (Partnership 1065)";
            } else if (str.includes('8879-f') || str.includes('1041') || str.includes('fiduc')) {
                el.value = "Form 8879-F (Fiduciary 1041)";
            } else if (str.includes('8879-eo') || str.includes('990') || str.includes('exempt')) {
                el.value = "Form 8879-EO (Exempt Org 990)";
            } else if (str.includes('8878') || str.includes('exten')) {
                el.value = "Form 8878 (Extension Authorization)";
            } else {
                el.value = "Form 8879 (Individual 1040)";
            }
        }

        function onCustomerTypeChange(prefix, autoSetForm8879 = true) {
            const typeVal = document.getElementById(`${prefix}Type`)?.value;
            const jointFields = document.getElementById(`${prefix}JointFields`);
            if (jointFields) {
                jointFields.style.display = (typeVal === 'Joint Account') ? 'block' : 'none';
            }
            if (autoSetForm8879) {
                const form8879Select = document.getElementById(`${prefix}Form8879Type`);
                if (form8879Select && typeVal) {
                    if (typeVal === 'Joint Account') {
                        setForm8879SelectValue(form8879Select, 'Form 8879J (Joint Account 1040)');
                    } else if (typeVal === 'Individual') {
                        setForm8879SelectValue(form8879Select, 'Form 8879 (Individual 1040)');
                    } else if (typeVal === 'S-Corporation') {
                        setForm8879SelectValue(form8879Select, 'Form 8879-S (S-Corporation 1120-S)');
                    } else if (typeVal === 'C-Corporation' || typeVal === 'Business') {
                        setForm8879SelectValue(form8879Select, 'Form 8879-C (Corporation 1120)');
                    } else if (typeVal === 'Partnership') {
                        setForm8879SelectValue(form8879Select, 'Form 8879-PE (Partnership 1065)');
                    } else if (typeVal === 'Estate/Trust') {
                        setForm8879SelectValue(form8879Select, 'Form 8879-F (Fiduciary 1041)');
                    } else if (typeVal === 'Non-Profit / Exempt Org') {
                        setForm8879SelectValue(form8879Select, 'Form 8879-EO (Exempt Org 990)');
                    }
                }
            }
        }

        function toggleCustomerForm() {
            const form = document.getElementById('customerForm');
            const btn = document.getElementById('toggleCustomerFormBtn');
            if (!form) return;
            if (form.style.display === 'none' || !form.style.display) {
                const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.value = val; };
                setVal('customerFormId', '');
                setVal('customerFormNumber', getNextCustomerNumber());
                setVal('customerFormType', 'Business');
                setForm8879SelectValue('customerFormForm8879Type', 'Form 8879 (Individual 1040)');
                setVal('customerFormSecondSignerName', '');
                setVal('customerFormSecondSignerEmail', '');
                setVal('customerFormSecondSignerPhone', '');
                setVal('customerFormLegalName', '');
                setVal('customerFormDisplayName', '');
                setVal('customerFormTaxId', '');
                setVal('customerFormAssignedUserId', '');
                setVal('customerFormStatus', 'Active');
                setVal('customerFormPhone', '');
                setVal('customerFormEmail', '');
                setVal('customerFormWebsite', '');
                setVal('customerFormNotes', '');
                onCustomerTypeChange('customerForm', true);
                const schedCb = document.getElementById('customerFormPresetSchedule');
                if (schedCb) schedCb.checked = true;
                const schedCont = document.getElementById('customerFormPresetScheduleContainer');
                if (schedCont) schedCont.style.display = 'flex';
                setLegalNameReadOnly('customerForm', false);
                const subBtn = document.getElementById('customerFormSubmitBtn');
                if (subBtn) subBtn.textContent = 'Save Customer';
                form.style.display = 'grid';
                if (btn) btn.textContent = 'Cancel';
            } else {
                form.style.display = 'none';
                if (btn) btn.textContent = '➕ Add New Customer';
            }
        }

        function toggleCustomerPageForm() {
            const form = document.getElementById('customerPageForm');
            if (!form) return;
            if (form.style.display === 'none' || !form.style.display) {
                const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.value = val; };
                setVal('customerPageFormId', '');
                setVal('customerPageFormNumber', getNextCustomerNumber());
                setVal('customerPageFormType', 'Business');
                setForm8879SelectValue('customerPageFormForm8879Type', 'Form 8879 (Individual 1040)');
                setVal('customerPageFormSecondSignerName', '');
                setVal('customerPageFormSecondSignerEmail', '');
                setVal('customerPageFormSecondSignerPhone', '');
                setVal('customerPageFormLegalName', '');
                setVal('customerPageFormDisplayName', '');
                setVal('customerPageFormTaxId', '');
                setVal('customerPageFormAssignedUserId', '');
                setVal('customerPageFormStatus', 'Active');
                setVal('customerPageFormPhone', '');
                setVal('customerPageFormEmail', '');
                setVal('customerPageFormWebsite', '');
                setVal('customerPageFormNotes', '');
                onCustomerTypeChange('customerPageForm', true);
                const schedCb = document.getElementById('customerPageFormPresetSchedule');
                if (schedCb) schedCb.checked = true;
                const schedCont = document.getElementById('customerPageFormPresetScheduleContainer');
                if (schedCont) schedCont.style.display = 'flex';
                setLegalNameReadOnly('customerPageForm', false);
                const subBtn = document.getElementById('customerPageFormSubmitBtn');
                if (subBtn) subBtn.textContent = 'Save Customer';
                form.style.display = 'grid';
            } else {
                form.style.display = 'none';
            }
        }

        function editCustomerRecord(id) {
            const rec = currentCustomerRecords.find(item => item.id == id);
            if (!rec) return;

            const modalForm = document.getElementById('customerForm');
            const pageForm = document.getElementById('customerPageForm');

            const populateForm = (prefix, targetForm) => {
                const setVal = (idKey, val) => { const el = document.getElementById(`${prefix}${idKey}`); if (el) el.value = val; };
                setVal('Id', rec.id);
                setVal('Number', rec.custumer_number || '');
                setVal('Type', rec.customer_type || 'Business');
                setForm8879SelectValue(`${prefix}Form8879Type`, rec.form_8879_type || 'Form 8879 (Individual 1040)');
                setVal('SecondSignerName', rec.second_signer_name || '');
                setVal('SecondSignerEmail', rec.second_signer_email || '');
                setVal('SecondSignerPhone', rec.second_signer_phone || '');
                setVal('LegalName', rec.legal_name || '');
                setVal('DisplayName', rec.display_name || '');
                setVal('TaxId', rec.tax_id || '');
                setVal('AssignedUserId', rec.assigned_user_id || '');
                setVal('Status', rec.status || 'Active');
                setVal('Phone', rec.phone || '');
                setVal('Email', rec.email || '');
                setVal('Website', rec.website || '');
                setVal('Notes', rec.notes || '');
                onCustomerTypeChange(prefix, false);
                const schedCont = document.getElementById(`${prefix}PresetScheduleContainer`);
                if (schedCont) schedCont.style.display = 'none';
                setLegalNameReadOnly(prefix, true);
                const subBtn = document.getElementById(`${prefix}SubmitBtn`);
                if (subBtn) subBtn.textContent = 'Update Customer';
                targetForm.style.display = 'grid';
            };

            if (pageForm) populateForm('customerPageForm', pageForm);
            if (modalForm) populateForm('customerForm', modalForm);
        }

        async function saveCustomerRecord(e, isPage = false) {
            e.preventDefault();
            const prefix = isPage ? 'customerPageForm' : 'customerForm';
            const getVal = (idKey) => (document.getElementById(`${prefix}${idKey}`)?.value || '').trim();
            const id = document.getElementById(`${prefix}Id`)?.value || '';
            const presetCb = document.getElementById(`${prefix}PresetSchedule`);
            const payload = {
                custumer_number: getVal('Number'),
                customer_type: getVal('Type') || 'Business',
                form_8879_type: getVal('Form8879Type') || 'Form 8879 (Individual 1040)',
                second_signer_name: getVal('SecondSignerName'),
                second_signer_email: getVal('SecondSignerEmail'),
                second_signer_phone: getVal('SecondSignerPhone'),
                legal_name: getVal('LegalName'),
                display_name: getVal('DisplayName'),
                tax_id: getVal('TaxId'),
                assigned_user_id: getVal('AssignedUserId'),
                status: getVal('Status') || 'Active',
                phone: getVal('Phone'),
                email: getVal('Email'),
                website: getVal('Website'),
                notes: getVal('Notes'),
                parent_name: CURRENT_PARENT_NAME,
                create_preset_schedule: presetCb ? presetCb.checked : true
            };

            try {
                const url = id ? `/api/customers/${id}` : '/api/customers';
                const method = id ? 'PUT' : 'POST';
                const res = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (res.ok) {
                    if (isPage) toggleCustomerPageForm();
                    else toggleCustomerForm();
                    await fetchCustomerRecords();
                    if (typeof fetchParentMappings === 'function') await fetchParentMappings();
                    if (typeof syncClientSelectDropdowns === 'function') await syncClientSelectDropdowns();
                    if (typeof populateCustomerDropdownForMappings === 'function') await populateCustomerDropdownForMappings();
                    if (typeof loadComplianceData === 'function') await loadComplianceData();
                } else {
                    const err = await res.json();
                    alert('Error saving customer: ' + (err.detail || err.error || 'Failed'));
                }
            } catch (err) {
                alert('Error saving customer: ' + err.message);
            }
        }

        function showDeleteCustomerConfirmModal(customerNum, legalName) {
            return new Promise((resolve) => {
                let modal = document.getElementById('deleteCustomerConfirmModal');
                if (!modal) {
                    modal = document.createElement('div');
                    modal.id = 'deleteCustomerConfirmModal';
                    modal.style.cssText = 'display: none; position: fixed; inset: 0; background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); z-index: 2147483647; justify-content: center; align-items: center; padding: 20px; animation: alertFadeIn 0.2s ease-out;';
                    modal.innerHTML = `
                        <div style="background: #0f172a; border: 1px solid rgba(244, 63, 94, 0.5); border-radius: 20px; max-width: 520px; width: 100%; display: flex; flex-direction: column; box-shadow: 0 25px 60px rgba(0, 0, 0, 0.9), 0 0 40px rgba(244, 63, 94, 0.25); color: #fff; overflow: hidden;">
                            <div style="padding: 28px 24px 16px 24px; display: flex; flex-direction: column; align-items: center; text-align: center; gap: 14px;">
                                <div style="width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.8rem; background: rgba(244, 63, 94, 0.15); border: 1px solid rgba(244, 63, 94, 0.4); color: #f43f5e;">
                                    ⚠️
                                </div>
                                <div style="width: 100%;">
                                    <h3 style="font-family: 'Outfit', sans-serif; font-size: 1.3rem; font-weight: 800; color: #f43f5e; margin: 0 0 10px 0; letter-spacing: -0.01em;">
                                        PERMANENT DELETE WARNING
                                    </h3>
                                    <div id="deleteCustomerWarningText" style="font-size: 0.88rem; color: #e2e8f0; line-height: 1.6; text-align: left; background: rgba(244, 63, 94, 0.08); border: 1px solid rgba(244, 63, 94, 0.25); border-radius: 12px; padding: 14px; margin-bottom: 16px;">
                                    </div>
                                    <div style="text-align: left;">
                                        <label style="display: block; font-size: 0.78rem; font-weight: 700; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">
                                            🔑 Enter Admin Password to Authorize Deletion:
                                        </label>
                                        <input type="password" id="deleteCustomerAdminPasswordInput" placeholder="Enter admin password..." style="width: 100%; background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(244, 63, 94, 0.4); border-radius: 10px; padding: 10px 14px; font-size: 0.92rem; color: #fff; outline: none; transition: border-color 0.2s ease;">
                                        <div id="deleteCustomerPasswordError" style="display: none; color: #fb7185; font-size: 0.78rem; font-weight: 600; margin-top: 6px;">
                                            Please enter the Admin Password to proceed.
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div style="padding: 16px 24px 24px 24px; display: flex; justify-content: flex-end; gap: 12px; border-top: 1px solid rgba(255, 255, 255, 0.08); background: rgba(0, 0, 0, 0.3);">
                                <button type="button" id="deleteCustomerCancelBtn" style="flex: 1; padding: 11px 18px; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15); color: #cbd5e1; font-weight: 700; border-radius: 10px; font-size: 0.85rem; cursor: pointer;">
                                    Cancel
                                </button>
                                <button type="button" id="deleteCustomerConfirmBtn" style="flex: 1; padding: 11px 18px; background: linear-gradient(135deg, #f43f5e, #be123c); color: #ffffff; font-weight: 800; border: none; border-radius: 10px; font-size: 0.85rem; cursor: pointer; box-shadow: 0 4px 14px rgba(244, 63, 94, 0.4);">
                                    PERMANENTLY DELETE
                                </button>
                            </div>
                        </div>
                    `;
                    document.body.appendChild(modal);
                }

                const warningEl = document.getElementById('deleteCustomerWarningText');
                const pwdInput = document.getElementById('deleteCustomerAdminPasswordInput');
                const pwdErr = document.getElementById('deleteCustomerPasswordError');
                const cancelBtn = document.getElementById('deleteCustomerCancelBtn');
                const confirmBtn = document.getElementById('deleteCustomerConfirmBtn');

                const displayNameStr = legalName ? `'${legalName}' (${customerNum})` : `'${customerNum}'`;

                warningEl.innerHTML = `
                    <strong>This action will remove all records in all files and tables related to customer <span style="color: #f43f5e;">${safeEscapeHtml(displayNameStr)}</span></strong> (including Parent Mappings, Chart of Accounts, task checklists, and Vendor Rules).<br><br>
                    <span style="color: #f87171; font-weight: 700;">⚠️ You will NOT be able to restore any data after this action.</span>
                `;

                pwdInput.value = '';
                pwdErr.style.display = 'none';
                modal.style.display = 'flex';

                setTimeout(() => pwdInput.focus(), 100);

                const handleCancel = () => {
                    modal.style.display = 'none';
                    cleanupListeners();
                    resolve(null);
                };

                const handleConfirm = () => {
                    const val = (pwdInput.value || '').trim();
                    if (!val) {
                        pwdErr.style.display = 'block';
                        pwdInput.focus();
                        return;
                    }
                    modal.style.display = 'none';
                    cleanupListeners();
                    resolve(val);
                };

                const handleKeyDown = (e) => {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        handleConfirm();
                    } else if (e.key === 'Escape') {
                        e.preventDefault();
                        handleCancel();
                    }
                };

                function cleanupListeners() {
                    cancelBtn.removeEventListener('click', handleCancel);
                    confirmBtn.removeEventListener('click', handleConfirm);
                    pwdInput.removeEventListener('keydown', handleKeyDown);
                }

                cancelBtn.addEventListener('click', handleCancel);
                confirmBtn.addEventListener('click', handleConfirm);
                pwdInput.addEventListener('keydown', handleKeyDown);
            });
        }

        async function deleteCustomerRecord(arg1, arg2, arg3, arg4) {
            let event = null, id = arg1, num = arg2, legalName = arg3 || '';
            if (arg1 && arg1.preventDefault) {
                event = arg1;
                event.preventDefault();
                event.stopPropagation();
                id = arg2;
                num = arg3;
                legalName = arg4 || '';
            }
            if (!id) return;
            const adminPassword = await showDeleteCustomerConfirmModal(num, legalName);
            if (!adminPassword) return;

            try {
                const res = await fetch(`/api/customers/${id}?admin_password=${encodeURIComponent(adminPassword)}`, {
                    method: 'DELETE',
                    headers: {
                        'X-Admin-Password': adminPassword
                    }
                });
                if (res.ok) {
                    await fetchCustomerRecords();
                    if (typeof fetchParentMappings === 'function') await fetchParentMappings();
                    if (typeof syncClientSelectDropdowns === 'function') await syncClientSelectDropdowns();
                    if (typeof populateCustomerDropdownForMappings === 'function') await populateCustomerDropdownForMappings();
                    if (typeof loadComplianceData === 'function') await loadComplianceData();
                    showAlert('Customer and all related records, files, and rules deleted successfully.', 'success', 'Customer Deleted');
                } else {
                    const err = await res.json();
                    showAlert('Error deleting customer: ' + (err.detail || err.error || 'Failed'), 'error', 'Delete Failed');
                }
            } catch (err) {
                showAlert('Error deleting customer: ' + err.message, 'error', 'Delete Error');
            }
        }

        // Load customer page data if active tab is customers or URL pathname is /customers
        if (window.location.pathname === '/customers' || '{{ active_tab }}' === 'customers') {
            fetchCustomerRecords(true);
        }

        // --- PDF Viewer Modal Functions ---
        function openPdfViewerModal(event, s3KeyOrUrl, fileName, rawUrl) {
            if (event) {
                event.stopPropagation();
                if (event.preventDefault) event.preventDefault();
            }
            let modal = document.getElementById('pdfViewerModal');
            if (!modal) return;
            const titleEl = document.getElementById('pdfViewerTitle');
            const iframeEl = document.getElementById('pdfViewerIframe');
            const extBtn = document.getElementById('pdfViewerExternalBtn');
            const dlBtn = document.getElementById('pdfViewerDownloadBtn');

            // Use in-app view-pdf and download streaming endpoints to stream files with correct headers
            const keyParam = encodeURIComponent(s3KeyOrUrl || '');
            const inlineViewUrl = `/api/storage/view-pdf?key=${keyParam}`;
            const downloadUrl = `/api/storage/download?key=${keyParam}`;

            if (titleEl) titleEl.textContent = fileName || 'PDF Document Viewer';
            if (iframeEl) iframeEl.src = inlineViewUrl;
            if (extBtn) extBtn.href = inlineViewUrl;
            if (dlBtn) dlBtn.href = downloadUrl;

            // Unconditionally append to body so pdfViewerModal is moved to the end of DOM and renders on top of all open modals
            document.body.appendChild(modal);
            modal.style.zIndex = '2147483655';
            modal.style.display = 'flex';
            modal.style.opacity = '1';
        }

        function closePdfViewerModal() {
            const modal = document.getElementById('pdfViewerModal');
            if (!modal) return;
            modal.style.opacity = '0';
            setTimeout(() => { modal.style.display = 'none'; }, 150);
            const iframeEl = document.getElementById('pdfViewerIframe');
            if (iframeEl) iframeEl.src = '';
        }

        // --- Customer Bookkeeping Workflow Checklist Functions ---
        let currentChecklistCustomerId = null;
        let currentChecklistPeriod = null;

        async function openCustomerChecklistModal(event, customerId, period, customerType) {
            if (event) event.stopPropagation();
            currentChecklistCustomerId = customerId;
            let modal = document.getElementById('customerChecklistModal');
            if (!modal) return;

            if (modal.parentElement !== document.body) {
                document.body.appendChild(modal);
            }

            // Fallback: look up customerType from currentCustomerRecords if not explicitly passed
            if (!customerType && typeof currentCustomerRecords !== 'undefined' && Array.isArray(currentCustomerRecords)) {
                const found = currentCustomerRecords.find(c => String(c.id) === String(customerId));
                if (found) {
                    customerType = found.customer_type || found.type || '';
                }
            }

            const isIndividual = ['individual', 'joint account'].includes((customerType || '').toString().trim().toLowerCase());
            const bkTabBtn = document.getElementById('tabBkWorkflow');
            if (bkTabBtn) {
                bkTabBtn.style.display = isIndividual ? 'none' : 'inline-flex';
            }

            if (isIndividual) {
                switchWorkflowTab('tax');
            } else {
                switchWorkflowTab('bookkeeping');
            }

            modal.style.display = 'flex';
            modal.style.opacity = '1';

            await loadCustomerChecklist(customerId, period);
        }

        function closeCustomerChecklistModal() {
            const modal = document.getElementById('customerChecklistModal');
            if (!modal) return;
            modal.style.display = 'none';
            modal.style.opacity = '0';
            currentChecklistCustomerId = null;
            if (typeof fetchPendingWorkload === 'function') {
                fetchPendingWorkload();
            }
        }

        // --- Customer Email Communication Functions ---
        let currentEmailCustomerId = null;

        async function openSendCustomerEmailModal(event, customerId) {
            if (event) event.stopPropagation();
            const cid = customerId || currentChecklistCustomerId;
            if (!cid) return;

            let cust = (typeof currentCustomerRecords !== 'undefined' && Array.isArray(currentCustomerRecords))
                ? currentCustomerRecords.find(c => c.id == cid)
                : null;

            if (!cust && typeof rawWorkloadData !== 'undefined' && Array.isArray(rawWorkloadData)) {
                cust = rawWorkloadData.find(w => w.customer_id == cid || w.id == cid);
            }

            if (!cust || !cust.email) {
                try {
                    const res = await fetch(`/api/customers/${cid}`);
                    if (res.ok) {
                        const fetchedCust = await res.json();
                        if (fetchedCust) cust = Object.assign({}, cust || {}, fetchedCust);
                    }
                } catch(e) {}
            }

            currentEmailCustomerId = cid;
            let modal = document.getElementById('sendCustomerEmailModal');
            if (!modal) return;
            if (modal.parentElement !== document.body) document.body.appendChild(modal);

            const titleEl = document.getElementById('sendEmailModalTitle');
            const subtitleEl = document.getElementById('sendEmailModalSubtitle');
            const toEl = document.getElementById('emailFormTo');
            const replyToEl = document.getElementById('emailFormReplyTo');
            const tplEl = document.getElementById('emailFormTemplateSelect');

            const custName = cust ? (cust.legal_name || cust.display_name || cust.customer_name) : `Customer #${cid}`;
            const custNum = cust ? (cust.custumer_number || cust.customer_id || cust.id) : cid;
            const custEmail = cust ? (cust.email || '') : '';

            if (titleEl) titleEl.textContent = `📧 Send Email — ${custName}`;
            if (subtitleEl) subtitleEl.textContent = `Customer #: ${custNum} | Email: ${custEmail || 'Not configured'}`;
            if (toEl) toEl.value = custEmail;
            let defaultReplyTo = (typeof RESEND_REPLY_TO_EMAIL !== 'undefined' && RESEND_REPLY_TO_EMAIL) ? RESEND_REPLY_TO_EMAIL : 'notification@vrtservices12.com';
            if (!defaultReplyTo || defaultReplyTo.includes('receive.datalazo.net')) {
                defaultReplyTo = 'notification@vrtservices12.com';
            }
            if (replyToEl) replyToEl.value = defaultReplyTo;
            if (tplEl) tplEl.value = 'custom';

            applyEmailTemplate('custom', cust || { legal_name: custName, custumer_number: custNum, email: custEmail });
            modal.style.zIndex = '2147483648';
            modal.style.display = 'flex';
        }

        function closeSendCustomerEmailModal() {
            const modal = document.getElementById('sendCustomerEmailModal');
            if (modal) modal.style.display = 'none';
        }

        function applyEmailTemplate(type, custData) {
            const subjectEl = document.getElementById('emailFormSubject');
            const msgEl = document.getElementById('emailFormMessage');
            if (!subjectEl || !msgEl) return;

            const cust = custData || currentCustomerRecords.find(c => c.id == currentEmailCustomerId) || {};
            const name = cust.legal_name || cust.display_name || 'Client';

            if (type === 'tax_docs') {
                subjectEl.value = `Tax Organizer & Document Request for ${name}`;
                msgEl.value = `Dear ${name},\n\nWe hope this message finds you well.\n\nWe are preparing your upcoming Tax Return. Please provide your tax organizer details along with your W-2s, 1099s, K-1s, and any relevant tax document statements.\n\nYou can reply directly to this email with your PDF/image attachments, or upload them to your client portal.\n\nThank you,\nAccount Management Team`;
            } else if (type === 'bk_stmt') {
                subjectEl.value = `Monthly Bank Statement Request - ${name}`;
                msgEl.value = `Dear ${name},\n\nThis is a reminder regarding your monthly bookkeeping process.\n\nPlease send us your latest bank and credit card statements so our accounting team can extract and categorize your transactions.\n\nSimply reply to this email with your statements attached.\n\nBest regards,\nAccounting Department`;
            } else if (type === 'sign_8879') {
                subjectEl.value = `Action Required: Form 8879 E-Signature - ${name}`;
                msgEl.value = `Dear ${name},\n\nYour Tax Return preparation and review has been completed!\n\nAttached / linked is Form 8879 for your authorization. Please sign and reply to this email with the signed authorization so we can e-file your return with the IRS & State taxing authorities.\n\nThank you,\nTax Preparation Team`;
            } else {
                subjectEl.value = `Information Update - ${name}`;
                msgEl.value = `Dear ${name},\n\n`;
            }
        }

        async function submitSendCustomerEmail() {
            if (!currentEmailCustomerId) return;
            const toVal = document.getElementById('emailFormTo')?.value || '';
            const replyToVal = document.getElementById('emailFormReplyTo')?.value || '';
            const subjectVal = document.getElementById('emailFormSubject')?.value || '';
            const msgVal = document.getElementById('emailFormMessage')?.value || '';
            const submitBtn = document.getElementById('sendEmailSubmitBtn');

            if (!toVal) {
                alert('❌ Customer does not have an email address configured. Please edit customer and add an email address first.');
                return;
            }
            if (!subjectVal || !msgVal) {
                alert('❌ Subject line and Message body are required.');
                return;
            }

            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = '⏳ Sending...';
            }

            try {
                const res = await fetch(`/api/customers/${currentEmailCustomerId}/send-email`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        subject: subjectVal,
                        message: msgVal,
                        reply_to: replyToVal
                    })
                });
                const data = await res.json();
                if (!res.ok) {
                    let errDetail = 'Failed to send email';
                    if (typeof data.detail === 'string') errDetail = data.detail;
                    else if (Array.isArray(data.detail)) errDetail = data.detail.map(d => d.msg || d.detail || JSON.stringify(d)).join(', ');
                    else if (data.message) errDetail = data.message;
                    throw new Error(errDetail);
                }

                alert(`✅ ${data.message}\nReply-To configured as: ${data.reply_to}`);
                closeSendCustomerEmailModal();
            } catch (err) {
                alert(`❌ Email Error: ${err.message}`);
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = '🚀 Send Email';
                }
            }
        }

        async function checkUnreadCommunicationsAlerts() {
            try {
                const res = await fetch('/api/communications/unread-summary');
                const data = await res.json();
                const total = data.total_unread || 0;
                currentUnreadMap = data.unread_by_customer || {};

                const badge = document.getElementById('headerUnreadEmailBadge');
                const badgeText = document.getElementById('headerUnreadCountText');
                if (badge && badgeText) {
                    if (total > 0) {
                        badgeText.textContent = `${total} New ${total === 1 ? 'Reply' : 'Replies'}`;
                        badge.style.display = 'flex';
                    } else {
                        badge.style.display = 'none';
                    }
                }

                // Update unread green dots and counts across customer table rows
                document.querySelectorAll('.unread-reply-dot').forEach(dot => {
                    const cid = parseInt(dot.getAttribute('data-cid'), 10);
                    if (cid && currentUnreadMap[cid] && currentUnreadMap[cid].unread_count > 0) {
                        const cnt = currentUnreadMap[cid].unread_count;
                        dot.textContent = `🟢 ${cnt} NEW`;
                        dot.style.display = 'inline-block';
                    } else {
                        dot.style.display = 'none';
                    }
                });
                document.querySelectorAll('.unread-history-badge').forEach(badgeEl => {
                    const cid = parseInt(badgeEl.getAttribute('data-cid'), 10);
                    if (cid && currentUnreadMap[cid] && currentUnreadMap[cid].unread_count > 0) {
                        const cnt = currentUnreadMap[cid].unread_count;
                        badgeEl.textContent = `${cnt} NEW`;
                        badgeEl.style.display = 'inline-block';
                    } else {
                        badgeEl.style.display = 'none';
                    }
                });
            } catch (err) {
                console.log('Error checking unread communications:', err);
            }
        }
        setInterval(checkUnreadCommunicationsAlerts, 15000);
        document.addEventListener('DOMContentLoaded', checkUnreadCommunicationsAlerts);

        function clearAllUnreadAlerts(event) {
            if (event) {
                event.preventDefault();
                event.stopPropagation();
            }
        }

        function formatEasternDateTime(dateInput) {
            if (!dateInput) return '';
            let d;
            if (dateInput instanceof Date) {
                d = dateInput;
            } else {
                let str = String(dateInput).trim();
                if (!str) return '';
                if (!str.includes('Z') && !str.includes('+') && !str.match(/-\d{2}:\d{2}$/)) {
                    str = str.replace(' ', 'T') + 'Z';
                }
                d = new Date(str);
            }
            if (isNaN(d.getTime())) {
                d = new Date(dateInput);
            }
            if (isNaN(d.getTime())) return String(dateInput);

            return d.toLocaleString('en-US', {
                timeZone: 'America/New_York',
                month: 'numeric',
                day: 'numeric',
                year: 'numeric',
                hour: 'numeric',
                minute: '2-digit',
                second: '2-digit',
                hour12: true
            }) + ' ET';
        }

        let activeHistoryCustomerId = null;

        async function openCatchallInboxModal() {
            await openCustomerCommsHistoryModal(null, true);
        }

        async function openCustomerCommsHistoryModal(customerId, showAllInbound = false) {
            const cid = customerId || currentEmailCustomerId;
            if (!cid && !showAllInbound) return;
            activeHistoryCustomerId = cid;

            let modal = document.getElementById('customerCommsHistoryModal');
            if (!modal) return;
            if (modal.parentElement !== document.body) document.body.appendChild(modal);

            const titleEl = document.getElementById('commsHistoryModalTitle');
            const subtitleEl = document.getElementById('commsHistoryModalSubtitle');

            const cust = (!showAllInbound && typeof currentCustomerRecords !== 'undefined' && Array.isArray(currentCustomerRecords))
                ? currentCustomerRecords.find(c => c.id == cid)
                : null;

            if (titleEl) {
                titleEl.innerHTML = showAllInbound 
                    ? `📥 Global Inbound Inbox` 
                    : `💬 Customer Communication History`;
            }

            if (subtitleEl) {
                if (showAllInbound) {
                    subtitleEl.textContent = 'All incoming client email replies and general unassigned emails across all accounts';
                } else if (cust) {
                    subtitleEl.innerHTML = `Customer: <strong style="color: #38bdf8;">${cust.legal_name || cust.display_name}</strong> (${cust.custumer_number ? 'Ref: ' + cust.custumer_number + ' | ' : ''}${cust.email ? 'Email: ' + cust.email : 'No email set'})`;
                } else {
                    subtitleEl.textContent = `Customer ID #${cid} — Email logs & received replies`;
                }
            }

            const listBody = document.getElementById('commsHistoryListBody');
            if (listBody) listBody.innerHTML = '<p style="text-align: center; color: #94a3b8;">Loading communications history...</p>';

            modal.style.display = 'flex';

            try {
                const fetchUrl = showAllInbound 
                    ? '/api/communications/all-inbound' 
                    : `/api/customers/${cid}/communications`;
                const res = await fetch(fetchUrl);
                if (!res.ok) {
                    const errText = await res.text();
                    let errMsg = `HTTP ${res.status}`;
                    try {
                        const errJson = JSON.parse(errText);
                        errMsg = errJson.detail || errJson.message || errMsg;
                    } catch(e) {}
                    throw new Error(errMsg);
                }
                const data = await res.json();
                const logs = data.communications || [];

                if (logs.length === 0) {
                    const custName = cust ? (cust.legal_name || cust.display_name) : (showAllInbound ? 'All Customers' : `Customer #${cid}`);
                    if (listBody) {
                        listBody.innerHTML = `
                            <div style="text-align: center; color: #64748b; padding: 36px 20px;">
                                <div style="font-size: 2.8rem; margin-bottom: 12px;">📭</div>
                                <h4 style="color: #cbd5e1; margin: 0 0 6px 0; font-size: 1.05rem;">No Inbound Email History Found</h4>
                                <p style="font-size: 0.82rem; color: #94a3b8; max-width: 440px; margin: 0 auto; line-height: 1.5;">No email communications were found for <strong style="color: #38bdf8;">${custName}</strong>.</p>
                            </div>
                        `;
                    }
                    return;
                }

                if (listBody) {
                    const unreadLogs = logs.filter(l => l.direction === 'INBOUND' && !l.is_read && l.status !== 'READ');
                    const markAllBtn = document.getElementById('commsHistoryMarkAllReadBtn');
                    if (markAllBtn) {
                        markAllBtn.style.display = (unreadLogs.length > 0 && !showAllInbound) ? 'inline-block' : 'none';
                    }

                    listBody.innerHTML = logs.map(item => {
                        const isOut = item.direction === 'OUTBOUND';
                        const isRead = item.is_read || item.status === 'READ';
                        const readDateStr = item.read_at ? formatEasternDateTime(item.read_at) : '';

                        let dirBadge = '';
                        if (isOut) {
                            dirBadge = '<span style="background: rgba(6, 182, 212, 0.2); color: #06b6d4; border: 1px solid rgba(6, 182, 212, 0.4); padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 0.7rem;">OUTBOUND SENT</span>';
                        } else {
                            const readBadge = isRead
                                ? `<span id="readStatusBadge-${item.id}" style="background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.35); padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 0.7rem;" title="Message read">👁️ READ ${readDateStr ? '(' + readDateStr + ')' : ''}</span>`
                                : `<span id="readStatusBadge-${item.id}" onclick="markSingleCommRead(event, ${item.id})" style="background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.5); padding: 2px 8px; border-radius: 6px; font-weight: 800; font-size: 0.72rem; cursor: pointer; box-shadow: 0 0 8px rgba(239, 68, 68, 0.4);" title="Click to mark this email reply as read and stamp read date">🟢 UNREAD — Click to Mark Read</span>`;
                            
                            dirBadge = '<span style="background: rgba(0, 230, 118, 0.2); color: #00e676; border: 1px solid rgba(0, 230, 118, 0.4); padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 0.7rem;">INBOUND REPLIED</span> ' + readBadge;
                        }

                        const custTag = (showAllInbound || !cust)
                            ? (item.legal_name 
                                ? `<span style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.35); padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 0.7rem;">Account: ${item.legal_name} (${item.custumer_number || 'ID #' + item.customer_id})</span> `
                                : `<span style="background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.35); padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 0.7rem;">Unassigned / Catch-All</span> `)
                            : '';

                        const dateStr = item.created_at ? formatEasternDateTime(item.created_at) : '';
                        let atts = item.attachments_json || [];
                        if (typeof atts === 'string') {
                            try { atts = JSON.parse(atts); } catch(e) { atts = []; }
                        }
                        if (!Array.isArray(atts)) atts = [];

                        let attHtml = '';
                        if (atts.length > 0) {
                            attHtml = '<div style="margin-top: 8px; font-size: 0.75rem; color: #38bdf8;"><strong>📎 Saved Attachments:</strong> ' + atts.map(a => {
                                if (!a) return '';
                                let filePath = '';
                                let fileName = '';
                                if (typeof a === 'object' && a !== null) {
                                    filePath = a.file_key || a.path || a.filename || a.name || '';
                                    fileName = a.filename || a.name || (filePath ? String(filePath).split('/').pop() : 'Attachment');
                                } else {
                                    filePath = String(a);
                                    fileName = filePath.split('/').pop();
                                }
                                if (!filePath) filePath = fileName;
                                const escKey = String(filePath).replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '&quot;');
                                const escName = String(fileName).replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '&quot;');
                                return `<a href="#" onclick="openPdfViewerModal(event, '${escKey}', '${escName}'); return false;" style="color: #38bdf8; text-decoration: underline; margin-right: 8px;">${fileName}</a>`;
                            }).filter(Boolean).join(' ') + '</div>';
                        }

                        const displayBody = (item.body_text && item.body_text.trim()) 
                            ? item.body_text 
                            : (atts && atts.length > 0)
                                ? '<span style="color: #38bdf8; font-style: italic;">📎 Attachment received (no text message body provided).</span>'
                                : '<span style="color: #64748b; font-style: italic;">(No text body in email)</span>';

                        const cardBorder = (!isOut && !isRead) ? 'rgba(239, 68, 68, 0.4)' : 'rgba(255,255,255,0.08)';
                        const cardBg = (!isOut && !isRead) ? 'rgba(239, 68, 68, 0.04)' : 'rgba(255,255,255,0.03)';
                        const cardClickAttr = (!isOut && !isRead) ? `onclick="markSingleCommRead(event, ${item.id})"` : '';

                        return `
                            <div id="commCard-${item.id}" ${cardClickAttr} style="background: ${cardBg}; border: 1px solid ${cardBorder}; border-radius: 12px; padding: 14px; display: flex; flex-direction: column; gap: 8px; ${ (!isOut && !isRead) ? 'cursor: pointer;' : '' } transition: all 0.2s;">
                                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                                    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                                        ${dirBadge}
                                        ${custTag}
                                        <strong style="font-size: 0.88rem; color: #fff;">${item.subject || '(No Subject)'}</strong>
                                    </div>
                                    <span style="font-size: 0.75rem; color: #64748b;">${dateStr}</span>
                                </div>
                                <div style="font-size: 0.78rem; color: #94a3b8;">
                                    From: <span style="color: #cbd5e1;">${item.sender_email}</span> | To: <span style="color: #cbd5e1;">${item.recipient_email}</span> ${item.reply_to_email ? `| Reply-To: <span style="color: #facc15;">${item.reply_to_email}</span>` : ''}
                                </div>
                                <div style="white-space: pre-wrap; font-size: 0.85rem; color: #e2e8f0; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px; margin-top: 4px;">${displayBody}</div>
                                ${attHtml}
                            </div>
                        `;
                    }).join('');
                }
            } catch (err) {
                if (listBody) listBody.innerHTML = `<p style="text-align: center; color: #f87171; padding: 20px;">Error loading communications: ${err.message}</p>`;
            }
        }

        async function markSingleCommRead(event, commId) {
            if (event) event.stopPropagation();
            const badgeEl = document.getElementById(`readStatusBadge-${commId}`);
            const cardEl = document.getElementById(`commCard-${commId}`);

            try {
                const res = await fetch(`/api/communications/${commId}/mark-single-read`, { method: 'POST' });
                const data = await res.json();
                if (res.ok && data.success) {
                    const readDateStr = data.read_at ? formatEasternDateTime(data.read_at) : formatEasternDateTime(new Date());
                    if (badgeEl) {
                        badgeEl.innerHTML = `👁️ READ (${readDateStr})`;
                        badgeEl.style.background = 'rgba(34, 197, 94, 0.15)';
                        badgeEl.style.color = '#4ade80';
                        badgeEl.style.border = '1px solid rgba(34, 197, 94, 0.35)';
                        badgeEl.style.boxShadow = 'none';
                        badgeEl.onclick = null;
                    }
                    if (cardEl) {
                        cardEl.style.borderColor = 'rgba(255,255,255,0.08)';
                        cardEl.style.background = 'rgba(255,255,255,0.03)';
                        cardEl.onclick = null;
                        cardEl.style.cursor = 'default';
                    }
                    await checkUnreadCommunicationsAlerts();
                }
            } catch (err) {
                console.error("Error marking single communication read:", err);
            }
        }

        async function markAllCommsReadForCurrentCustomer() {
            if (!activeHistoryCustomerId) return;
            try {
                await fetch(`/api/customers/${activeHistoryCustomerId}/communications/mark-read`, { method: 'POST' });
                await openCustomerCommsHistoryModal(activeHistoryCustomerId);
                await checkUnreadCommunicationsAlerts();
            } catch (e) {
                console.error("Error marking all comms read:", e);
            }
        }

        function closeCustomerCommsHistoryModal() {
            const modal = document.getElementById('customerCommsHistoryModal');
            if (modal) modal.style.display = 'none';
            const debugBox = document.getElementById('webhookDebugLogBox');
            if (debugBox) debugBox.remove();

            const pdfModal = document.getElementById('pdfViewerModal');
            if (pdfModal && pdfModal.style.display !== 'none') {
                pdfModal.style.zIndex = '2147483649';
            }
        }

        async function toggleWebhookLogInspector(event) {
            if (event) event.stopPropagation();
            let debugBox = document.getElementById('webhookDebugLogBox');
            if (debugBox) {
                debugBox.style.display = (debugBox.style.display === 'none') ? 'block' : 'none';
                return;
            }
            const listBody = document.getElementById('commsHistoryListBody');
            if (!listBody) return;
            
            const newBox = document.createElement('div');
            newBox.id = 'webhookDebugLogBox';
            newBox.style.cssText = 'background: #0f172a; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 12px; padding: 14px; margin-bottom: 16px; font-size: 0.78rem; font-family: monospace; color: #cbd5e1;';
            newBox.innerHTML = 'Loading server webhook debug logs...';
            listBody.insertBefore(newBox, listBody.firstChild);

            try {
                const res = await fetch('/api/debug/last-inbound');
                const data = await res.json();
                const logs = data.last_webhook_logs || [];
                if (logs.length === 0) {
                    newBox.innerHTML = '<strong style="color: #f87171;">⚠️ No Webhooks Received Yet:</strong><br><span style="color: #94a3b8;">The server has not received any HTTP POST webhooks from Resend yet.<br>Please verify in <a href="https://resend.com/webhooks" target="_blank" style="color: #38bdf8; text-decoration: underline;">Resend Dashboard → Webhooks</a> that a Webhook is configured pointing to:<br><code style="color: #4ade80;">https://vrtservices12.com/api/webhooks/resend-inbound</code> for event <code>email.received</code>.</span>';
                } else {
                    let html = '<strong style="color: #38bdf8;">📡 Server Webhook Log Audit (Last 5 Hits):</strong><br><br>';
                    html += logs.map(l => `
                        <div style="border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 6px; margin-bottom: 6px;">
                            <span style="color: #facc15;">[${l.created_at || ''}]</span> 
                            <strong>Status:</strong> <span style="color: ${l.status === 'SUCCESS' ? '#4ade80' : '#f87171'}; font-weight: 800;">${l.status}</span><br>
                            <strong>From:</strong> ${l.sender_email || 'N/A'} | <strong>To:</strong> ${l.recipient_email || 'N/A'}<br>
                            <strong>Subject:</strong> ${l.subject || '(No Subject)'}
                        </div>
                    `).join('');
                    newBox.innerHTML = html;
                }
            } catch(err) {
                newBox.innerHTML = `<span style="color: #f87171;">Error fetching debug logs: ${err.message}</span>`;
            }
        }

        // --- Workload Summary & Pending Tasks Functions ---
        let rawWorkloadData = [];
        let currentWorkloadFilter = 'all';
        let currentWorkloadUserFilter = 'all';

        async function loadWorkloadSummary() {
            const tbody = document.getElementById('workloadPendingTableBody');
            if (!tbody) return;
            try {
                const parentParam = typeof CURRENT_PARENT_NAME !== 'undefined' ? CURRENT_PARENT_NAME : (window.parentName || '');
                const res = await fetch(`/api/dashboard/pending-tasks?parentName=${encodeURIComponent(parentParam)}`);
                const data = await res.json();
                rawWorkloadData = data.pending_tasks || [];

                const summary = data.summary || {};
                const kpiBk = document.getElementById('kpiPendingBkCount');
                const kpiTax = document.getElementById('kpiPendingTaxCount');
                const kpiTotal = document.getElementById('kpiTotalIncompleteCount');

                if (kpiBk) kpiBk.textContent = summary.pending_bookkeeping_count || 0;
                if (kpiTax) kpiTax.textContent = summary.pending_tax_count || 0;
                if (kpiTotal) kpiTotal.textContent = summary.total_incomplete_customers || 0;

                updateWorkloadUserDropdown();
                renderWorkloadTable();
            } catch (err) {
                console.error('Error loading workload summary:', err);
                if (tbody) tbody.innerHTML = '<tr><td colSpan="6" style="padding: 24px; text-align: center; color: #ff5252;">Failed to load workload tasks.</td></tr>';
            }
        }

        function updateWorkloadUserDropdown() {
            const select = document.getElementById('workloadAssignedUserSelect');
            if (!select) return;
            const currentVal = select.value || 'all';

            const usersSet = new Set();
            (rawWorkloadData || []).forEach(i => {
                const uStr = i.assigned_user_id ? String(i.assigned_user_id).trim() : '';
                if (uStr) {
                    usersSet.add(uStr);
                }
            });

            const sortedUsers = Array.from(usersSet).sort((a, b) => a.localeCompare(b));
            let html = `<option value="all" style="background: #0f172a; color: #fff;">All Assigned Users</option>`;
            html += `<option value="unassigned" style="background: #0f172a; color: #fff;">Unassigned Only</option>`;
            sortedUsers.forEach(u => {
                const escaped = u.replace(/"/g, '&quot;');
                html += `<option value="${escaped}" style="background: #0f172a; color: #fff;">${u}</option>`;
            });
            select.innerHTML = html;
            if (Array.from(select.options).some(o => o.value === currentVal)) {
                select.value = currentVal;
            } else {
                select.value = 'all';
                currentWorkloadUserFilter = 'all';
            }
        }

        function filterWorkloadAssignedUserChanged() {
            const select = document.getElementById('workloadAssignedUserSelect');
            if (select) {
                currentWorkloadUserFilter = select.value;
            }
            renderWorkloadTable();
        }

        function filterWorkloadTable(mode) {
            currentWorkloadFilter = mode;
            ['btnFilterWorkloadAll', 'btnFilterWorkloadBk', 'btnFilterWorkloadTax'].forEach(id => {
                const btn = document.getElementById(id);
                if (btn) {
                    btn.style.background = 'rgba(255, 255, 255, 0.05)';
                    btn.style.borderColor = 'rgba(255, 255, 255, 0.12)';
                    btn.style.color = '#94a3b8';
                }
            });

            const activeBtnId = mode === 'bk' ? 'btnFilterWorkloadBk' : (mode === 'tax' ? 'btnFilterWorkloadTax' : 'btnFilterWorkloadAll');
            const activeBtn = document.getElementById(activeBtnId);
            if (activeBtn) {
                activeBtn.style.background = 'rgba(250, 204, 21, 0.2)';
                activeBtn.style.borderColor = 'rgba(250, 204, 21, 0.5)';
                activeBtn.style.color = '#facc15';
            }
            renderWorkloadTable();
        }

        function renderWorkloadTable() {
            const tbody = document.getElementById('workloadPendingTableBody');
            if (!tbody) return;

            let items = (rawWorkloadData || []).filter(i => {
                const cNum = (i.custumer_number || '').toUpperCase();
                const dName = (i.display_name || '').toUpperCase();
                const lName = (i.legal_name || '').toUpperCase();
                return cNum !== 'CUST-0000' && !dName.includes('CUST-0000') && !lName.includes('UNASSIGNED INBOUND');
            });
            if (currentWorkloadFilter === 'bk') {
                items = items.filter(i => i.bk && i.bk.has_pending);
            } else if (currentWorkloadFilter === 'tax') {
                items = items.filter(i => i.tax && i.tax.has_pending);
            }

            if (currentWorkloadUserFilter === 'unassigned') {
                items = items.filter(i => !i.assigned_user_id || !String(i.assigned_user_id).trim());
            } else if (currentWorkloadUserFilter && currentWorkloadUserFilter !== 'all') {
                items = items.filter(i => String(i.assigned_user_id || '').trim().toLowerCase() === currentWorkloadUserFilter.trim().toLowerCase());
            }

            if (items.length === 0) {
                tbody.innerHTML = '<tr><td colSpan="5" style="padding: 32px; text-align: center; color: #38ef7d; font-weight: 700;">🎉 All caught up! No pending tasks found for this filter.</td></tr>';
                return;
            }

            tbody.innerHTML = items.map(item => {
                const isInd = item.is_individual;
                const typeBadge = isInd 
                    ? '<span style="background: rgba(168, 85, 247, 0.2); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.4); padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 0.72rem;">Individual</span>'
                    : '<span style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4); padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 0.72rem;">Business</span>';

                let bkProgressPercent = item.bk ? (item.bk.progress_percent || 0) : 0;
                let taxProgressPercent = item.tax ? (item.tax.progress_percent || 0) : 0;

                let missingBadges = '';
                let progressCellHtml = '';

                if (isInd) {
                    missingBadges = (item.tax.missing_steps || []).map(s => `<span style="background: rgba(239,68,68,0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.3); padding: 2px 7px; border-radius: 6px; font-size: 0.72rem;">☐ ${s}</span>`).join(' ');
                    const taxPeriodLabel = (item.tax && item.tax.period_label) ? item.tax.period_label : 'Tax Year';
                    progressCellHtml = `
                        <div style="display: flex; flex-direction: column; gap: 4px; min-width: 170px;">
                            <div style="display: flex; justify-content: space-between; font-weight: 700; color: #f87171; font-size: 0.73rem;">
                                <span>📑 Tax (${taxPeriodLabel}):</span>
                                <span>${taxProgressPercent}%</span>
                            </div>
                            <div style="width: 160px; height: 6px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden;">
                                <div style="width: ${taxProgressPercent}%; height: 100%; background: linear-gradient(90deg, #f43f5e, #fb7185); border-radius: 4px;"></div>
                            </div>
                        </div>
                    `;
                } else {
                    let bkBadges = ((item.bk ? item.bk.missing_steps : []) || []).map(s => `<span style="background: rgba(56,189,248,0.15); color: #38bdf8; border: 1px solid rgba(56,189,248,0.3); padding: 2px 7px; border-radius: 6px; font-size: 0.72rem;">☐ ${s}</span>`).join(' ');
                    let taxBadges = (item.tax ? (item.tax.missing_steps || []) : []).map(s => `<span style="background: rgba(239,68,68,0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.3); padding: 2px 7px; border-radius: 6px; font-size: 0.72rem;">☐ Tax: ${s}</span>`).join(' ');
                    missingBadges = [bkBadges, taxBadges].filter(Boolean).join(' ');

                    const bkPeriodLabel = (item.bk && item.bk.period_label) ? item.bk.period_label : 'Current Period';
                    const taxPeriodLabel = (item.tax && item.tax.period_label) ? item.tax.period_label : 'Tax Year';

                    progressCellHtml = `
                        <div style="display: flex; flex-direction: column; gap: 8px; min-width: 170px;">
                            <div>
                                <div style="display: flex; justify-content: space-between; font-weight: 700; color: #38bdf8; font-size: 0.73rem; margin-bottom: 2px;">
                                    <span>📊 Bk (${bkPeriodLabel}):</span>
                                    <span>${bkProgressPercent}%</span>
                                </div>
                                <div style="width: 160px; height: 6px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden;">
                                    <div style="width: ${bkProgressPercent}%; height: 100%; background: linear-gradient(90deg, #00f2fe, #38bdf8); border-radius: 4px;"></div>
                                </div>
                            </div>
                            <div>
                                <div style="display: flex; justify-content: space-between; font-weight: 700; color: #f87171; font-size: 0.73rem; margin-bottom: 2px;">
                                    <span>📑 Tax (${taxPeriodLabel}):</span>
                                    <span>${taxProgressPercent}%</span>
                                </div>
                                <div style="width: 160px; height: 6px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden;">
                                    <div style="width: ${taxProgressPercent}%; height: 100%; background: linear-gradient(90deg, #7f00ff, #f43f5e); border-radius: 4px;"></div>
                                </div>
                            </div>
                        </div>
                    `;
                }

                return `
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.06); transition: background 0.2s ease;">
                        <td style="padding: 12px 18px; font-weight: 700; color: #fff;">
                            ${item.legal_name || item.display_name}
                            <div style="font-size: 0.75rem; color: #64748b; font-family: monospace; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-top: 3px;">
                                <span>${item.custumer_number || ''}</span>
                                ${item.assigned_user_id ? `<span style="background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.35); color: #c084fc; padding: 1px 7px; border-radius: 5px; font-size: 0.7rem; font-weight: 700; font-family: sans-serif;">👤 ${item.assigned_user_id}</span>` : ''}
                            </div>
                        </td>
                        <td style="padding: 12px 18px;">${typeBadge}</td>
                        <td style="padding: 12px 18px; display: flex; gap: 6px; flex-wrap: wrap;">${missingBadges}</td>
                        <td style="padding: 12px 18px;">${progressCellHtml}</td>
                        <td style="padding: 12px 18px; text-align: right;">
                            <button onclick="openCustomerChecklistModal(event, ${item.customer_id}, '${item.period || ''}', '${item.customer_type || ''}')" style="padding: 6px 12px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; color: #fff; font-weight: 700; font-size: 0.78rem; cursor: pointer; transition: all 0.2s ease;">
                                📋 Open Checklist
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        let activeWorkflowTab = 'bookkeeping'; // 'bookkeeping' or 'tax'

        function switchWorkflowTab(tabName) {
            activeWorkflowTab = tabName;
            const bkTabBtn = document.getElementById('tabBkWorkflow');
            const taxTabBtn = document.getElementById('tabTaxWorkflow');
            const bkSection = document.getElementById('checklistBkSection');
            const taxSection = document.getElementById('checklistTaxSection');

            if (tabName === 'tax') {
                if (taxTabBtn) {
                    taxTabBtn.style.background = 'rgba(239, 68, 68, 0.25)';
                    taxTabBtn.style.borderColor = 'rgba(239, 68, 68, 0.5)';
                    taxTabBtn.style.color = '#f87171';
                }
                if (bkTabBtn) {
                    bkTabBtn.style.background = 'rgba(255, 255, 255, 0.05)';
                    bkTabBtn.style.borderColor = 'rgba(255, 255, 255, 0.12)';
                    bkTabBtn.style.color = '#94a3b8';
                }
                if (bkSection) bkSection.style.display = 'none';
                if (taxSection) taxSection.style.display = 'flex';
                // Auto-load Tax Document Tracker when switching to tax tab
                if (currentChecklistCustomerId) {
                    loadTaxDocTracking(currentChecklistCustomerId);
                }
            } else {
                if (bkTabBtn) {
                    bkTabBtn.style.background = 'rgba(56, 189, 248, 0.25)';
                    bkTabBtn.style.borderColor = 'rgba(56, 189, 248, 0.5)';
                    bkTabBtn.style.color = '#38bdf8';
                }
                if (taxTabBtn) {
                    taxTabBtn.style.background = 'rgba(255, 255, 255, 0.05)';
                    taxTabBtn.style.borderColor = 'rgba(255, 255, 255, 0.12)';
                    taxTabBtn.style.color = '#94a3b8';
                }
                if (bkSection) bkSection.style.display = 'flex';
                if (taxSection) taxSection.style.display = 'none';
            }

            // Re-populate dropdown and reload checklist for selected mode
            populateChecklistPeriodDropdown();
            loadCustomerChecklist(null, document.getElementById('checklistPeriodSelect')?.value);
        }

        async function loadCustomerChecklist(customerId, period) {
            const cid = customerId || currentChecklistCustomerId;
            if (!cid) return;

            const selectedPeriod = period || document.getElementById('checklistPeriodSelect')?.value || '';
            try {
                const url = `/api/customers/${cid}/checklist?workflow_tab=${encodeURIComponent(activeWorkflowTab)}` + (selectedPeriod ? `&period=${encodeURIComponent(selectedPeriod)}` : '');
                const res = await fetch(url);
                const data = await res.json();

                if (!res.ok) throw new Error(data.detail || 'Failed to fetch checklist');

                if (data.customer_id) {
                    currentChecklistCustomerId = data.customer_id;
                }
                currentChecklistPeriod = data.period;

                const titleEl = document.getElementById('checklistModalTitle');
                const subtitleEl = document.getElementById('checklistModalSubtitle');

                if (titleEl) titleEl.textContent = `📋 ${data.legal_name} — Workflow Checklist`;
                if (subtitleEl) {
                    const labelText = activeWorkflowTab === 'tax' ? 'Tax Year' : 'Period Cycle';
                    const modeLabel = data.is_in_process ? `🔄 In Process (${data.in_process_label})` : `📁 Historical Archive (${data.period})`;
                    subtitleEl.textContent = `${labelText}: ${modeLabel} | Last Updated: ${data.updated_at ? new Date(data.updated_at).toLocaleString() : 'Just now'}`;
                }

                // Populate period select options dynamically
                populateChecklistPeriodDropdown(data);

                // Hide/show Reopen button if viewing historical archive
                const reopenBtn = document.getElementById('btnReopenChecklist');
                if (reopenBtn) {
                    reopenBtn.style.display = (!data.is_in_process) ? 'inline-block' : 'none';
                }

                renderChecklistUI(data);
            } catch (err) {
                alert(`❌ Checklist Error: ${err.message}`);
            }
        }

        function renderChecklistUI(data) {
            window.lastChecklistData = data;
            const progressBarEl = document.getElementById('checklistProgressBar');
            const progressTextEl = document.getElementById('checklistProgressText');

            if (activeWorkflowTab === 'tax') {
                const taxData = data.tax || {};
                const steps = taxData.steps || {};
                if (progressBarEl) progressBarEl.style.width = `${taxData.progress_percent || 0}%`;
                if (progressTextEl) progressTextEl.textContent = `${taxData.completed_count || 0} of 8 Completed (${taxData.progress_percent || 0}%)`;

                setCheckstepState('step_tax_docs_requested', steps.tax_docs_requested);
                setCheckstepState('step_tax_docs_received', steps.tax_docs_received);
                setCheckstepState('step_tax_organizer', steps.tax_organizer);
                setCheckstepState('step_tax_preparation', steps.tax_preparation);
                setCheckstepState('step_tax_review', steps.tax_review);
                setCheckstepState('step_tax_client_signature', steps.tax_client_signature);
                setCheckstepState('step_tax_efile', steps.tax_efile);
                setCheckstepState('step_tax_accepted', steps.tax_accepted);

                const taxNotesInput = document.getElementById('checklistTaxNotesInput');
                if (taxNotesInput) taxNotesInput.value = data.tax_notes || '';
            } else {
                const bkData = data.bookkeeping || data;
                const steps = bkData.steps || {};
                if (progressBarEl) progressBarEl.style.width = `${bkData.progress_percent || 0}%`;
                if (progressTextEl) progressTextEl.textContent = `${bkData.completed_count || 0} of 4 Completed (${bkData.progress_percent || 0}%)`;

                setCheckstepState('step_bank_statement_received', steps.bank_statement_received);
                setCheckstepState('step_check_images_received', steps.check_images_received);
                setCheckstepState('step_extraction_ai_categorization_done', steps.extraction_ai_categorization_done);
                setCheckstepState('step_accountant_reviewed', steps.accountant_reviewed);

                const notesInput = document.getElementById('checklistNotesInput');
                if (notesInput) notesInput.value = data.notes || '';
            }
        }

        function populateChecklistPeriodDropdown(data) {
            const select = document.getElementById('checklistPeriodSelect');
            const labelEl = document.getElementById('checklistPeriodLabel');
            if (!select) return;

            let optionsHtml = '';
            const inProcessLabel = (data && data.in_process_label) ? data.in_process_label : 'Current Period';
            const inProcessSlug = (data && data.in_process_period) ? data.in_process_period : 'in_process';
            const historical = (data && data.historical_periods) ? data.historical_periods : [];

            if (activeWorkflowTab === 'tax') {
                if (labelEl) labelEl.textContent = 'TAX YEAR:';
                optionsHtml += `<option value="${inProcessSlug}">🔄 In Process (${inProcessLabel})</option>`;
                if (historical.length > 0) {
                    optionsHtml += `<option disabled style="color: #64748b; background: #0f172a;">── Historical Completed Years ──</option>`;
                    historical.forEach(hp => {
                        const slug = typeof hp === 'object' ? hp.slug : hp;
                        const label = typeof hp === 'object' ? hp.label : `Tax Year ${hp}`;
                        optionsHtml += `<option value="${slug}">📁 ${label}</option>`;
                    });
                }
            } else {
                if (labelEl) labelEl.textContent = 'PERIOD CYCLE:';
                optionsHtml += `<option value="${inProcessSlug}">🔄 In Process (${inProcessLabel})</option>`;
                if (historical.length > 0) {
                    optionsHtml += `<option disabled style="color: #64748b; background: #0f172a;">── Historical Completed Periods ──</option>`;
                    historical.forEach(hp => {
                        const slug = typeof hp === 'object' ? hp.slug : hp;
                        const label = typeof hp === 'object' ? hp.label : `Period ${hp}`;
                        optionsHtml += `<option value="${slug}">📁 ${label}</option>`;
                    });
                }
            }

            select.innerHTML = optionsHtml;
            if (data && data.period) {
                select.value = data.period;
            }
        }

        function setCheckstepState(elemId, isChecked) {
            const chk = document.getElementById(elemId);
            const card = document.getElementById(`${elemId}_card`);
            if (chk) chk.checked = !!isChecked;
            if (card) {
                if (isChecked) {
                    card.style.background = 'rgba(0, 230, 118, 0.08)';
                    card.style.borderColor = 'rgba(0, 230, 118, 0.4)';
                } else {
                    card.style.background = 'rgba(255, 255, 255, 0.02)';
                    card.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                }
            }
        }

        async function toggleChecklistStep(stepKey, isChecked) {
            if (!currentChecklistCustomerId) return;
            const periodToUse = currentChecklistPeriod || document.getElementById('checklistPeriodSelect')?.value || 'in_process';
            try {
                const res = await fetch(`/api/customers/${currentChecklistCustomerId}/checklist/toggle`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        period: periodToUse,
                        step_key: stepKey,
                        value: isChecked,
                        workflow_mode: activeWorkflowTab
                    })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Failed to update checklist step');

                renderChecklistUI(data);
                populateChecklistPeriodDropdown(data);
                const reopenBtn = document.getElementById('btnReopenChecklist');
                if (reopenBtn) {
                    reopenBtn.style.display = (!data.is_in_process) ? 'inline-block' : 'none';
                }

                if (typeof fetchPendingWorkload === 'function') {
                    fetchPendingWorkload();
                }


                if (data.just_archived) {
                    alert(data.archived_message || '🎉 Workflow Completed & Archived!');
                    await loadCustomerChecklist(currentChecklistCustomerId, 'in_process');
                }
            } catch (err) {
                alert(`❌ Step Toggle Error: ${err.message}`);
            }
        }

        async function reopenChecklistPeriod(event) {
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

                renderChecklistUI(data);
                populateChecklistPeriodDropdown(data);
                const reopenBtn = document.getElementById('btnReopenChecklist');
                if (reopenBtn) reopenBtn.style.display = 'none';


            } catch (err) {
                alert(`❌ Reopen Error: ${err.message}`);
            }
        }

        async function saveChecklistNotes(isTax = false) {
            if (!currentChecklistCustomerId || !currentChecklistPeriod) return;
            const inputId = isTax ? 'checklistTaxNotesInput' : 'checklistNotesInput';
            const notesVal = document.getElementById(inputId)?.value || '';
            const payload = { period: currentChecklistPeriod };
            if (isTax) {
                payload.tax_notes = notesVal;
            } else {
                payload.notes = notesVal;
            }

            try {
                const res = await fetch(`/api/customers/${currentChecklistCustomerId}/checklist/toggle`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Failed to save notes');
                alert('✅ Checklist notes saved successfully!');
            } catch (err) {
                alert(`❌ Save Notes Error: ${err.message}`);
            }
        }

        // ── TAX DOCUMENT TRACKING JS ────────────────────────────────────────────

        let _taxDocCurrentYear = new Date().getFullYear() - 1;
        let _taxDocReqs = [];
        let _taxDocReceived = [];

        function switchTaxDocTab(tabName) {
            ['reqs', 'received'].forEach(t => {
                const btn = document.getElementById(`taxDocTabBtn-${t}`);
                const panel = document.getElementById(`taxDocPanel-${t}`);
                if (t === tabName) {
                    btn.style.background = 'rgba(248,113,113,0.15)';
                    btn.style.color = '#f87171';
                    btn.style.borderColor = 'rgba(248,113,113,0.4)';
                    if (panel) panel.style.display = 'block';
                } else {
                    btn.style.background = 'rgba(255,255,255,0.03)';
                    btn.style.color = '#64748b';
                    btn.style.borderColor = 'rgba(255,255,255,0.08)';
                    if (panel) panel.style.display = 'none';
                }
            });
        }

        function _taxDocStatusBadgeHtml(status) {
            if (status === 'Completed') return `<span id="taxDocStatusBadge" style="font-size:0.7rem;padding:3px 12px;border-radius:20px;font-weight:800;background:rgba(0,230,118,0.15);color:#00e676;border:1px solid rgba(0,230,118,0.3);">✅ COMPLETED</span>`;
            if (status === 'Needs Review') return `<span id="taxDocStatusBadge" style="font-size:0.7rem;padding:3px 12px;border-radius:20px;font-weight:800;background:rgba(250,204,21,0.15);color:#facc15;border:1px solid rgba(250,204,21,0.3);">🔍 NEEDS REVIEW</span>`;
            return `<span id="taxDocStatusBadge" style="font-size:0.7rem;padding:3px 12px;border-radius:20px;font-weight:800;background:rgba(248,113,113,0.15);color:#f87171;border:1px solid rgba(248,113,113,0.3);">⚠️ INCOMPLETE</span>`;
        }

        function populateTaxDocYearSelect() {
            const yearSel = document.getElementById('taxDocYearSelect');
            if (!yearSel) return;
            const currentYear = new Date().getFullYear();
            const years = [];
            // Dynamically generates current year (e.g. Tax Year 2026) and past 5 years
            for (let y = currentYear; y >= currentYear - 5; y--) {
                years.push(y);
            }
            if (!years.includes(_taxDocCurrentYear)) _taxDocCurrentYear = currentYear - 1;
            yearSel.innerHTML = years.map(y => `<option value="${y}" ${y === _taxDocCurrentYear ? 'selected' : ''}>Tax Year ${y}</option>`).join('');
        }

        function onTaxDocYearChange(newYear) {
            _taxDocCurrentYear = parseInt(newYear);
            if (currentChecklistCustomerId) {
                loadTaxDocTracking(currentChecklistCustomerId);
            }
        }

        async function loadTaxDocTracking(customerId) {
            if (!customerId) return;
            populateTaxDocYearSelect();
            try {
                // Load requirements + received status in parallel
                const [reqRes, statusRes] = await Promise.all([
                    fetch(`/api/tax-requirements/${customerId}?tax_year=${_taxDocCurrentYear}`),
                    fetch(`/api/tax-docs-status/${customerId}?tax_year=${_taxDocCurrentYear}`)
                ]);
                const reqData = await reqRes.json();
                const statusData = await statusRes.json();
                _taxDocReqs = reqData.requirements || [];
                _taxDocReceived = statusData.received_docs || [];

                // Update status badge
                const badgeEl = document.getElementById('taxDocStatusBadge');
                if (badgeEl) {
                    const st = statusData.status || 'Incomplete';
                    const rcv = statusData.total_received || 0;
                    const tot = statusData.total_required || 0;
                    const nr = statusData.needs_review || 0;
                    let badgeText = st === 'Completed' ? '✅ COMPLETED' : (st === 'Needs Review' ? `🔍 NEEDS REVIEW (${nr})` : `⚠️ INCOMPLETE (${rcv}/${tot})`);
                    let badgeColor = st === 'Completed' ? '#00e676' : (st === 'Needs Review' ? '#facc15' : '#f87171');
                    let badgeBg = st === 'Completed' ? 'rgba(0,230,118,0.15)' : (st === 'Needs Review' ? 'rgba(250,204,21,0.15)' : 'rgba(248,113,113,0.15)');
                    let badgeBorder = st === 'Completed' ? 'rgba(0,230,118,0.3)' : (st === 'Needs Review' ? 'rgba(250,204,21,0.3)' : 'rgba(248,113,113,0.3)');
                    badgeEl.textContent = badgeText;
                    badgeEl.style.color = badgeColor;
                    badgeEl.style.background = badgeBg;
                    badgeEl.style.border = `1px solid ${badgeBorder}`;
                }

                // Update email sent label
                const emailLabel = document.getElementById('taxDocEmailSentLabel');
                if (emailLabel) {
                    const sentAt = statusData.req_email_sent_at;
                    emailLabel.textContent = sentAt ? `📧 Email sent: ${new Date(sentAt).toLocaleString()}` : '📧 Email not sent yet';
                }

                renderTaxReqTable();
                renderTaxRecTable();
            } catch (err) {
                console.error('[TAX DOC TRACKING] Load error:', err);
            }
        }

        function renderTaxReqTable() {
            const tbody = document.getElementById('taxReqTableBody');
            if (!tbody) return;
            if (!_taxDocReqs.length) {
                tbody.innerHTML = `<tr><td colspan="5" style="padding:16px;text-align:center;color:#475569;font-size:0.82rem;">No requirements defined yet. Click "+ Add Document" to start.</td></tr>`;
                return;
            }
            tbody.innerHTML = _taxDocReqs.map(r => {
                const received = r.received_status === 'Matched' || r.received_status === 'Received';
                const needsReview = r.received_status === 'Needs Review';
                let statusBadge = `<span style="font-size:0.68rem;padding:2px 8px;border-radius:12px;font-weight:800;background:rgba(148,163,184,0.12);color:#94a3b8;border:1px solid rgba(148,163,184,0.25);">Pending</span>`;
                if (received) statusBadge = `<span style="font-size:0.68rem;padding:2px 8px;border-radius:12px;font-weight:800;background:rgba(0,230,118,0.12);color:#00e676;border:1px solid rgba(0,230,118,0.25);">✅ Received</span>`;
                if (needsReview) statusBadge = `<span style="font-size:0.68rem;padding:2px 8px;border-radius:12px;font-weight:800;background:rgba(250,204,21,0.12);color:#facc15;border:1px solid rgba(250,204,21,0.25);">🔍 Review</span>`;
                const labelText = r.doc_label || '';
                const sourceText = r.source_description ? ` (${r.source_description})` : '';
                const isChecked = r.received_status === 'Matched' || r.received_status === 'Received';
                return `<tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
                    <td style="padding:8px;color:#f8fafc;font-weight:700;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${r.doc_type}</td>
                    <td style="padding:8px;color:#94a3b8;font-size:0.8rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${labelText}${sourceText}">${labelText}${sourceText ? `<em style="color:#64748b;">${sourceText}</em>` : ''}</td>
                    <td style="padding:8px; text-align:center;">
                        <input type="checkbox" onchange="updateTaxRequirementManualStatus(${r.id}, this.checked)" ${isChecked ? 'checked' : ''} style="width:16px;height:16px;accent-color:#00e676;cursor:pointer;">
                    </td>
                    <td style="padding:8px;">${statusBadge}</td>
                    <td style="padding:8px;text-align:right;white-space:nowrap;">
                        <button type="button" onclick="deleteTaxRequirement(${r.id}); event.stopPropagation();" title="Delete requirement" style="padding:4px 10px;background:rgba(248,113,113,0.2);border:1px solid rgba(248,113,113,0.4);color:#f87171;border-radius:6px;font-size:0.75rem;font-weight:700;cursor:pointer;display:inline-flex;align-items:center;gap:4px;">🗑 Delete</button>
                    </td>
                </tr>`;
            }).join('');
        }

        function renderTaxRecTable() {
            const tbody = document.getElementById('taxRecTableBody');
            if (!tbody) return;
            if (!_taxDocReceived.length) {
                tbody.innerHTML = `<tr><td colspan="6" style="padding:16px;text-align:center;color:#475569;font-size:0.82rem;">No documents received or classified yet. Click "Scan & Classify Inbox Docs" to load uploaded files.</td></tr>`;
                return;
            }
            tbody.innerHTML = _taxDocReceived.map(d => {
                let stBadge = `<span style="font-size:0.68rem;padding:2px 8px;border-radius:12px;font-weight:800;background:rgba(148,163,184,0.12);color:#94a3b8;">Received</span>`;
                if (d.status === 'Matched') stBadge = `<span style="font-size:0.68rem;padding:2px 8px;border-radius:12px;font-weight:800;background:rgba(0,230,118,0.12);color:#00e676;border:1px solid rgba(0,230,118,0.25);">✅ Matched</span>`;
                if (d.status === 'Needs Review') stBadge = `<span style="font-size:0.68rem;padding:2px 8px;border-radius:12px;font-weight:800;background:rgba(250,204,21,0.12);color:#facc15;border:1px solid rgba(250,204,21,0.25);">🔍 Review</span>`;
                const conf = d.ocr_confidence ? `${Math.round(d.ocr_confidence * 100)}%` : '—';
                const fileKey = d.file_key || '';
                const origName = d.original_filename || '—';
                const renName = d.renamed_filename || '—';
                return `<tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
                    <td style="padding:8px;color:#94a3b8;font-size:0.78rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${origName}">${origName}</td>
                    <td style="padding:8px;color:#f8fafc;font-weight:700;font-size:0.78rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${renName}">${renName}</td>
                    <td style="padding:8px;color:#38bdf8;font-weight:700;font-size:0.78rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${d.doc_type_detected || '—'}</td>
                    <td style="padding:8px;color:#94a3b8;font-size:0.78rem;">${conf}</td>
                    <td style="padding:8px;">${stBadge}</td>
                    <td style="padding:8px;text-align:right;white-space:nowrap;">
                        <button type="button" onclick="reClassifyTaxDoc('${fileKey.replace(/'/g, "\\'")}', '${origName.replace(/'/g, "\\'")}'); event.stopPropagation();" title="Re-classify document" style="padding:4px 7px;background:rgba(56,189,248,0.15);border:1px solid rgba(56,189,248,0.35);color:#38bdf8;border-radius:6px;font-size:0.72rem;font-weight:700;cursor:pointer;margin-right:4px;">🔄 Retry</button>
                        <button type="button" onclick="deleteReceivedTaxDoc(${d.id}); event.stopPropagation();" title="Delete received document record" style="padding:4px 7px;background:rgba(248,113,113,0.2);border:1px solid rgba(248,113,113,0.4);color:#f87171;border-radius:6px;font-size:0.72rem;font-weight:700;cursor:pointer;">🗑 Delete</button>
                    </td>
                </tr>`;
            }).join('');
        }

        async function sendTaxRequirementsEmail() {
            if (!currentChecklistCustomerId) return;
            let confirmSend = true;
            if (typeof showCustomConfirm === 'function') {
                confirmSend = await showCustomConfirm(
                    `Are you sure you want to send the tax document requirements email to this customer for tax year ${_taxDocCurrentYear}?`,
                    'Send Tax Requirements Email',
                    '📧 Yes, Send Email',
                    'Cancel'
                );
            } else if (!confirm(`Send tax document requirements email to this customer for tax year ${_taxDocCurrentYear}?`)) {
                return;
            }
            if (!confirmSend) return;

            const btn = document.getElementById('btnSendTaxEmail');
            if (btn) { btn.disabled = true; btn.textContent = '⏳ Sending…'; }
            try {
                const res = await fetch('/api/tax-requirements/send-email', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ customer_id: currentChecklistCustomerId, tax_year: _taxDocCurrentYear })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || data.message || 'Send failed');

                if (data.sent_count > 0 || data.success) {
                    let alertMsg = data.message || `Tax requirements email successfully sent for tax year ${_taxDocCurrentYear}!`;
                    if (data.errors && data.errors.length > 0) {
                        alertMsg += `\n\nWarnings:\n` + data.errors.join('\n');
                    }
                    if (typeof showCustomAlert === 'function') {
                        showCustomAlert('Email Sent Successfully', alertMsg, 'success');
                    } else {
                        alert(`✅ ${alertMsg}`);
                    }
                } else {
                    let errorDetails = (data.errors && data.errors.length > 0) ? data.errors.join('\n') : (data.message || 'Send failed');
                    if (typeof showCustomAlert === 'function') {
                        showCustomAlert('Email Not Sent', errorDetails, 'error');
                    } else {
                        alert(`❌ ${errorDetails}`);
                    }
                }
                await loadTaxDocTracking(currentChecklistCustomerId);
            } catch (err) {
                if (typeof showCustomAlert === 'function') {
                    showCustomAlert('Error Sending Email', err.message || 'An unexpected error occurred while sending email.', 'error');
                } else {
                    alert(`❌ Error: ${err.message}`);
                }
            } finally {
                if (btn) { btn.disabled = false; btn.innerHTML = '📧 Send Requirements Email'; }
            }
        }

        async function copyTaxRequirementsFromYear() {
            if (!currentChecklistCustomerId) return;
            const fromYear = _taxDocCurrentYear - 1;
            let confirmCopy = true;
            if (typeof showCustomConfirm === 'function') {
                confirmCopy = await showCustomConfirm(
                    `Copy all tax document requirements from Tax Year ${fromYear} to Tax Year ${_taxDocCurrentYear}?`,
                    'Copy Last Year Requirements',
                    '📋 Yes, Copy Requirements',
                    'Cancel'
                );
            } else if (!confirm(`Copy all requirements from tax year ${fromYear} to ${_taxDocCurrentYear}?`)) {
                return;
            }
            if (!confirmCopy) return;

            try {
                const res = await fetch('/api/tax-requirements/copy-from-year', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ customer_id: currentChecklistCustomerId, from_year: fromYear, to_year: _taxDocCurrentYear })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || data.message || 'Copy failed');

                if (data.copied_count > 0) {
                    if (typeof showCustomAlert === 'function') {
                        showCustomAlert('Copy Successful', `Successfully copied ${data.copied_count} requirement(s) from Tax Year ${fromYear} to Tax Year ${_taxDocCurrentYear}!`, 'success');
                    } else {
                        alert(`✅ Copied ${data.copied_count} requirement(s) from ${fromYear} → ${_taxDocCurrentYear}`);
                    }
                } else if (data.from_count === 0) {
                    if (typeof showCustomAlert === 'function') {
                        showCustomAlert('No Requirements Found', `Tax Year ${fromYear} has no tax document requirements defined yet to copy from.`, 'info');
                    } else {
                        alert(`ℹ️ Tax Year ${fromYear} has no requirements defined.`);
                    }
                } else {
                    if (typeof showCustomAlert === 'function') {
                        showCustomAlert('Already Copied', `All ${data.from_count || data.existing_count} requirement(s) from Tax Year ${fromYear} are already present in Tax Year ${_taxDocCurrentYear}.`, 'info');
                    } else {
                        alert(`ℹ️ All requirements from ${fromYear} are already present in ${_taxDocCurrentYear}.`);
                    }
                }
                await loadTaxDocTracking(currentChecklistCustomerId);
            } catch (err) {
                if (typeof showCustomAlert === 'function') {
                    showCustomAlert('Error Copying Requirements', err.message || 'Failed to copy requirements.', 'error');
                } else {
                    alert(`❌ Error: ${err.message}`);
                }
            }
        }

        async function deleteTaxRequirement(reqId) {
            if (!reqId) return;
            // Instant optimistic UI removal
            _taxDocReqs = _taxDocReqs.filter(r => r.id != reqId);
            renderTaxReqTable();
            try {
                const res = await fetch('/api/tax-requirements/' + reqId, {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include'
                });
                let data = {};
                try { data = await res.json(); } catch(_) {}
                if (!res.ok) throw new Error(data.detail || `Server error ${res.status}`);
                await loadTaxDocTracking(currentChecklistCustomerId);
            } catch (err) {
                console.error('[TAX DELETE]', err);
                alert(`❌ Delete failed: ${err.message}`);
                await loadTaxDocTracking(currentChecklistCustomerId);
            }
        }

        async function updateTaxRequirementManualStatus(reqId, isChecked) {
            if (!reqId) return;
            const req = _taxDocReqs.find(r => r.id === reqId);
            if (!req) return;
            
            req.manual_status = isChecked ? 'Received' : 'Pending';
            req.received_status = req.manual_status; // Optimistic UI update
            renderTaxReqTable();
            
            const payload = isChecked ? { manual_status: 'Received' } : { clear_received: true };
            
            try {
                const res = await fetch('/api/tax-requirements/' + reqId, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify(payload)
                });
                if (!res.ok) {
                    const data = await res.json();
                    throw new Error(data.detail || `Server error ${res.status}`);
                }
                await loadTaxDocTracking(currentChecklistCustomerId);
            } catch (err) {
                console.error('[TAX UPDATE STATUS]', err);
                alert(`❌ Update failed: ${err.message}`);
                await loadTaxDocTracking(currentChecklistCustomerId);
            }
        }

        async function deleteReceivedTaxDoc(docId) {
            if (!docId) return;
            // Instant optimistic UI removal
            _taxDocReceived = _taxDocReceived.filter(d => d.id != docId);
            renderTaxRecTable();
            try {
                const res = await fetch('/api/tax-docs/received/' + docId, {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include'
                });
                let data = {};
                try { data = await res.json(); } catch(_) {}
                if (!res.ok) throw new Error(data.detail || `Server error ${res.status}`);
                await loadTaxDocTracking(currentChecklistCustomerId);
            } catch (err) {
                console.error('[TAX REC DELETE]', err);
                alert(`❌ Delete failed: ${err.message}`);
                await loadTaxDocTracking(currentChecklistCustomerId);
            }
        }

        async function reClassifyTaxDoc(fileKey, originalFilename) {
            if (!fileKey || !currentChecklistCustomerId) return;
            if (!confirm(`Re-classify document "${originalFilename || fileKey}"?`)) return;
            try {
                const res = await fetch('/api/tax-docs/classify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        customer_id: currentChecklistCustomerId,
                        file_key: fileKey,
                        original_filename: originalFilename,
                        tax_year: _taxDocCurrentYear
                    })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Classify failed');
                alert(`✅ ${data.message} — OCR processing started.`);
                [1000, 3500, 7000].forEach(delay => {
                    setTimeout(() => loadTaxDocTracking(currentChecklistCustomerId), delay);
                });
            } catch (err) {
                alert(`❌ Error: ${err.message}`);
            }
        }

        const TAX_DOC_TYPES = ['W2','1099-NEC','1099-MISC','1099-INT','1099-DIV','1099-R','1099-G','SSA-1099','1098','1098-T','1098-E','1099-B','1095-A','1095-B','1095-C','K-1','PRIOR-RETURN','OTHER'];

        function openAddTaxRequirementModal() {
            const docType = prompt(
                `Enter document type for tax year ${_taxDocCurrentYear}:\n\nOptions: ${TAX_DOC_TYPES.join(', ')}\n\nType a value (or any custom type):`,
                'W2'
            );
            if (!docType) return;
            const label = prompt('Optional: Enter a label/description (e.g. "Employer W2 from Amazon")', '');
            const source = prompt('Optional: Source description (e.g. "Amazon", "Chase Bank")', '');
            addTaxRequirement(docType.toUpperCase(), label || '', source || '');
        }

        async function addTaxRequirement(docType, docLabel, sourceDescription) {
            if (!currentChecklistCustomerId || !docType) return;
            try {
                const res = await fetch('/api/tax-requirements', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        customer_id: currentChecklistCustomerId,
                        tax_year: _taxDocCurrentYear,
                        doc_type: docType,
                        doc_label: docLabel || null,
                        source_description: sourceDescription || null,
                        is_required: true
                    })
                });
                let data = {};
                try { data = await res.json(); } catch(_) {}
                if (!res.ok) throw new Error(data.detail || `Server error ${res.status}`);
                await loadTaxDocTracking(currentChecklistCustomerId);
            } catch (err) {
                console.error('[TAX ADD REQ]', err);
                alert(`❌ Error adding requirement: ${err.message}`);
            }
        }

        async function scanExistingTaxDocs() {
            if (!currentChecklistCustomerId) return;
            const btn = document.getElementById('btnScanInboxDocs');
            if (btn) { btn.disabled = true; btn.textContent = '🔍 Scanning Inbox…'; }
            try {
                const res = await fetch('/api/tax-docs/scan-existing', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ customer_id: currentChecklistCustomerId })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Scan failed');
                alert(`✅ ${data.message} — OCR classification results will appear shortly.`);
                setTimeout(() => loadTaxDocTracking(currentChecklistCustomerId), 4000);
            } catch (err) {
                alert(`❌ Error scanning docs: ${err.message}`);
            } finally {
                if (btn) { btn.disabled = false; btn.textContent = '🔍 Scan & Classify Inbox Docs'; }
            }
        }

        async function clearAllReceivedTaxDocs() {
            if (!currentChecklistCustomerId) return;
            if (!confirm(`Are you sure you want to remove ALL received document records for tax year ${_taxDocCurrentYear}?`)) return;
            const btn = document.getElementById('btnClearAllRecDocs');
            if (btn) { btn.disabled = true; btn.textContent = '⏳ Clearing…'; }
            try {
                _taxDocReceived = [];
                renderTaxRecTable();

                const res = await fetch(`/api/tax-docs/received-all/${currentChecklistCustomerId}?tax_year=${_taxDocCurrentYear}`, {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include'
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Clear failed');
                await loadTaxDocTracking(currentChecklistCustomerId);
            } catch (err) {
                alert(`❌ Error: ${err.message}`);
                await loadTaxDocTracking(currentChecklistCustomerId);
            } finally {
                if (btn) { btn.disabled = false; btn.textContent = '🗑 Clear All Received'; }
            }
        }

        async function sendTaxBulkEmail() {
            const taxYear = new Date().getFullYear() - 1;
            if (!confirm(`Send tax document requirements email to ALL Individual & Joint Account customers for tax year ${taxYear}?\n\nThis will send one email per customer and log the sent timestamp.`)) return;
            const btn1 = document.getElementById('btnBulkTaxEmail');
            const btn2 = document.getElementById('btnBulkTaxEmailPage');
            [btn1, btn2].forEach(b => { if (b) { b.disabled = true; b.textContent = '⏳ Sending…'; } });
            try {
                const res = await fetch('/api/tax-requirements/send-email', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ tax_year: taxYear })   // no customer_id = send to all
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Bulk send failed');
                let msg = `✅ ${data.message}`;
                if (data.errors && data.errors.length) {
                    msg += `\n\nWarnings:\n${data.errors.join('\n')}`;
                }
                alert(msg);
            } catch (err) {
                console.error('[TAX BULK EMAIL]', err);
                alert(`❌ Bulk Email Error: ${err.message}`);
            } finally {
                [btn1, btn2].forEach(b => { if (b) { b.disabled = false; b.innerHTML = '📧 Bulk Tax Email'; } });
            }
        }



        // --- Global Keyboard & Backdrop Event Delegation for All Modals ---
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                const pdfModal = document.getElementById('pdfViewerModal');
                if (pdfModal && pdfModal.style.display !== 'none') {
                    closePdfViewerModal();
                    return;
                }
                const storageModal = document.getElementById('customerStorageModal');
                if (storageModal && storageModal.style.display !== 'none') {
                    closeCustomerStorageModal();
                    return;
                }
                closeAllAppModals();
            }
        });

        document.addEventListener('click', function(e) {
            const allModalIds = [
                'pdfViewerModal', 'customerStorageModal', 'customerChecklistModal',
                'customerModal', 'coaModal', 'mappingsModal', 'historyModal',
                'supportModal', 'sendCustomerEmailModal', 'customerCommsHistoryModal',
                'esignatureModal', 'verifyIdentityModal', 'esignatureViewModal'
            ];
            allModalIds.forEach(id => {
                const modal = document.getElementById(id);
                if (modal && modal.style.display !== 'none' && e.target === modal) {
                    if (id === 'pdfViewerModal') closePdfViewerModal();
                    else if (id === 'customerStorageModal') closeCustomerStorageModal();
                    else if (id === 'customerChecklistModal') closeCustomerChecklistModal();
                    else if (id === 'customerModal') closeCustomerModal();
                    else if (id === 'coaModal') closeCoaModal();
                    else if (id === 'mappingsModal') closeMappingsModal();
                    else if (id === 'historyModal') closeHistoryModal();
                    else if (id === 'supportModal') closeSupportModal();
                    else if (id === 'esignatureModal') closeCreateEsignatureModal();
                    else if (id === 'verifyIdentityModal') closeVerifyIdentityModal();
                    else if (id === 'esignatureViewModal') closeEsignatureViewModal();
                    else {
                        modal.style.display = 'none';
                        modal.style.opacity = '0';
                    }
                }
            });
        });

        // --- Move customerStorageModal, pdfViewerModal & customerChecklistModal to body root ---
        (function() {
            const storageModalHtml = `
<div id="customerStorageModal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.88); z-index: 2147483647; align-items: center; justify-content: center; padding: 20px;">
    <div style="background: #121624; border: 1px solid rgba(255,255,255,0.12); border-radius: 20px; width: 100%; max-width: 920px; max-height: 88vh; display: flex; flex-direction: column; box-shadow: 0 25px 60px rgba(0,0,0,0.8); overflow: hidden;">
        <div style="padding: 20px 24px; border-bottom: 1px solid rgba(255,255,255,0.08); display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.02);">
            <div>
                <h3 id="storageModalTitle" style="font-size: 1.2rem; font-weight: 800; color: #fff; display: flex; align-items: center; gap: 8px; font-family: 'Outfit', sans-serif;">📂 Customer Storage Manager</h3>
                <p id="storageModalSubtitle" style="font-size: 0.72rem; color: #94a3b8; margin-top: 4px; font-family: monospace;"></p>
            </div>
            <button onclick="closeCustomerStorageModal()" style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); color: #cbd5e1; width: 34px; height: 34px; border-radius: 10px; font-size: 1.1rem; cursor: pointer; display: flex; align-items: center; justify-content: center;">✕</button>
        </div>
        <div style="padding: 14px 24px; border-bottom: 1px solid rgba(255,255,255,0.06); background: rgba(0,0,0,0.25); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
            <div id="storageBreadcrumbs" style="display: flex; align-items: center; gap: 6px; font-size: 0.8rem; font-family: monospace; color: #cbd5e1; flex-wrap: wrap;"></div>
            <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                <input type="file" id="storageFileInput" multiple style="display: none;" onchange="handleStorageFileUpload(event)">
                <button onclick="document.getElementById('storageFileInput').click()" style="padding: 7px 16px; background: linear-gradient(135deg, #00e676, #00b0ff); border: none; color: #000; font-weight: 800; border-radius: 8px; font-size: 0.76rem; text-transform: uppercase; cursor: pointer;">📤 Upload Files</button>
                <button onclick="createStorageFolder()" style="padding: 7px 14px; background: rgba(250,204,21,0.15); border: 1px solid rgba(250,204,21,0.4); color: #facc15; font-weight: 700; border-radius: 8px; font-size: 0.76rem; text-transform: uppercase; cursor: pointer;" title="Create a new subfolder in the current directory">📁 New Folder</button>
                <button id="storageMergePdfBtn" onclick="mergeSelectedStorageImagesToPdf()" style="display: none; padding: 7px 14px; background: linear-gradient(135deg, #a855f7, #ec4899); border: none; color: #fff; font-weight: 800; border-radius: 8px; font-size: 0.76rem; text-transform: uppercase; cursor: pointer;" title="Merge checked image files into 1 PDF document">📑 Merge Selected (0) -> PDF</button>
                <button id="storageBatchMoveBtn" onclick="moveSelectedStorageFiles()" style="display: none; padding: 7px 14px; background: linear-gradient(135deg, #f59e0b, #d97706); border: none; color: #fff; font-weight: 800; border-radius: 8px; font-size: 0.76rem; text-transform: uppercase; cursor: pointer;" title="Move selected files to another directory">🚚 Move Selected (0)</button>
                <button id="storageBatchConvertBtn" onclick="batchConvertInboxToPdf()" style="padding: 7px 14px; background: rgba(168, 85, 247, 0.2); border: 1px solid rgba(168, 85, 247, 0.45); color: #c084fc; font-weight: 700; border-radius: 8px; font-size: 0.76rem; text-transform: uppercase; cursor: pointer;" title="Convert all non-PDF files in this directory to PDF">📄 Convert Inbox to PDF</button>
                <button onclick="reinitStorageFromModal()" style="padding: 7px 14px; background: rgba(56,189,248,0.15); border: 1px solid rgba(56,189,248,0.35); color: #38bdf8; font-weight: 700; border-radius: 8px; font-size: 0.76rem; text-transform: uppercase; cursor: pointer;">⚡ Re-Init Folders</button>
                <button onclick="refreshCurrentStorageFolder()" style="padding: 7px 14px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.12); color: #fff; font-weight: 700; border-radius: 8px; font-size: 0.76rem; text-transform: uppercase; cursor: pointer;">🔄 Refresh</button>
            </div>
        </div>
        <div style="padding: 10px 24px; border-bottom: 1px solid rgba(255,255,255,0.05); background: rgba(0,0,0,0.15);">
            <input type="text" id="storageFileSearchInput" placeholder="🔍 Search current folder..." oninput="filterStorageItems()" style="width: 100%; padding: 8px 14px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: #fff; font-size: 0.82rem; outline: none;">
        </div>
        <div style="flex: 1; overflow-y: auto; padding: 16px 24px; min-height: 250px;">
            <div id="storageLoadingSpinner" style="text-align: center; padding: 50px; color: #94a3b8; display: none;"><div style="font-size: 1.8rem; margin-bottom: 10px;">⏳</div>Loading customer files...</div>
            <table style="width: 100%; border-collapse: collapse; font-size: 0.82rem;">
                <thead>
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.1); text-align: left; color: #94a3b8; font-size: 0.72rem; text-transform: uppercase;">
                        <th style="padding: 10px 12px; display: flex; align-items: center; gap: 8px;"><input type="checkbox" id="storageSelectAllChk" onchange="toggleStorageSelectAll(this)" style="cursor: pointer; accent-color: #38bdf8; width: 15px; height: 15px;" title="Select all items"> Name</th>
                        <th style="padding: 10px 12px; width: 120px;">Size</th>
                        <th style="padding: 10px 12px; width: 180px;">Last Modified</th>
                        <th style="padding: 10px 12px; width: 220px; text-align: right;">Actions</th>
                    </tr>
                </thead>
                <tbody id="storageFilesTbody"></tbody>
            </table>
        </div>
        <div style="padding: 12px 24px; border-top: 1px solid rgba(255,255,255,0.08); background: rgba(0,0,0,0.25); display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; color: #64748b;">
            <span id="storageFileStats">0 items</span>
            <span>Storage Container: <strong style="color: #38bdf8;">datalazocrm</strong></span>
        </div>
    </div>
</div>`;

            const pdfViewerModalHtml = `
<div id="pdfViewerModal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.92); z-index: 2147483648; align-items: center; justify-content: center; padding: 16px;">
    <div style="background: #0f172a; border: 1px solid rgba(255,255,255,0.15); border-radius: 16px; width: 100%; max-width: 1100px; height: 92vh; display: flex; flex-direction: column; box-shadow: 0 25px 60px rgba(0,0,0,0.9); overflow: hidden;">
        <div style="padding: 14px 20px; border-bottom: 1px solid rgba(255,255,255,0.08); display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.03);">
            <div style="display: flex; align-items: center; gap: 10px; min-width: 0;">
                <span style="font-size: 1.3rem;">📄</span>
                <h3 id="pdfViewerTitle" style="font-size: 1.05rem; font-weight: 700; color: #f8fafc; font-family: 'Outfit', sans-serif; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin: 0;">PDF Document Viewer</h3>
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <a id="pdfViewerExternalBtn" href="#" target="_blank" style="padding: 5px 12px; background: rgba(56,189,248,0.15); border: 1px solid rgba(56,189,248,0.35); color: #38bdf8; border-radius: 6px; font-size: 0.75rem; font-weight: 700; text-decoration: none;" title="Open in full browser tab">↗ New Tab</a>
                <a id="pdfViewerDownloadBtn" href="#" download style="padding: 5px 12px; background: rgba(0,230,118,0.15); border: 1px solid rgba(0,230,118,0.35); color: #00e676; border-radius: 6px; font-size: 0.75rem; font-weight: 700; text-decoration: none;" title="Download PDF file">📥 Download</a>
                <button onclick="closePdfViewerModal()" style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); color: #cbd5e1; width: 32px; height: 32px; border-radius: 8px; font-size: 1.1rem; cursor: pointer; display: flex; align-items: center; justify-content: center;" title="Close Preview">✕</button>
            </div>
        </div>
        <div style="flex: 1; position: relative; background: #020617; display: flex; align-items: center; justify-content: center;">
            <iframe id="pdfViewerIframe" src="" style="width: 100%; height: 100%; border: none; background: #020617;"></iframe>
        </div>
    </div>
</div>`;

            const customerChecklistModalHtml = `
<div id="customerChecklistModal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.88); z-index: 2147483647; align-items: center; justify-content: center; padding: 20px;">
    <div style="background: #121624; border: 1px solid rgba(255,255,255,0.14); border-radius: 20px; width: 100%; max-width: 820px; max-height: 92vh; display: flex; flex-direction: column; box-shadow: 0 25px 60px rgba(0,0,0,0.9); overflow: hidden;">
        <div style="padding: 18px 24px; border-bottom: 1px solid rgba(255,255,255,0.08); display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.02);">
            <div>
                <h3 id="checklistModalTitle" style="font-size: 1.2rem; font-weight: 800; color: #fff; display: flex; align-items: center; gap: 8px; font-family: 'Outfit', sans-serif;">📋 Customer Workflow Checklist</h3>
                <p id="checklistModalSubtitle" style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px; font-family: monospace;"></p>
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <button onclick="openSendCustomerEmailModal(event, currentChecklistCustomerId)" style="padding: 6px 14px; background: rgba(56, 189, 248, 0.18); border: 1px solid rgba(56, 189, 248, 0.45); color: #38bdf8; font-weight: 700; border-radius: 8px; font-size: 0.78rem; cursor: pointer; display: flex; align-items: center; gap: 6px; box-shadow: 0 0 10px rgba(56, 189, 248, 0.2);" title="Send Email Message to Customer">📧 Send Email</button>
                <button onclick="closeCustomerChecklistModal()" style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); color: #cbd5e1; width: 34px; height: 34px; border-radius: 10px; font-size: 1.1rem; cursor: pointer; display: flex; align-items: center; justify-content: center;">✕</button>
            </div>
        </div>

        <div style="padding: 10px 24px; border-bottom: 1px solid rgba(255,255,255,0.06); background: rgba(0,0,0,0.15); display: flex; gap: 10px; align-items: center;">
            <button id="tabBkWorkflow" onclick="switchWorkflowTab('bookkeeping')" style="padding: 7px 16px; background: rgba(56, 189, 248, 0.25); border: 1px solid rgba(56, 189, 248, 0.5); color: #38bdf8; font-weight: 700; border-radius: 8px; font-size: 0.78rem; cursor: pointer; display: flex; align-items: center; gap: 6px;">📊 Bookkeeping Workflow (4 Steps)</button>
            <button id="tabTaxWorkflow" onclick="switchWorkflowTab('tax')" style="padding: 7px 16px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.12); color: #94a3b8; font-weight: 700; border-radius: 8px; font-size: 0.78rem; cursor: pointer; display: flex; align-items: center; gap: 6px;">📑 Tax Preparation Workflow (8 Steps)</button>
        </div>
        
        <div style="padding: 14px 24px; border-bottom: 1px solid rgba(255,255,255,0.06); background: rgba(0,0,0,0.2); display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <label id="checklistPeriodLabel" style="font-size: 0.8rem; font-weight: 700; color: #cbd5e1; font-family: monospace;">PERIOD CYCLE:</label>
                <select id="checklistPeriodSelect" onchange="loadCustomerChecklist(null, this.value)" style="padding: 6px 12px; background: #0f172a; border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; color: #38bdf8; font-weight: 700; font-size: 0.82rem; outline: none; cursor: pointer;">
                    <option value="in_process">🔄 In Process</option>
                </select>
                <button type="button" id="btnReopenChecklist" onclick="reopenChecklistPeriod(event)" style="display: none; padding: 5px 12px; background: rgba(250,204,21,0.15); border: 1px solid rgba(250,204,21,0.4); color: #facc15; border-radius: 8px; font-size: 0.76rem; font-weight: 700; cursor: pointer; transition: all 0.2s;" title="Re-open this period as In Process to make corrections">↩️ Re-open Period</button>
            </div>
            <div style="flex: 1; max-width: 320px;">
                <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #94a3b8; margin-bottom: 4px; font-family: monospace;">
                    <span>WORKFLOW PROGRESS</span>
                    <strong id="checklistProgressText" style="color: #00e676;">0 Completed (0%)</strong>
                </div>
                <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.08); border-radius: 4px; overflow: hidden;">
                    <div id="checklistProgressBar" style="width: 0%; height: 100%; background: linear-gradient(90deg, #00e676, #38bdf8); transition: width 0.3s ease;"></div>
                </div>
            </div>
        </div>

        <div style="flex: 1; overflow-y: auto; padding: 20px 24px;">
            <!-- Bookkeeping Section -->
            <div id="checklistBkSection" style="display: flex; flex-direction: column; gap: 12px;">
                <!-- Step 1 -->
                <div id="step_bank_statement_received_card" style="padding: 14px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); display: flex; align-items: center; justify-content: space-between; transition: all 0.2s;">
                    <div style="display: flex; align-items: center; gap: 14px;">
                        <input type="checkbox" id="step_bank_statement_received" onchange="toggleChecklistStep('bank_statement_received', this.checked)" style="width: 18px; height: 18px; accent-color: #00e676; cursor: pointer;">
                        <div>
                            <h4 style="font-size: 0.95rem; font-weight: 700; color: #f8fafc; margin: 0;">1. Bank Statement Received</h4>
                            <p style="font-size: 0.73rem; color: #94a3b8; margin: 2px 0 0 0;">Statement PDF uploaded to storage or loaded into bank extractor</p>
                        </div>
                    </div>
                    <span style="font-size: 0.72rem; padding: 3px 10px; border-radius: 20px; font-weight: 700; background: rgba(56,189,248,0.15); color: #38bdf8; border: 1px solid rgba(56,189,248,0.3);">Step 1</span>
                </div>

                <!-- Step 2 -->
                <div id="step_check_images_received_card" style="padding: 14px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); display: flex; align-items: center; justify-content: space-between; transition: all 0.2s;">
                    <div style="display: flex; align-items: center; gap: 14px;">
                        <input type="checkbox" id="step_check_images_received" onchange="toggleChecklistStep('check_images_received', this.checked)" style="width: 18px; height: 18px; accent-color: #00e676; cursor: pointer;">
                        <div>
                            <h4 style="font-size: 0.95rem; font-weight: 700; color: #f8fafc; margin: 0;">2. Check Images Received</h4>
                            <p style="font-size: 0.73rem; color: #94a3b8; margin: 2px 0 0 0;">Check image files or check PDFs uploaded for the period</p>
                        </div>
                    </div>
                    <span style="font-size: 0.72rem; padding: 3px 10px; border-radius: 20px; font-weight: 700; background: rgba(250,204,21,0.15); color: #facc15; border: 1px solid rgba(250,204,21,0.3);">Step 2</span>
                </div>

                <!-- Step 3 -->
                <div id="step_extraction_ai_categorization_done_card" style="padding: 14px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); display: flex; align-items: center; justify-content: space-between; transition: all 0.2s;">
                    <div style="display: flex; align-items: center; gap: 14px;">
                        <input type="checkbox" id="step_extraction_ai_categorization_done" onchange="toggleChecklistStep('extraction_ai_categorization_done', this.checked)" style="width: 18px; height: 18px; accent-color: #00e676; cursor: pointer;">
                        <div>
                            <h4 style="font-size: 0.95rem; font-weight: 700; color: #f8fafc; margin: 0;">3. Statement Extraction & AI Categorization Completed</h4>
                            <p style="font-size: 0.73rem; color: #94a3b8; margin: 2px 0 0 0;">OCR text extracted, transactions parsed, check data read, and AI GL accounts assigned</p>
                        </div>
                    </div>
                    <span style="font-size: 0.72rem; padding: 3px 10px; border-radius: 20px; font-weight: 700; background: rgba(168,85,247,0.15); color: #c084fc; border: 1px solid rgba(168,85,247,0.3);">Step 3</span>
                </div>

                <!-- Step 4 -->
                <div id="step_accountant_reviewed_card" style="padding: 14px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); display: flex; align-items: center; justify-content: space-between; transition: all 0.2s;">
                    <div style="display: flex; align-items: center; gap: 14px;">
                        <input type="checkbox" id="step_accountant_reviewed" onchange="toggleChecklistStep('accountant_reviewed', this.checked)" style="width: 18px; height: 18px; accent-color: #00e676; cursor: pointer;">
                        <div>
                            <h4 style="font-size: 0.95rem; font-weight: 700; color: #f8fafc; margin: 0;">4. Accountant Reviewed & Reconciled</h4>
                            <p style="font-size: 0.73rem; color: #94a3b8; margin: 2px 0 0 0;">Final accountant review completed and ready for export to QBO/Accounting software</p>
                        </div>
                    </div>
                    <span style="font-size: 0.72rem; padding: 3px 10px; border-radius: 20px; font-weight: 700; background: rgba(0,230,118,0.15); color: #00e676; border: 1px solid rgba(0,230,118,0.3);">Step 4</span>
                </div>

                <div style="margin-top: 10px;">
                    <label style="font-size: 0.78rem; font-weight: 700; color: #cbd5e1; display: block; margin-bottom: 6px;">Bookkeeping Notes / Review Comments:</label>
                    <textarea id="checklistNotesInput" rows="3" placeholder="Add optional reviewer notes or accounting comments for bookkeeping..." style="width: 100%; padding: 10px 14px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; color: #fff; font-size: 0.8rem; outline: none; resize: vertical;"></textarea>
                    <button onclick="saveChecklistNotes(false)" style="margin-top: 8px; padding: 6px 14px; background: rgba(56,189,248,0.15); border: 1px solid rgba(56,189,248,0.35); color: #38bdf8; font-weight: 700; border-radius: 8px; font-size: 0.76rem; cursor: pointer;">💾 Save Bookkeeping Notes</button>
                </div>
            </div>

            <!-- Tax Section -->
            <div id="checklistTaxSection" style="display: none; flex-direction: column; gap: 12px;">
                <!-- Tax Step 1 -->
                <div id="step_tax_docs_requested_card" style="padding: 12px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); display: flex; align-items: center; justify-content: space-between; transition: all 0.2s;">
                    <div style="display: flex; align-items: center; gap: 14px;">
                        <input type="checkbox" id="step_tax_docs_requested" onchange="toggleChecklistStep('tax_docs_requested', this.checked)" style="width: 18px; height: 18px; accent-color: #f87171; cursor: pointer;">
                        <div>
                            <h4 style="font-size: 0.92rem; font-weight: 700; color: #f8fafc; margin: 0;">1. Documents Requested</h4>
                            <p style="font-size: 0.72rem; color: #94a3b8; margin: 2px 0 0 0;">Tax document checklist and request email sent to client</p>
                        </div>
                    </div>
                    <span style="font-size: 0.7rem; padding: 3px 10px; border-radius: 20px; font-weight: 700; background: rgba(239,68,68,0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.3);">Step 1</span>
                </div>

                <!-- Tax Step 2 -->
                <div id="step_tax_docs_received_card" style="padding: 12px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); display: flex; align-items: center; justify-content: space-between; transition: all 0.2s;">
                    <div style="display: flex; align-items: center; gap: 14px;">
                        <input type="checkbox" id="step_tax_docs_received" onchange="toggleChecklistStep('tax_docs_received', this.checked)" style="width: 18px; height: 18px; accent-color: #f87171; cursor: pointer;">
                        <div>
                            <h4 style="font-size: 0.92rem; font-weight: 700; color: #f8fafc; margin: 0;">2. Documents Received</h4>
                            <p style="font-size: 0.72rem; color: #94a3b8; margin: 2px 0 0 0;">Tax documents (W-2, 1099s, K-1s, receipts) received and uploaded</p>
                        </div>
                    </div>
                    <span style="font-size: 0.7rem; padding: 3px 10px; border-radius: 20px; font-weight: 700; background: rgba(245,158,11,0.15); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3);">Step 2</span>
                </div>

                <!-- Tax Step 3 -->
                <div id="step_tax_organizer_card" style="padding: 12px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); display: flex; align-items: center; justify-content: space-between; transition: all 0.2s;">
                    <div style="display: flex; align-items: center; gap: 14px;">
                        <input type="checkbox" id="step_tax_organizer" onchange="toggleChecklistStep('tax_organizer', this.checked)" style="width: 18px; height: 18px; accent-color: #f87171; cursor: pointer;">
                        <div>
                            <h4 style="font-size: 0.92rem; font-weight: 700; color: #f8fafc; margin: 0;">3. Tax Organizer</h4>
                            <p style="font-size: 0.72rem; color: #94a3b8; margin: 2px 0 0 0;">Tax organizer questionnaire filled out and verified</p>
                        </div>
                    </div>
                    <span style="font-size: 0.7rem; padding: 3px 10px; border-radius: 20px; font-weight: 700; background: rgba(168,85,247,0.15); color: #c084fc; border: 1px solid rgba(168,85,247,0.3);">Step 3</span>
                </div>

                <!-- Tax Step 4 -->
                <div id="step_tax_preparation_card" style="padding: 12px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); display: flex; align-items: center; justify-content: space-between; transition: all 0.2s;">
                    <div style="display: flex; align-items: center; gap: 14px;">
                        <input type="checkbox" id="step_tax_preparation" onchange="toggleChecklistStep('tax_preparation', this.checked)" style="width: 18px; height: 18px; accent-color: #f87171; cursor: pointer;">
                        <div>
                            <h4 style="font-size: 0.92rem; font-weight: 700; color: #f8fafc; margin: 0;">4. Preparation</h4>
                            <p style="font-size: 0.72rem; color: #94a3b8; margin: 2px 0 0 0;">Tax return preparation in progress in tax software</p>
                        </div>
                    </div>
                    <span style="font-size: 0.7rem; padding: 3px 10px; border-radius: 20px; font-weight: 700; background: rgba(56,189,248,0.15); color: #38bdf8; border: 1px solid rgba(56,189,248,0.3);">Step 4</span>
                </div>

                <!-- Tax Step 5 -->
                <div id="step_tax_review_card" style="padding: 12px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); display: flex; align-items: center; justify-content: space-between; transition: all 0.2s;">
                    <div style="display: flex; align-items: center; gap: 14px;">
                        <input type="checkbox" id="step_tax_review" onchange="toggleChecklistStep('tax_review', this.checked)" style="width: 18px; height: 18px; accent-color: #f87171; cursor: pointer;">
                        <div>
                            <h4 style="font-size: 0.92rem; font-weight: 700; color: #f8fafc; margin: 0;">5. Review</h4>
                            <p style="font-size: 0.72rem; color: #94a3b8; margin: 2px 0 0 0;">Senior CPA / Reviewer quality check and approval completed</p>
                        </div>
                    </div>
                    <span style="font-size: 0.7rem; padding: 3px 10px; border-radius: 20px; font-weight: 700; background: rgba(250,204,21,0.15); color: #facc15; border: 1px solid rgba(250,204,21,0.3);">Step 5</span>
                </div>

                <!-- Tax Step 6 -->
                <div id="step_tax_client_signature_card" style="padding: 12px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); display: flex; align-items: center; justify-content: space-between; transition: all 0.2s;">
                    <div style="display: flex; align-items: center; gap: 14px;">
                        <input type="checkbox" id="step_tax_client_signature" onchange="toggleChecklistStep('tax_client_signature', this.checked)" style="width: 18px; height: 18px; accent-color: #f87171; cursor: pointer;">
                        <div>
                            <h4 style="font-size: 0.92rem; font-weight: 700; color: #f8fafc; margin: 0;">6. Client Signature</h4>
                            <p style="font-size: 0.72rem; color: #94a3b8; margin: 2px 0 0 0;">Form 8879 authorization signed by taxpayer / client</p>
                        </div>
                    </div>
                    <span style="font-size: 0.7rem; padding: 3px 10px; border-radius: 20px; font-weight: 700; background: rgba(168,85,247,0.15); color: #c084fc; border: 1px solid rgba(168,85,247,0.3);">Step 6</span>
                </div>

                <!-- Tax Step 7 -->
                <div id="step_tax_efile_card" style="padding: 12px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); display: flex; align-items: center; justify-content: space-between; transition: all 0.2s;">
                    <div style="display: flex; align-items: center; gap: 14px;">
                        <input type="checkbox" id="step_tax_efile" onchange="toggleChecklistStep('tax_efile', this.checked)" style="width: 18px; height: 18px; accent-color: #f87171; cursor: pointer;">
                        <div>
                            <h4 style="font-size: 0.92rem; font-weight: 700; color: #f8fafc; margin: 0;">7. E-file</h4>
                            <p style="font-size: 0.72rem; color: #94a3b8; margin: 2px 0 0 0;">Tax return transmitted / e-filed with IRS and State taxing agencies</p>
                        </div>
                    </div>
                    <span style="font-size: 0.7rem; padding: 3px 10px; border-radius: 20px; font-weight: 700; background: rgba(56,189,248,0.15); color: #38bdf8; border: 1px solid rgba(56,189,248,0.3);">Step 7</span>
                </div>

                <!-- Tax Step 8 -->
                <div id="step_tax_accepted_card" style="padding: 12px 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); display: flex; align-items: center; justify-content: space-between; transition: all 0.2s;">
                    <div style="display: flex; align-items: center; gap: 14px;">
                        <input type="checkbox" id="step_tax_accepted" onchange="toggleChecklistStep('tax_accepted', this.checked)" style="width: 18px; height: 18px; accent-color: #f87171; cursor: pointer;">
                        <div>
                            <h4 style="font-size: 0.92rem; font-weight: 700; color: #f8fafc; margin: 0;">8. Accepted</h4>
                            <p style="font-size: 0.72rem; color: #94a3b8; margin: 2px 0 0 0;">IRS and State e-file acknowledgment received and accepted</p>
                        </div>
                    </div>
                    <span style="font-size: 0.7rem; padding: 3px 10px; border-radius: 20px; font-weight: 700; background: rgba(0,230,118,0.15); color: #00e676; border: 1px solid rgba(0,230,118,0.3);">Step 8</span>
                </div>

                <div style="margin-top: 10px;">
                    <label style="font-size: 0.78rem; font-weight: 700; color: #cbd5e1; display: block; margin-bottom: 6px;">Tax Preparation Notes / Comments:</label>
                    <textarea id="checklistTaxNotesInput" rows="3" placeholder="Add optional preparer/reviewer notes or tax return comments..." style="width: 100%; padding: 10px 14px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; color: #fff; font-size: 0.8rem; outline: none; resize: vertical;"></textarea>
                    <button onclick="saveChecklistNotes(true)" style="margin-top: 8px; padding: 6px 14px; background: rgba(248,113,113,0.15); border: 1px solid rgba(248,113,113,0.35); color: #f87171; font-weight: 700; border-radius: 8px; font-size: 0.76rem; cursor: pointer;">💾 Save Tax Notes</button>
                </div>

                <!-- ══ TAX DOCUMENT TRACKING PANEL ══ -->
                <div id="taxDocTrackingPanel" style="margin-top: 18px; border: 1px solid rgba(248,113,113,0.25); border-radius: 14px; background: rgba(248,113,113,0.04); overflow: hidden;">
                    <!-- Header bar -->
                    <div style="padding: 12px 18px; background: rgba(248,113,113,0.10); border-bottom: 1px solid rgba(248,113,113,0.2); display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 1rem;">📂</span>
                            <span style="font-family: 'Outfit', sans-serif; font-size: 0.95rem; font-weight: 800; color: #f8fafc;">Tax Document Tracker</span>
                            <select id="taxDocYearSelect" onchange="onTaxDocYearChange(this.value)" style="background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(248,113,113,0.4); color: #f87171; border-radius: 8px; padding: 3px 10px; font-size: 0.78rem; font-weight: 800; cursor: pointer; outline: none; box-shadow: 0 0 10px rgba(0,0,0,0.3);"></select>
                            <span id="taxDocStatusBadge" style="font-size: 0.7rem; padding: 3px 12px; border-radius: 20px; font-weight: 800; background: rgba(148,163,184,0.15); color: #94a3b8; border: 1px solid rgba(148,163,184,0.3);">Loading…</span>
                        </div>
                        <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
                            <span id="taxDocEmailSentLabel" style="font-size: 0.7rem; color: #64748b; font-style: italic;"></span>
                            <button onclick="sendTaxRequirementsEmail()" id="btnSendTaxEmail" style="padding: 6px 14px; background: linear-gradient(135deg,#2563eb,#38bdf8); color: #fff; border: none; border-radius: 8px; font-size: 0.78rem; font-weight: 800; cursor: pointer; display: flex; align-items: center; gap: 6px;">📧 Send Requirements Email</button>
                            <button onclick="copyTaxRequirementsFromYear()" style="padding: 6px 14px; background: rgba(250,204,21,0.12); border: 1px solid rgba(250,204,21,0.3); color: #facc15; border-radius: 8px; font-size: 0.78rem; font-weight: 800; cursor: pointer;">📋 Copy Last Year</button>
                        </div>
                    </div>

                    <!-- Requirements Panel -->
                    <div id="taxDocPanel-reqs" style="padding: 14px 18px;">
                        <div style="display: flex; justify-content: flex-end; gap: 8px; margin-bottom: 10px;">
                            <button onclick="openAddTaxRequirementModal()" style="padding: 6px 14px; background: rgba(248,113,113,0.15); border: 1px solid rgba(248,113,113,0.3); color: #f87171; border-radius: 8px; font-size: 0.78rem; font-weight: 800; cursor: pointer;">+ Add Document</button>
                        </div>
                        <div id="taxReqTableWrap" style="width: 100%; overflow: hidden;">
                            <table style="width: 100%; table-layout: fixed; border-collapse: collapse; font-size: 0.82rem;">
                                <thead>
                                    <tr style="text-align: left; color: #64748b; font-size: 0.72rem; text-transform: uppercase; border-bottom: 1px solid rgba(255,255,255,0.07);">
                                        <th style="padding: 6px 8px; width: 22%;">Type</th>
                                        <th style="padding: 6px 8px; width: 33%;">Label / Source</th>
                                        <th style="padding: 6px 8px; width: 10%; text-align: center;">Done</th>
                                        <th style="padding: 6px 8px; width: 17%;">Status</th>
                                        <th style="padding: 6px 8px; text-align: right; width: 18%;">Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="taxReqTableBody">
                                    <tr><td colspan="4" style="padding: 16px; text-align: center; color: #475569;">Loading requirements…</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                <!-- ══ END TAX DOCUMENT TRACKING PANEL ══ -->
            </div>
        </div>

        <div style="padding: 14px 24px; border-top: 1px solid rgba(255,255,255,0.08); background: rgba(0,0,0,0.25); display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; color: #64748b;">
            <span>CRM Bookkeeping & Tax Workflow System</span>
            <div style="display: flex; gap: 10px; align-items: center;">
                <button onclick="openSendCustomerEmailModal(event, currentChecklistCustomerId)" style="padding: 6px 16px; background: rgba(56, 189, 248, 0.18); border: 1px solid rgba(56, 189, 248, 0.45); color: #38bdf8; font-weight: 700; border-radius: 8px; font-size: 0.78rem; cursor: pointer; display: flex; align-items: center; gap: 6px;" title="Send Email Message to Customer">📧 Send Email</button>
                <button onclick="closeCustomerChecklistModal()" style="padding: 6px 16px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); color: #fff; font-weight: 700; border-radius: 8px; font-size: 0.78rem; cursor: pointer;">Close</button>
            </div>
        </div>
    </div>
</div>`;

            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = storageModalHtml + pdfViewerModalHtml + customerChecklistModalHtml;
            while (tempDiv.firstElementChild) {
                const el = tempDiv.firstElementChild;
                document.body.appendChild(el);
                el.addEventListener('click', (e) => {
                    if (e.target === el) {
                        if (el.id === 'customerStorageModal') closeCustomerStorageModal();
                        if (el.id === 'pdfViewerModal') closePdfViewerModal();
                        if (el.id === 'customerChecklistModal') closeCustomerChecklistModal();
                    }
                });
            }
        })();
        // --- Move customerStorageModal, pdfViewerModal, customerChecklistModal, sendCustomerEmailModal & customerCommsHistoryModal to body root ---
        (function() {
            const sendEmailModalHtml = `
<div id="sendCustomerEmailModal" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.85); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); z-index: 2147483647; justify-content: center; align-items: center; padding: 20px;">
    <div style="background: #0f172a; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 20px; max-width: 650px; width: 100%; display: flex; flex-direction: column; box-shadow: 0 25px 50px rgba(0,0,0,0.6); gap: 16px; color: #fff; overflow: hidden;">
        <div style="padding: 16px 24px; border-bottom: 1px solid rgba(255,255,255,0.08); background: rgba(0,0,0,0.3); display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h3 id="sendEmailModalTitle" style="font-family: 'Outfit', sans-serif; font-size: 1.2rem; font-weight: 800; color: #fff; margin: 0; display: flex; align-items: center; gap: 8px;">
                    📧 Send Email to Customer
                </h3>
                <p id="sendEmailModalSubtitle" style="font-size: 0.78rem; color: #94a3b8; margin: 4px 0 0 0; font-family: monospace;">Recipient: ...</p>
            </div>
            <button onclick="closeSendCustomerEmailModal()" style="background: transparent; border: none; color: #94a3b8; cursor: pointer; font-size: 1.2rem; padding: 4px;">✕</button>
        </div>

        <div style="padding: 0 24px; display: flex; flex-direction: column; gap: 14px;">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                <div>
                    <label style="display: block; font-size: 0.72rem; font-weight: 700; color: #94a3b8; margin-bottom: 4px; text-transform: uppercase;">To (Customer Email):</label>
                    <input type="email" id="emailFormTo" required readonly style="width: 100%; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 8px 12px; font-size: 0.85rem; color: #38bdf8; font-weight: 700;">
                </div>
                <div>
                    <label style="display: block; font-size: 0.72rem; font-weight: 700; color: #94a3b8; margin-bottom: 4px; text-transform: uppercase;">Reply-To (Your Inbox):</label>
                    <input type="email" id="emailFormReplyTo" required style="width: 100%; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 8px 12px; font-size: 0.85rem; color: #facc15; font-weight: 700;">
                </div>
            </div>

            <div>
                <label style="display: block; font-size: 0.72rem; font-weight: 700; color: #94a3b8; margin-bottom: 4px; text-transform: uppercase;">Quick Message Template:</label>
                <select id="emailFormTemplateSelect" onchange="applyEmailTemplate(this.value)" style="width: 100%; background: #0b1324; border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; padding: 8px 12px; font-size: 0.85rem; color: #c084fc; font-weight: 700; outline: none; cursor: pointer;">
                    <option value="custom">💬 Custom Message</option>
                    <option value="tax_docs">📑 Tax Organizer & Document Request</option>
                    <option value="bk_stmt">📊 Monthly Bank Statement Request</option>
                    <option value="sign_8879">✍️ Form 8879 E-Signature Required</option>
                </select>
            </div>

            <div>
                <label style="display: block; font-size: 0.72rem; font-weight: 700; color: #94a3b8; margin-bottom: 4px; text-transform: uppercase;">Subject Line *:</label>
                <input type="text" id="emailFormSubject" required placeholder="e.g. Document Request for April 2026" style="width: 100%; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 8px 12px; font-size: 0.88rem; color: #fff; font-weight: 600;">
            </div>

            <div>
                <label style="display: block; font-size: 0.72rem; font-weight: 700; color: #94a3b8; margin-bottom: 4px; text-transform: uppercase;">Message Body *:</label>
                <textarea id="emailFormMessage" rows="6" required placeholder="Write your message here..." style="width: 100%; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 10px 12px; font-size: 0.88rem; color: #fff; resize: vertical; outline: none; font-family: inherit;"></textarea>
            </div>
        </div>

        <div style="padding: 14px 24px; border-top: 1px solid rgba(255,255,255,0.08); background: rgba(0,0,0,0.25); display: flex; justify-content: space-between; align-items: center;">
            <button type="button" onclick="openCustomerCommsHistoryModal(currentEmailCustomerId)" style="padding: 8px 16px; background: rgba(168, 85, 247, 0.2); border: 1px solid rgba(168, 85, 247, 0.4); color: #c084fc; font-weight: 700; border-radius: 8px; font-size: 0.78rem; cursor: pointer;">💬 View Email History</button>
            <div style="display: flex; gap: 10px;">
                <button type="button" onclick="closeSendCustomerEmailModal()" style="padding: 8px 16px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); color: #fff; font-weight: 700; border-radius: 8px; font-size: 0.78rem; cursor: pointer;">Cancel</button>
                <button type="button" id="sendEmailSubmitBtn" onclick="submitSendCustomerEmail()" style="padding: 8px 24px; background: linear-gradient(135deg, #06b6d4, #2563eb); color: #fff; font-weight: 800; border: none; border-radius: 8px; font-size: 0.8rem; cursor: pointer; box-shadow: 0 0 15px rgba(6, 182, 212, 0.35);">🚀 Send Email</button>
            </div>
        </div>
    </div>
</div>`;

            const commsHistoryModalHtml = `
<div id="customerCommsHistoryModal" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.85); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); z-index: 2147483647; justify-content: center; align-items: center; padding: 20px;">
    <div style="background: #0b1324; border: 1px solid rgba(168, 85, 247, 0.3); border-radius: 20px; max-width: 750px; width: 100%; max-height: 85vh; display: flex; flex-direction: column; box-shadow: 0 25px 50px rgba(0,0,0,0.6); gap: 16px; color: #fff; overflow: hidden;">
        <div style="padding: 16px 24px; border-bottom: 1px solid rgba(255,255,255,0.08); background: rgba(0,0,0,0.3); display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h3 id="commsHistoryModalTitle" style="font-family: 'Outfit', sans-serif; font-size: 1.2rem; font-weight: 800; color: #fff; margin: 0; display: flex; align-items: center; gap: 8px;">
                    💬 Customer Communication History
                </h3>
                <p id="commsHistoryModalSubtitle" style="font-size: 0.78rem; color: #94a3b8; margin: 4px 0 0 0;">Email logs & received replies</p>
            </div>
            <div style="display: flex; align-items: center; gap: 12px;">
                <button type="button" onclick="toggleWebhookLogInspector(event)" style="padding: 4px 10px; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.35); color: #38bdf8; border-radius: 6px; font-weight: 700; font-size: 0.72rem; cursor: pointer;" title="Inspect raw webhook logs received by server from Resend">🔍 Webhook Inspector</button>
                <button id="commsHistoryMarkAllReadBtn" onclick="markAllCommsReadForCurrentCustomer()" style="display: none; padding: 4px 10px; background: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34, 197, 94, 0.35); color: #4ade80; border-radius: 6px; font-weight: 700; font-size: 0.72rem; cursor: pointer;" title="Mark all messages as read for this customer">✓ Mark All Read</button>
                <button onclick="closeCustomerCommsHistoryModal()" style="background: transparent; border: none; color: #94a3b8; cursor: pointer; font-size: 1.2rem; padding: 4px;">✕</button>
            </div>
        </div>

        <div id="commsHistoryListBody" style="padding: 20px 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 16px; min-height: 250px;">
            <p style="text-align: center; color: #94a3b8;">Loading history...</p>
        </div>

        <div style="padding: 14px 24px; border-top: 1px solid rgba(255,255,255,0.08); background: rgba(0,0,0,0.25); display: flex; justify-content: flex-end;">
            <button type="button" onclick="closeCustomerCommsHistoryModal()" style="padding: 6px 16px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); color: #fff; font-weight: 700; border-radius: 8px; font-size: 0.78rem; cursor: pointer;">Close</button>
        </div>
    </div>
</div>`;

            const moveFileModalHtml = `
<div id="moveFileModal" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.85); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); z-index: 2147483649; justify-content: center; align-items: center; padding: 20px;">
    <div style="background: #0f172a; border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 20px; max-width: 520px; width: 100%; display: flex; flex-direction: column; box-shadow: 0 25px 60px rgba(0,0,0,0.8); gap: 16px; color: #fff; overflow: hidden;">
        <div style="padding: 16px 20px; border-bottom: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.3rem;">🚚</span>
                <h3 id="moveFileModalTitle" style="font-family: 'Outfit', sans-serif; font-size: 1.1rem; font-weight: 800; color: #fbbf24; margin: 0;">Move File to Folder</h3>
            </div>
            <button onclick="closeMoveFileModal()" style="background: transparent; border: none; color: #94a3b8; cursor: pointer; font-size: 1.2rem; padding: 4px;">✕</button>
        </div>

        <div style="padding: 0 20px; display: flex; flex-direction: column; gap: 14px;">
            <div>
                <label id="moveFileTargetLabel" style="display: block; font-size: 0.72rem; font-weight: 700; color: #94a3b8; margin-bottom: 4px; text-transform: uppercase;">File to Move:</label>
                <div id="moveFileTargetName" style="background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 8px 12px; font-size: 0.88rem; color: #38bdf8; font-weight: 700; word-break: break-word; max-height: 80px; overflow-y: auto;">-</div>
            </div>

            <div>
                <label style="display: block; font-size: 0.72rem; font-weight: 700; color: #94a3b8; margin-bottom: 4px; text-transform: uppercase;">Select Destination Folder:</label>
                <select id="moveFileFolderSelect" onchange="handleMoveFolderSelectChange(this.value)" style="width: 100%; background: #0b1324; border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 8px; padding: 10px 12px; font-size: 0.88rem; color: #fbbf24; font-weight: 700; outline: none; cursor: pointer;">
                    <option value="Inbox/">📥 Inbox (Received Attachments)</option>
                    <option value="Tax Documents/">📂 Tax Documents (Main Folder)</option>
                    <option value="Tax Documents/Tax Year 2026/">📁 Tax Documents / Tax Year 2026</option>
                    <option value="Tax Documents/Tax Year 2025/">📁 Tax Documents / Tax Year 2025</option>
                    <option value="Bank Statements/">📁 Bank Statements</option>
                    <option value="Check Images/">📁 Check Images</option>
                    <option value="custom">✏️ Enter Custom Folder Path...</option>
                </select>
            </div>

            <div id="moveFileCustomGroup" style="display: none;">
                <label style="display: block; font-size: 0.72rem; font-weight: 700; color: #94a3b8; margin-bottom: 4px; text-transform: uppercase;">Custom Subfolder Path:</label>
                <input type="text" id="moveFileCustomInput" placeholder="e.g. Tax Documents/Tax Year 2026/" style="width: 100%; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 8px 12px; font-size: 0.85rem; color: #fff; font-weight: 600;">
            </div>
        </div>

        <div style="padding: 14px 20px; border-top: 1px solid rgba(255,255,255,0.08); background: rgba(0,0,0,0.25); display: flex; justify-content: flex-end; gap: 10px;">
            <button type="button" onclick="closeMoveFileModal()" style="padding: 8px 16px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); color: #fff; font-weight: 700; border-radius: 8px; font-size: 0.78rem; cursor: pointer;">Cancel</button>
            <button type="button" id="submitMoveFileBtn" onclick="confirmSubmitMoveFile()" style="padding: 8px 20px; background: linear-gradient(135deg, #f59e0b, #d97706); color: #fff; font-weight: 800; border: none; border-radius: 8px; font-size: 0.8rem; cursor: pointer; box-shadow: 0 0 15px rgba(245, 158, 11, 0.35);">🚚 Move File Now</button>
        </div>
    </div>
</div>`;

            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = sendEmailModalHtml + commsHistoryModalHtml + moveFileModalHtml;
            while (tempDiv.firstElementChild) {
                const el = tempDiv.firstElementChild;
                document.body.appendChild(el);
            }
        })();

        document.addEventListener('DOMContentLoaded', () => {
            fetchTaxTeamMembers();
            if ('{{ active_tab }}' === 'compliance') {
                loadComplianceData();
            }
        });

        // ── TAX PREP TEAM MANAGEMENT MODAL LOGIC ───────────────────────
        let currentTaxTeamList = [];

        async function fetchTaxTeamMembers() {
            try {
                const res = await fetch('/api/tax-team');
                if (res.ok) {
                    const data = await res.json();
                    currentTaxTeamList = data.team || [];
                    renderTaxTeamTable();
                    populateCustomerTaxPrepDropdowns();
                }
            } catch (err) {
                console.error('Error fetching TaxTeam:', err);
            }
        }

        function renderTaxTeamTable() {
            const tbody = document.getElementById('taxTeamTableBody');
            if (!tbody) return;
            if (currentTaxTeamList.length === 0) {
                tbody.innerHTML = '<tr><td colSpan="3" style="padding: 24px; text-align: center; color: #64748b;">No Tax Prep Team members added yet.</td></tr>';
                return;
            }
            tbody.innerHTML = currentTaxTeamList.map(m => `
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); transition: background 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.03)'" onmouseout="this.style.background='transparent'">
                    <td style="padding: 10px 18px; font-family: monospace; color: #facc15; font-weight: 700;">#${m.id}</td>
                    <td style="padding: 10px 18px; font-weight: 700; color: #fff;">👤 ${m.name}</td>
                    <td style="padding: 10px 18px; text-align: right;">
                        <button type="button" onclick="editTaxTeamMember(event, ${m.id}, '${m.name.replace(/'/g, "\\'")}')" style="padding: 4px 10px; background: rgba(250, 204, 21, 0.15); border: 1px solid rgba(250, 204, 21, 0.4); color: #facc15; border-radius: 6px; font-size: 0.72rem; font-weight: 700; cursor: pointer; margin-right: 6px;">✏️ EDIT</button>
                        <button type="button" onclick="deleteTaxTeamMember(event, ${m.id}, '${m.name.replace(/'/g, "\\'")}')" style="padding: 4px 10px; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); color: #f87171; border-radius: 6px; font-size: 0.72rem; font-weight: 700; cursor: pointer;">🗑️ DEL</button>
                    </td>
                </tr>
            `).join('');
        }

        function populateCustomerTaxPrepDropdowns() {
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
        }

        function openTaxTeamModal() {
            const modal = document.getElementById('taxTeamModal');
            if (!modal) return;
            modal.style.display = 'flex';
            resetTaxTeamForm();
            fetchTaxTeamMembers();
        }

        function closeTaxTeamModal() {
            const modal = document.getElementById('taxTeamModal');
            if (modal) modal.style.display = 'none';
        }

        function resetTaxTeamForm() {
            const idEl = document.getElementById('taxTeamFormId');
            const nameEl = document.getElementById('taxTeamFormName');
            const cancelBtn = document.getElementById('taxTeamCancelEditBtn');
            const subBtn = document.getElementById('taxTeamSubmitBtn');
            if (idEl) idEl.value = '';
            if (nameEl) nameEl.value = '';
            if (cancelBtn) cancelBtn.style.display = 'none';
            if (subBtn) subBtn.textContent = 'Add Member';
        }

        function editTaxTeamMember(arg1, arg2, arg3) {
            let event = null, id = arg1, name = arg2;
            if (arg1 && arg1.preventDefault) {
                event = arg1;
                event.preventDefault();
                event.stopPropagation();
                id = arg2;
                name = arg3;
            }
            const idEl = document.getElementById('taxTeamFormId');
            const nameEl = document.getElementById('taxTeamFormName');
            const cancelBtn = document.getElementById('taxTeamCancelEditBtn');
            const subBtn = document.getElementById('taxTeamSubmitBtn');
            if (idEl) idEl.value = id;
            if (nameEl) nameEl.value = name;
            if (cancelBtn) cancelBtn.style.display = 'inline-block';
            if (subBtn) subBtn.textContent = 'Update Member';
            if (nameEl) {
                nameEl.focus();
                nameEl.select();
            }
        }

        async function saveTaxTeamMember(e) {
            e.preventDefault();
            const id = document.getElementById('taxTeamFormId')?.value;
            const name = (document.getElementById('taxTeamFormName')?.value || '').trim();
            if (!name) return alert('Please enter member name.');
            const method = id ? 'PUT' : 'POST';
            const url = id ? `/api/tax-team/${id}` : '/api/tax-team';
            try {
                const res = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name })
                });
                if (res.ok) {
                    resetTaxTeamForm();
                    await fetchTaxTeamMembers();
                    if (typeof fetchCustomerRecords === 'function') fetchCustomerRecords(true);
                    if (typeof loadWorkloadSummary === 'function') loadWorkloadSummary();
                } else {
                    const err = await res.json();
                    alert('Error: ' + (err.detail || err.error || 'Failed to save member'));
                }
            } catch (err) {
                alert('Error saving Tax Team member: ' + err.message);
            }
        }

        async function deleteTaxTeamMember(arg1, arg2, arg3) {
            let event = null, id = arg1, name = arg2;
            if (arg1 && arg1.preventDefault) {
                event = arg1;
                event.preventDefault();
                event.stopPropagation();
                id = arg2;
                name = arg3;
            }
            if (!id) return;
            if (!await showCustomConfirm(`Are you sure you want to delete Tax Prep member "${name}"?`, 'Delete Tax Prep Member', 'Yes, Delete', 'Cancel')) return;
            try {
                const res = await fetch(`/api/tax-team/${id}`, { method: 'DELETE' });
                if (res.ok) {
                    await fetchTaxTeamMembers();
                    if (typeof fetchCustomerRecords === 'function') fetchCustomerRecords(true);
                    if (typeof loadWorkloadSummary === 'function') loadWorkloadSummary();
                } else {
                    const err = await res.json();
                    const errMsg = err.detail || err.error || 'Failed to delete member';
                    if (typeof showAlert === 'function') showAlert('Error deleting member: ' + errMsg, 'error', 'Delete Failed');
                    else alert('Error deleting member: ' + errMsg);
                }
            } catch (err) {
                if (typeof showAlert === 'function') showAlert('Error deleting member: ' + err.message, 'error', 'Delete Error');
                else alert('Error deleting member: ' + err.message);
            }
        }

        // ── COMPLIANCE CALENDAR MODULE LOGIC ─────────────────────────────
        let complianceCurrentEvents = [];
        let complianceCurrentYear = new Date().getFullYear();
        let complianceCurrentMonth = new Date().getMonth() + 1;
        let complianceViewMode = 'calendar';

        async function loadComplianceData() {
            if ((!currentCustomerRecords || currentCustomerRecords.length === 0) && typeof fetchCustomerRecords === 'function') {
                await fetchCustomerRecords();
            }
            if ((!currentTaxTeamList || currentTaxTeamList.length === 0) && typeof fetchTaxTeamMembers === 'function') {
                await fetchTaxTeamMembers();
            }
            currentCustomerList = currentCustomerRecords;
            populateComplianceModalDropdowns();
            if (typeof checkCompliancePresetStatus === 'function') {
                checkCompliancePresetStatus();
            }

            const customer = document.getElementById('complianceFilterCustomer')?.value || 'all';
            const category = document.getElementById('complianceFilterCategory')?.value || 'all';
            const status = document.getElementById('complianceFilterStatus')?.value || 'all';
            const taxPrep = document.getElementById('complianceFilterTaxPrep')?.value || 'all';
            const dateRange = document.getElementById('complianceFilterDateRange')?.value || 'month';
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
                let url = `/api/compliance/events?customer_id=${customer}&category=${encodeURIComponent(category)}&status=${encodeURIComponent(status)}&assigned_tax_prep=${encodeURIComponent(taxPrep)}`;
                if (dateRange === 'all_years' && complianceViewMode === 'table') {
                    // Omit year & month to fetch all schedules across all years for Datatable View
                } else {
                    url += `&year=${year}&month=${month}`;
                }

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
            const rangeEl = document.getElementById('complianceFilterDateRange');
            const monthEl = document.getElementById('complianceFilterMonth');

            if (mode === 'calendar') {
                if (gridContainer) gridContainer.style.display = 'block';
                if (tableContainer) tableContainer.style.display = 'none';
                if (btnCal) { btnCal.style.background = 'rgba(245, 158, 11, 0.25)'; btnCal.style.color = '#f59e0b'; }
                if (btnTab) { btnTab.style.background = 'transparent'; btnTab.style.color = '#94a3b8'; }

                if (rangeEl && rangeEl.value === 'all_years') {
                    rangeEl.value = 'month';
                    if (monthEl) monthEl.style.display = 'inline-block';
                    loadComplianceData();
                } else {
                    renderComplianceCalendarGrid();
                }
            } else {
                if (gridContainer) gridContainer.style.display = 'none';
                if (tableContainer) tableContainer.style.display = 'block';
                if (btnCal) { btnCal.style.background = 'transparent'; btnCal.style.color = '#94a3b8'; }
                if (btnTab) { btnTab.style.background = 'rgba(245, 158, 11, 0.25)'; btnTab.style.color = '#f59e0b'; }

                if (rangeEl && rangeEl.value === 'all_years') {
                    if (monthEl) monthEl.style.display = 'none';
                    loadComplianceData();
                } else {
                    if (monthEl) monthEl.style.display = 'inline-block';
                    renderComplianceTable();
                }
            }
        }

        function onComplianceDateRangeChange() {
            const rangeVal = document.getElementById('complianceFilterDateRange')?.value || 'month';
            const monthEl = document.getElementById('complianceFilterMonth');
            if (rangeVal === 'all_years') {
                if (monthEl) monthEl.style.display = 'none';
                if (complianceViewMode !== 'table') {
                    setComplianceViewMode('table');
                } else {
                    loadComplianceData();
                }
            } else {
                if (monthEl) monthEl.style.display = 'inline-block';
                loadComplianceData();
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

        function formatDateMMDDYYYY(dateStr) {
            if (!dateStr) return '—';
            const clean = String(dateStr).trim().split('T')[0];
            const parts = clean.split('-');
            if (parts.length === 3) {
                const [yyyy, mm, dd] = parts;
                return `${mm}/${dd}/${yyyy}`;
            }
            return dateStr;
        }

        function renderComplianceSummaryKPIs() {
            const now = new Date();
            const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0, 0);
            const in7DaysEnd = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 7, 23, 59, 59, 999);

            let overdueCount = 0;
            let dueNext7DaysCount = 0;
            let completedCount = 0;

            (complianceCurrentEvents || []).forEach(e => {
                const isDone = e.status === 'Completed';
                if (isDone) {
                    completedCount++;
                    return;
                }

                if (e.due_date) {
                    const cleanDate = String(e.due_date).trim().split('T')[0];
                    const parts = cleanDate.split('-');
                    if (parts.length === 3) {
                        const dueDate = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]), 12, 0, 0);
                        if (dueDate < todayStart || e.status === 'Overdue') {
                            overdueCount++;
                        } else if (dueDate >= todayStart && dueDate <= in7DaysEnd) {
                            dueNext7DaysCount++;
                        }
                    }
                } else if (e.status === 'Overdue') {
                    overdueCount++;
                }
            });

            const totalEvents = complianceCurrentEvents ? complianceCurrentEvents.length : 0;
            const activePending = totalEvents - completedCount;
            const pct = totalEvents > 0 ? Math.round((completedCount / totalEvents) * 100) : 0;

            const elOver = document.getElementById('complianceKpiOverdue');
            const elUp = document.getElementById('complianceKpiUpcoming');
            const elActive = document.getElementById('complianceKpiActiveMonth');
            const elComp = document.getElementById('complianceKpiCompletedMetric');

            if (elOver) elOver.textContent = overdueCount;
            if (elUp) elUp.textContent = dueNext7DaysCount;
            if (elActive) elActive.textContent = activePending;
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

                const dayEvents = (complianceCurrentEvents || []).filter(e => {
                    if (!e || !e.due_date) return false;
                    const cleanDate = String(e.due_date).trim().split('T')[0];
                    return cleanDate === dateStr;
                });

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
                        <td style="padding: 12px 18px; font-family: monospace; font-weight: 700; color: #facc15;">${formatDateMMDDYYYY(e.due_date)}</td>
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
                    if (typeof currentChecklistCustomerId !== 'undefined' && currentChecklistCustomerId) {
                        await loadCustomerChecklist(currentChecklistCustomerId, currentChecklistPeriod);
                    }
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

        async function openPresetComplianceModal(event, preselectedCid = null) {
            if (event && event.preventDefault) {
                event.preventDefault();
                event.stopPropagation();
            }
            try {
                if ((!currentCustomerRecords || currentCustomerRecords.length === 0) && typeof fetchCustomerRecords === 'function') {
                    await fetchCustomerRecords();
                }
                const rawCustList = currentCustomerRecords || currentCustomerList || [];
                const validCustList = rawCustList.filter(c => (c.custumer_number || '').trim() !== 'CUST-0000');

                const modal = document.getElementById('presetComplianceModal');
                const select = document.getElementById('presetComplianceCustomerSelect');
                if (!modal || !select) return;

                select.innerHTML = '<option value="">Select Customer *</option>' + validCustList.map(c => 
                    `<option value="${c.id}" ${preselectedCid && String(preselectedCid) === String(c.id) ? 'selected' : ''}>${c.legal_name} (${c.custumer_number || 'No ID'}) [${c.customer_type || 'Business'}]</option>`
                ).join('');

                modal.style.display = 'flex';
            } catch (err) {
                console.error('Error opening preset compliance modal:', err);
                alert('Error opening Preset Schedule modal: ' + err.message);
            }
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

        async function runBulkPresetComplianceSchedule() {
            const confirmed = await showCustomConfirm("Are you sure you want to generate statutory compliance preset schedules for ALL active clients? (Duplicate events will be automatically skipped)", "Bulk Compliance Generator", "Yes, Generate All", "Cancel");
            if (!confirmed) return;
            try {
                const res = await fetch('/api/compliance/generate-preset-all', { method: 'POST' });
                if (res.ok) {
                    const data = await res.json();
                    const msg = `Bulk Generation Complete!\nProcessed Clients: ${data.processed_clients}\nCreated Events: ${data.total_created}\nSkipped Duplicates: ${data.total_skipped}`;
                    if (typeof showAlert === 'function') {
                        showAlert(msg, 'success', 'All-Clients Schedule Generated');
                    } else {
                        alert(msg);
                    }
                    checkCompliancePresetStatus();
                    if (typeof loadComplianceData === 'function') {
                        await loadComplianceData();
                    }
                } else {
                    const err = await res.json();
                    alert('Error: ' + (err.detail || 'Failed to generate bulk preset schedule'));
                }
            } catch (err) {
                alert('Error running bulk preset schedule: ' + err.message);
            }
        }

        async function checkCompliancePresetStatus() {
            try {
                const res = await fetch('/api/compliance/check-preset-status');
                if (res.ok) {
                    const data = await res.json();
                    const banner = document.getElementById('complianceAutoPresetBanner');
                    const textElem = document.getElementById('complianceAutoPresetBannerText');
                    if (banner) {
                        if (data.needs_preset) {
                            if (textElem) textElem.innerText = `${data.missing_clients_count} out of ${data.total_active_clients} active clients are missing preset statutory tax & compliance deadlines for ${data.target_year}.`;
                            banner.style.display = 'flex';
                        } else {
                            banner.style.display = 'none';
                        }
                    }
                }
            } catch (e) {
                console.error("[PRESET STATUS CHECK ERROR]:", e);
            }
        }

        function populateComplianceModalDropdowns() {
            const custSelect = document.getElementById('complianceModalCustomer');
            const taxPrepSelect = document.getElementById('complianceModalTaxPrep');
            const filterCust = document.getElementById('complianceFilterCustomer');
            const filterTaxPrep = document.getElementById('complianceFilterTaxPrep');

            const rawCusts = (typeof currentCustomerRecords !== 'undefined' && currentCustomerRecords.length > 0) 
                ? currentCustomerRecords 
                : (currentCustomerList || []);
            
            const custs = rawCusts.filter(c => (c.custumer_number || '').trim() !== 'CUST-0000');
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
        }

        async function openCreateComplianceModal(event) {
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
                        sync_customer_tax_prep: document.getElementById('complianceModalSyncCustomerTaxPrep')?.checked || false,
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

        // ── DOCUSEAL E-SIGNATURE FUNCTIONS ──────────────────────────────────────
        let allEsignatureRequests = [];
        let allCustomersCache = [];

        async function fetchEsignatureRequests() {
            try {
                const res = await fetch('/api/esignature/requests');
                if (res.ok) {
                    const data = await res.json();
                    allEsignatureRequests = data.requests || [];
                    renderEsignatureTable();
                }
            } catch (err) {
                console.error('Error fetching e-signature requests:', err);
            }
        }

        function renderEsignatureTable() {
            const tbody = document.getElementById('esignTableBody');
            if (!tbody) return;

            const query = (document.getElementById('esignSearchInput')?.value || '').toLowerCase();
            const statusFilter = (document.getElementById('esignStatusFilter')?.value || '').toLowerCase();

            let filtered = allEsignatureRequests.filter(r => {
                const matchesQuery = (r.customer_name || '').toLowerCase().includes(query) ||
                                     (r.document_name || '').toLowerCase().includes(query) ||
                                     (r.signer_email || '').toLowerCase().includes(query);
                const matchesStatus = !statusFilter || (r.status || '').toLowerCase() === statusFilter;
                return matchesQuery && matchesStatus;
            });

            const total = allEsignatureRequests.length;
            const pending = allEsignatureRequests.filter(r => (r.status || '').toLowerCase() === 'pending').length;
            const completed = allEsignatureRequests.filter(r => (r.status || '').toLowerCase() === 'completed').length;

            if (document.getElementById('esignStatTotal')) document.getElementById('esignStatTotal').innerText = total;
            if (document.getElementById('esignStatPending')) document.getElementById('esignStatPending').innerText = pending;
            if (document.getElementById('esignStatCompleted')) document.getElementById('esignStatCompleted').innerText = completed;

            if (filtered.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="7" style="padding: 30px; text-align: center; color: #64748b;">
                            No e-signature requests found. Click <strong>"Send E-Signature Request"</strong> to send one.
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = filtered.map(r => {
                const isCompleted = (r.status || '').toLowerCase() === 'completed';
                const badgeColor = isCompleted ? 'background: rgba(74, 222, 128, 0.15); color: #4ade80; border: 1px solid rgba(74, 222, 128, 0.3);' 
                                               : 'background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3);';
                const sentDate = r.created_at ? new Date(r.created_at).toLocaleDateString() : '-';
                const signedDate = r.signed_at ? new Date(r.signed_at).toLocaleDateString() : '-';

                return `
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.04); transition: background 0.2s ease;">
                        <td style="padding: 12px 16px; font-weight: 700; color: #fff;">${escapeHtml(r.customer_name || 'Customer #' + r.customer_id)}</td>
                        <td style="padding: 12px 16px; color: #cbd5e1;">
                            📄 ${escapeHtml(r.document_name || 'Document')}
                            ${r.verification_method === 'IN_PERSON' ?
                                '<br><span style="font-size: 0.68rem; color: #34d399; font-weight: 800; background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); padding: 1px 6px; border-radius: 6px; display: inline-block; margin-top: 3px;" title="IRS Pub 1345 In-Person Verification Record Attached">🛡️ In-Person Verified</span>' :
                                (r.is_tax_form ? '<br><span style="font-size: 0.68rem; color: #fbbf24; font-weight: 800; background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3); padding: 1px 6px; border-radius: 6px; display: inline-block; margin-top: 3px;" title="IRS Tax Form requires ID Check or KBA">⚠️ KBA Pending</span>' : '')
                            }
                        </td>
                        <td style="padding: 12px 16px; color: #94a3b8;">${escapeHtml(r.signer_email)}</td>
                        <td style="padding: 12px 16px;">
                            <span style="padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; ${badgeColor}">
                                ${r.status}
                            </span>
                        </td>
                        <td style="padding: 12px 16px; color: #94a3b8;">${sentDate}</td>
                        <td style="padding: 12px 16px; color: #94a3b8;">${signedDate}</td>
                        <td style="padding: 12px 16px; text-align: right;">
                            <div style="display: flex; justify-content: flex-end; gap: 8px;">
                                ${isCompleted ? 
                                    `<button onclick="openEsignatureSummaryModal(${r.id}, '${escapeHtml(r.document_name)}', '${escapeHtml(r.customer_name)}', '${escapeHtml(r.signer_email)}', '${signedDate}')" style="padding: 6px 12px; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); color: #38bdf8; border-radius: 8px; font-size: 0.75rem; font-weight: 700; cursor: pointer;">👁️ Summary</button>
                                     <a href="/api/esignature/requests/${r.id}/pdf" target="_blank" style="padding: 6px 12px; background: rgba(74, 222, 128, 0.15); border: 1px solid rgba(74, 222, 128, 0.3); color: #4ade80; border-radius: 8px; font-size: 0.75rem; font-weight: 700; text-decoration: none; display: inline-flex; align-items: center; gap: 4px;">📄 Signed PDF</a>
                                     <a href="/api/esignature/requests/${r.id}/audit-pdf" target="_blank" style="padding: 6px 12px; background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.3); color: #c084fc; border-radius: 8px; font-size: 0.75rem; font-weight: 700; text-decoration: none; display: inline-flex; align-items: center; gap: 4px;">📜 Audit Certificate</a>` : 
                                    (r.embed_src ? `<button onclick="viewEsignatureRequest('${escapeHtml(r.embed_src)}', '${escapeHtml(r.document_name)}')" style="padding: 6px 12px; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); color: #38bdf8; border-radius: 8px; font-size: 0.75rem; font-weight: 700; cursor: pointer;">✍️ Sign Document</button>` : '')
                                }
                                <button onclick="deleteEsignatureRequest(${r.id})" style="padding: 6px 10px; background: rgba(244, 63, 94, 0.15); border: 1px solid rgba(244, 63, 94, 0.3); color: #f43f5e; border-radius: 8px; font-size: 0.75rem; font-weight: 700; cursor: pointer;">🗑️</button>
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        async function openCreateEsignatureModal(preselectCustomerId = null) {
            console.log("[ESIGN MODAL] Opening e-signature modal...");
            const modal = document.getElementById('esignatureModal');
            if (!modal) {
                console.error("[ESIGN MODAL] esignatureModal element not found in DOM!");
                return;
            }

            modal.style.display = 'flex';
            modal.style.opacity = '1';
            modal.style.visibility = 'visible';
            modal.style.zIndex = '2147483647';
            if (modal.children && modal.children[0]) {
                modal.children[0].style.transform = 'scale(1)';
                modal.children[0].style.opacity = '1';
            }

            try {
                const res = await fetch('/api/customers?business_only=true');
                if (res.ok) {
                    const data = await res.json();
                    allCustomersCache = data.customers || [];
                    const select = document.getElementById('esignCustomerSelect');
                    if (select) {
                        select.innerHTML = '<option value="">-- Select Customer --</option>' + 
                            allCustomersCache.map(c => `<option value="${c.id}">${escapeHtml(c.legal_name || '')} (${c.parent_name || 'No Parent'})</option>`).join('');
                        if (preselectCustomerId) {
                            select.value = preselectCustomerId;
                        }
                    }
                }
            } catch (err) {
                console.error('Error fetching customers for e-signature modal:', err);
            }

            try {
                if (preselectCustomerId || document.getElementById('esignCustomerSelect')?.value) {
                    onEsignCustomerChange();
                }
            } catch (e) {
                console.error("Error in onEsignCustomerChange:", e);
            }
        }

        function closeCreateEsignatureModal() {
            const modal = document.getElementById('esignatureModal');
            if (modal) {
                modal.style.opacity = '0';
                setTimeout(() => { modal.style.display = 'none'; }, 300);
            }
        }

        function updateEsignIdentityBadge(cust) {
            const badge = document.getElementById('esignCustIdentityBadge');
            const isTaxForm = document.getElementById('esignIsTaxFormCheck')?.checked;
            if (!badge) return;

            if (!cust) {
                badge.style.background = 'rgba(255,255,255,0.05)';
                badge.style.color = '#cbd5e1';
                badge.style.border = '1px solid rgba(255,255,255,0.1)';
                badge.innerHTML = 'Select a customer to view identity status...';
                return;
            }

            if (cust.identity_verified && cust.verification_method === 'IN_PERSON') {
                badge.style.background = 'rgba(16, 185, 129, 0.12)';
                badge.style.color = '#34d399';
                badge.style.border = '1px solid rgba(16, 185, 129, 0.35)';
                badge.innerHTML = `🛡️ <strong>IN-PERSON VERIFIED:</strong> ${cust.id_type || 'Photo ID'} (${cust.id_state_issuer || ''} ${cust.id_last4 || ''}) by ${cust.verified_by_user || 'ERO'}. <strong>KBA Waived per IRS Pub 1345.</strong>`;
            } else if (isTaxForm) {
                badge.style.background = 'rgba(245, 158, 11, 0.12)';
                badge.style.color = '#fbbf24';
                badge.style.border = '1px solid rgba(245, 158, 11, 0.35)';
                badge.innerHTML = `⚠️ <strong>IDENTITY UNVERIFIED:</strong> This customer has not been verified in office. IRS Form 8879 requires an In-Person Photo ID check or Remote KBA. <button type="button" onclick="openVerifyIdentityModal(${cust.id}, '${(cust.legal_name || '').replace(/'/g, "\\'")}')" style="margin-left: 6px; padding: 2px 8px; background: #f59e0b; color: #000; font-weight: 800; border: none; border-radius: 4px; cursor: pointer; font-size: 0.72rem;">Verify ID Now 🛡️</button>`;
            } else {
                badge.style.background = 'rgba(56, 189, 248, 0.1)';
                badge.style.color = '#7dd3fc';
                badge.style.border = '1px solid rgba(56, 189, 248, 0.25)';
                badge.innerHTML = `ℹ️ Standard document request. IRS Pub 1345 KBA not mandated.`;
            }
        }

        function onEsignTaxFormToggle() {
            const custId = document.getElementById('esignCustomerSelect')?.value;
            const cust = (allCustomersCache || []).find(c => String(c.id) === String(custId));
            updateEsignIdentityBadge(cust);
        }

        function onEsignCustomerChange() {
            const custId = document.getElementById('esignCustomerSelect')?.value;
            if (!custId) {
                updateEsignIdentityBadge(null);
                if (document.getElementById('esignSecondSignerGroup')) document.getElementById('esignSecondSignerGroup').style.display = 'none';
                return;
            }
            const cust = (allCustomersCache || []).find(c => String(c.id) === String(custId));
            if (cust) {
                if (document.getElementById('esignSignerNameInput')) {
                    document.getElementById('esignSignerNameInput').value = cust.primary_contact || cust.legal_name || '';
                }
                if (document.getElementById('esignSignerEmailInput')) {
                    document.getElementById('esignSignerEmailInput').value = cust.email || '';
                }
                if (document.getElementById('esignSecondSignerNameInput')) {
                    document.getElementById('esignSecondSignerNameInput').value = cust.second_signer_name || '';
                }
                if (document.getElementById('esignSecondSignerEmailInput')) {
                    document.getElementById('esignSecondSignerEmailInput').value = cust.second_signer_email || '';
                }

                // Automatic Document Preset Selection based on Customer Setup
                const presetSelect = document.getElementById('esignDocPresetSelect');
                if (presetSelect) {
                    const fType = String(cust.form_8879_type || '').toLowerCase();
                    if (fType.includes('8879j')) {
                        presetSelect.value = 'Form 8879J (Joint Account - Dual Signatures)';
                    } else if (fType.includes('8879-c') || (fType.includes('1120') && !fType.includes('1120-s')) || fType.includes('corp')) {
                        presetSelect.value = 'Form 8879-C (IRS e-File Corporate Tax Return)';
                    } else if (fType.includes('8879-s') || fType.includes('1120-s') || fType.includes('s-corp')) {
                        presetSelect.value = 'Form 8879-S (IRS e-File S-Corporation Tax Return)';
                    } else if (fType.includes('8879-pe') || fType.includes('1065') || fType.includes('partner')) {
                        presetSelect.value = 'Form 8879-PE (IRS e-File Partnership Tax Return)';
                    } else if (fType.includes('8879-f') || fType.includes('1041') || fType.includes('fiduc')) {
                        presetSelect.value = 'Form 8879-F (IRS e-File Fiduciary Tax Return)';
                    } else if (fType.includes('8879-eo') || fType.includes('990') || fType.includes('exempt')) {
                        presetSelect.value = 'Form 8879-EO (IRS e-File Exempt Organization Return)';
                    } else if (fType.includes('8878') || fType.includes('exten')) {
                        presetSelect.value = 'Form 8878 (IRS e-File Extension Authorization)';
                    } else {
                        presetSelect.value = 'Form 8879 (IRS e-File Signature Authorization)';
                    }
                    onEsignDocPresetChange();
                }
            }
            updateEsignIdentityBadge(cust);
        }

        function onEsignDocPresetChange() {
            const val = document.getElementById('esignDocPresetSelect')?.value;
            const nameInput = document.getElementById('esignDocNameInput');
            const fileGroup = document.getElementById('esignFileUploadGroup');
            const isTaxCheck = document.getElementById('esignIsTaxFormCheck');
            const secGroup = document.getElementById('esignSecondSignerGroup');
            const custId = document.getElementById('esignCustomerSelect')?.value;
            const cust = (allCustomersCache || []).find(c => String(c.id) === String(custId));

            if (val === 'Custom Document') {
                if (fileGroup) fileGroup.style.display = 'block';
                if (nameInput) nameInput.value = '';
                if (isTaxCheck) isTaxCheck.checked = false;
            } else {
                if (fileGroup) fileGroup.style.display = 'none';
                if (nameInput) nameInput.value = val;
                if (isTaxCheck) isTaxCheck.checked = val.includes('8879') || val.includes('8878') || val.includes('7216') || val.includes('Tax');
            }

            const isJoint = (cust && cust.customer_type === 'Joint Account') || (val && (val.includes('Joint') || val.includes('8879J'))) || (cust && Boolean(cust.second_signer_name)) || Boolean(document.getElementById('esignSecondSignerNameInput')?.value);
            if (secGroup) {
                secGroup.style.display = isJoint ? 'grid' : 'none';
            }

            onEsignTaxFormToggle();
        }

        async function openVerifyIdentityModal(customerId, customerName) {
            console.log("[VERIFY ID MODAL] Opening for customer:", customerId, customerName);
            const modal = document.getElementById('verifyIdentityModal');
            if (!modal) {
                console.error("[VERIFY ID MODAL] verifyIdentityModal element not found in DOM!");
                return;
            }

            modal.style.display = 'flex';
            modal.style.opacity = '1';
            modal.style.visibility = 'visible';
            modal.style.zIndex = '2147483647';
            if (modal.children && modal.children[0]) {
                modal.children[0].style.transform = 'scale(1)';
                modal.children[0].style.opacity = '1';
            }

            const setVal = (id, val) => {
                const el = document.getElementById(id);
                if (el) el.value = val !== undefined && val !== null ? val : '';
            };

            setVal('vIdCustomerId', customerId);
            setVal('vIdCustomerName', customerName || ('Customer #' + customerId));
            
            const revokeBtn = document.getElementById('vIdRevokeBtn');
            if (revokeBtn) revokeBtn.style.display = 'none';

            setVal('vIdType', "Driver's License");
            setVal('vIdStateIssuer', 'FL');
            setVal('vIdExpiration', '');
            setVal('vIdLast4', '');
            setVal('vIdNotes', '');

            setVal('vIdSecondCustomerName', '');
            setVal('vIdSecondType', "Driver's License");
            setVal('vIdSecondStateIssuer', '');
            setVal('vIdSecondExpiration', '');
            setVal('vIdSecondLast4', '');
            
            const secContainer = document.getElementById('vIdSecondSignerContainer');
            if (secContainer) secContainer.style.display = 'none';

            try {
                const res = await fetch(`/api/customers/${customerId}/identity-status`);
                if (res.ok) {
                    const data = await res.json();

                    const isJoint = data.customer_type === 'Joint Account' || Boolean(data.second_signer_name);
                    if (secContainer) secContainer.style.display = isJoint ? 'flex' : 'none';
                    if (isJoint) setVal('vIdSecondCustomerName', data.second_signer_name || 'Spouse / Second Signer');

                    if (data.identity_verified) {
                        setVal('vIdType', data.id_type || "Driver's License");
                        setVal('vIdStateIssuer', data.id_state_issuer || '');
                        setVal('vIdExpiration', data.id_expiration ? String(data.id_expiration).split('T')[0] : '');
                        setVal('vIdLast4', data.id_last4 || '');
                        setVal('vIdNotes', data.identity_notes || '');
                        if (revokeBtn) revokeBtn.style.display = 'inline-block';

                        if (isJoint) {
                            setVal('vIdSecondType', data.second_signer_id_type || "Driver's License");
                            setVal('vIdSecondStateIssuer', data.second_signer_id_state || '');
                            setVal('vIdSecondExpiration', data.second_signer_id_expiration ? String(data.second_signer_id_expiration).split('T')[0] : '');
                            setVal('vIdSecondLast4', data.second_signer_id_last4 || '');
                        }
                    }
                }
            } catch (err) {
                console.error('Error fetching customer identity status:', err);
            }
        }

        function closeVerifyIdentityModal() {
            const modal = document.getElementById('verifyIdentityModal');
            if (modal) {
                modal.style.opacity = '0';
                setTimeout(() => { modal.style.display = 'none'; }, 300);
            }
        }

        async function submitVerifyIdentity(evt) {
            evt.preventDefault();
            const customerId = document.getElementById('vIdCustomerId').value;
            const btn = document.getElementById('vIdSubmitBtn');
            if (btn) { btn.disabled = true; btn.innerText = 'Saving...'; }

            try {
                const formData = new FormData();
                formData.append('id_type', document.getElementById('vIdType').value);
                formData.append('id_state_issuer', document.getElementById('vIdStateIssuer').value);
                formData.append('id_expiration', document.getElementById('vIdExpiration').value || '');
                formData.append('id_last4', document.getElementById('vIdLast4').value);
                formData.append('second_signer_id_type', document.getElementById('vIdSecondType')?.value || '');
                formData.append('second_signer_id_state', document.getElementById('vIdSecondStateIssuer')?.value || '');
                formData.append('second_signer_id_expiration', document.getElementById('vIdSecondExpiration')?.value || '');
                formData.append('second_signer_id_last4', document.getElementById('vIdSecondLast4')?.value || '');
                formData.append('identity_notes', document.getElementById('vIdNotes').value || '');

                const res = await fetch(`/api/customers/${customerId}/verify-identity`, {
                    method: 'POST',
                    body: formData
                });

                if (res.ok) {
                    showCustomAlert('Success', 'In-Person photo ID verification recorded successfully! KBA waived for IRS tax forms.', 'success');
                    closeVerifyIdentityModal();
                    if (typeof fetchCustomerRecords === 'function') fetchCustomerRecords(true);
                } else {
                    const err = await res.json();
                    showCustomAlert('Error', 'Failed to save identity verification: ' + (err.detail || 'Unknown error'), 'error');
                }
            } catch (err) {
                console.error('Error saving identity verification:', err);
                showCustomAlert('Error', 'Error saving identity verification: ' + err.message, 'error');
            } finally {
                if (btn) { btn.disabled = false; btn.innerText = 'Save In-Person Verification'; }
            }
        }

        async function revokeCustomerIdentity() {
            const customerId = document.getElementById('vIdCustomerId').value;
            const confirmRevoke = await showCustomConfirm('Are you sure you want to revoke this customer\'s identity verification? IRS Form 8879 will require a new ID check or remote KBA.', 'Revoke Identity', 'Revoke Verification', 'Cancel');
            if (!confirmRevoke) return;

            try {
                const res = await fetch(`/api/customers/${customerId}/revoke-identity`, { method: 'POST' });
                if (res.ok) {
                    showCustomAlert('Revoked', 'Customer identity verification has been revoked.', 'info');
                    closeVerifyIdentityModal();
                    if (typeof fetchCustomerRecords === 'function') fetchCustomerRecords(true);
                } else {
                    const err = await res.json();
                    showCustomAlert('Error', 'Failed to revoke verification: ' + (err.detail || 'Unknown error'), 'error');
                }
            } catch (err) {
                console.error('Error revoking identity verification:', err);
                showCustomAlert('Error', 'Error revoking verification: ' + err.message, 'error');
            }
        }

        async function submitCreateEsignature(evt) {
            evt.preventDefault();
            const btn = document.getElementById('esignSubmitBtn');
            if (btn) { btn.disabled = true; btn.innerText = 'Sending...'; }

            try {
                const formData = new FormData();
                formData.append('customer_id', document.getElementById('esignCustomerSelect').value);
                formData.append('document_name', document.getElementById('esignDocNameInput').value);
                formData.append('signer_name', document.getElementById('esignSignerNameInput').value);
                formData.append('signer_email', document.getElementById('esignSignerEmailInput').value);
                formData.append('second_signer_name', document.getElementById('esignSecondSignerNameInput')?.value || '');
                formData.append('second_signer_email', document.getElementById('esignSecondSignerEmailInput')?.value || '');
                formData.append('template_id', document.getElementById('esignTemplateIdInput').value || '');
                formData.append('is_tax_form', document.getElementById('esignIsTaxFormCheck')?.checked || false);
                formData.append('send_email', document.getElementById('esignSendEmailCheck').checked);

                const pdfFile = document.getElementById('esignPdfFileInput')?.files[0];
                if (pdfFile) {
                    formData.append('pdf_file', pdfFile);
                }

                const res = await fetch('/api/esignature/send', {
                    method: 'POST',
                    body: formData
                });

                if (res.ok) {
                    showCustomAlert('Success', 'E-Signature request sent successfully via DocuSeal!', 'success');
                    closeCreateEsignatureModal();
                    fetchEsignatureRequests();
                } else {
                    const err = await res.json();
                    showCustomAlert('Error', 'Failed to send e-signature request: ' + (err.detail || 'Unknown error'), 'error');
                }
            } catch (err) {
                console.error('Error submitting e-signature request:', err);
                showCustomAlert('Error', 'Error sending signature request: ' + err.message, 'error');
            } finally {
                if (btn) { btn.disabled = false; btn.innerText = 'Send Signature Request'; }
            }
        }

        function openEsignatureSummaryModal(reqId, docTitle, custName, signerEmail, signedDate) {
            closeAllAppModals();
            const modal = document.getElementById('esignatureViewModal');
            const container = document.getElementById('esignViewModalContainer');
            const title = document.getElementById('esignViewModalTitle');

            if (!modal || !container) return;

            if (title) title.innerText = '✍️ E-Signature Summary — ' + (docTitle || 'Document');

            container.innerHTML = `
                <div style="padding: 24px; color: #f8fafc; font-family: 'Outfit', sans-serif;">
                    <div style="background: rgba(74, 222, 128, 0.1); border: 1px solid rgba(74, 222, 128, 0.3); border-radius: 12px; padding: 16px 20px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
                        <div>
                            <span style="background: #4ade80; color: #0f172a; padding: 3px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 800; text-transform: uppercase;">COMPLETED & VERIFIED</span>
                            <h3 style="margin: 8px 0 0 0; color: #fff; font-size: 1.1rem;">${escapeHtml(docTitle)}</h3>
                        </div>
                        <div style="text-align: right; font-size: 0.85rem; color: #94a3b8;">
                            <div>Signed Date: <strong style="color: #4ade80;">${signedDate || 'Completed'}</strong></div>
                        </div>
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px;">
                        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); padding: 14px 18px; border-radius: 10px;">
                            <div style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Customer</div>
                            <div style="font-size: 0.95rem; font-weight: 700; color: #38bdf8; margin-top: 4px;">${escapeHtml(custName || '-')}</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); padding: 14px 18px; border-radius: 10px;">
                            <div style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Signer Email</div>
                            <div style="font-size: 0.95rem; font-weight: 700; color: #cbd5e1; margin-top: 4px;">${escapeHtml(signerEmail || '-')}</div>
                        </div>
                    </div>

                    <div style="display: flex; gap: 12px; margin-bottom: 20px;">
                        <a href="/api/esignature/requests/${reqId}/pdf" target="_blank" style="flex: 1; text-align: center; padding: 12px; background: rgba(74, 222, 128, 0.2); border: 1px solid rgba(74, 222, 128, 0.4); color: #4ade80; border-radius: 10px; font-weight: 700; text-decoration: none; font-size: 0.88rem;">📄 Open Signed PDF Document</a>
                        <a href="/api/esignature/requests/${reqId}/audit-pdf" target="_blank" style="flex: 1; text-align: center; padding: 12px; background: rgba(168, 85, 247, 0.2); border: 1px solid rgba(168, 85, 247, 0.4); color: #c084fc; border-radius: 10px; font-weight: 700; text-decoration: none; font-size: 0.88rem;">📜 Open Legal Audit Certificate</a>
                    </div>

                    <div style="border-radius: 12px; overflow: hidden; border: 1px solid rgba(255,255,255,0.1); height: 420px; background: #141722;">
                        <iframe src="/api/esignature/requests/${reqId}/pdf" style="width: 100%; height: 100%; border: none;"></iframe>
                    </div>
                </div>
            `;

            modal.style.display = 'flex';
            setTimeout(() => { modal.style.opacity = '1'; }, 10);
        }

        function viewEsignatureRequest(embedSrc, docTitle) {
            closeAllAppModals();
            const modal = document.getElementById('esignatureViewModal');
            const container = document.getElementById('esignViewModalContainer');
            const title = document.getElementById('esignViewModalTitle');

            if (!modal || !container) return;

            if (title) title.innerText = '✍️ ' + (docTitle || 'DocuSeal E-Signature Document');

            if (embedSrc) {
                container.innerHTML = `<iframe src="${escapeHtml(embedSrc)}" style="width: 100%; height: 100%; border: none; border-radius: 12px;" allow="camera; microphone; clipboard-read; clipboard-write;"></iframe>`;
            } else {
                container.innerHTML = `<p style="color: #f87171;">No preview source available for this request.</p>`;
            }

            modal.style.display = 'flex';
            setTimeout(() => { modal.style.opacity = '1'; }, 10);
        }

        function closeEsignatureViewModal() {
            const modal = document.getElementById('esignatureViewModal');
            if (modal) {
                modal.style.opacity = '0';
                setTimeout(() => { modal.style.display = 'none'; }, 300);
            }
        }

        async function deleteEsignatureRequest(reqId) {
            const confirmed = await showCustomConfirm('Are you sure you want to delete this e-signature request?', 'Delete Request', 'Yes, Delete', 'Cancel');
            if (!confirmed) return;
            try {
                const res = await fetch(`/api/esignature/requests/${reqId}`, { method: 'DELETE' });
                if (res.ok) {
                    showCustomAlert('Success', 'E-Signature request deleted.', 'success');
                    fetchEsignatureRequests();
                } else {
                    showCustomAlert('Error', 'Could not delete request.', 'error');
                }
            } catch (err) {
                console.error('Error deleting request:', err);
            }
        }

        window.openSecurityModal = function openSecurityModal() {
            console.log("[SECURITY MODAL] Opening Account & Security Settings modal...");
            const modal = document.getElementById('securityModal');
            if (modal) {
                modal.style.setProperty('display', 'flex', 'important');
                modal.style.setProperty('opacity', '1', 'important');
                modal.style.setProperty('z-index', '2147483647', 'important');
                modal.style.setProperty('pointer-events', 'auto', 'important');
            } else {
                console.error("[SECURITY MODAL ERROR] Element #securityModal not found in DOM");
                alert("Account & Security Settings modal could not be found.");
            }
        };

        window.closeSecurityModal = function closeSecurityModal() {
            const modal = document.getElementById('securityModal');
            if (modal) {
                modal.style.display = 'none';
            }
        };
    