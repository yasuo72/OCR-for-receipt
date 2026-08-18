/**
 * FinSathi OCR Dashboard JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const dropzoneContent = document.getElementById('dropzoneContent');
    const previewArea = document.getElementById('previewArea');
    const imagePreview = document.getElementById('imagePreview');
    const removeFileBtn = document.getElementById('removeFileBtn');
    const scanBtn = document.getElementById('scanBtn');
    const scanBtnText = document.getElementById('scanBtnText');
    const fastModeToggle = document.getElementById('fastModeToggle');
    
    // Results elements
    const emptyResultState = document.getElementById('emptyResultState');
    const loadingState = document.getElementById('loadingState');
    const resultsContent = document.getElementById('resultsContent');
    const confidenceIndicator = document.getElementById('confidenceIndicator');
    const confidenceScore = document.getElementById('confidenceScore');
    
    const resMerchant = document.getElementById('resMerchant');
    const resDate = document.getElementById('resDate');
    const resTotal = document.getElementById('resTotal');
    const resTax = document.getElementById('resTax');
    const itemsTableBody = document.getElementById('itemsTableBody');
    const itemsCountBadge = document.getElementById('itemsCountBadge');
    const rawTextView = document.getElementById('rawTextView');
    const jsonCodeView = document.getElementById('jsonCodeView');
    
    // History elements
    const historyTableBody = document.getElementById('historyTableBody');
    const refreshHistoryBtn = document.getElementById('refreshHistoryBtn');
    const totalScannedCount = document.getElementById('totalScannedCount');
    
    // Sample chips
    const sampleChips = document.querySelectorAll('.sample-chip');
    const runAllSamplesBtn = document.getElementById('runAllSamplesBtn');

    let currentFile = null;

    // --- Drag and Drop Handlers ---
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt && dt.files && dt.files.length > 0) {
            handleFileSelect(dt.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    function handleFileSelect(file) {
        if (!file.type.startsWith('image/')) {
            alert('Please select an image file (PNG, JPG, JPEG, WEBP, etc.)');
            return;
        }

        currentFile = file;
        const reader = new FileReader();
        reader.onload = (event) => {
            imagePreview.src = event.target.result;
            dropzoneContent.classList.add('d-none');
            previewArea.classList.remove('d-none');
            scanBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    removeFileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        currentFile = null;
        fileInput.value = '';
        imagePreview.src = '';
        previewArea.classList.add('d-none');
        dropzoneContent.classList.remove('d-none');
        scanBtn.disabled = true;
    });

    // --- Scan Receipt Execution ---
    scanBtn.addEventListener('click', async () => {
        if (!currentFile) return;

        // UI Loading State
        scanBtn.disabled = true;
        scanBtnText.textContent = 'Processing OCR...';
        emptyResultState.classList.add('d-none');
        resultsContent.classList.add('d-none');
        loadingState.classList.remove('d-none');

        const formData = new FormData();
        formData.append('file', currentFile);
        if (fastModeToggle.checked) {
            formData.append('fast_mode', 'true');
        }

        try {
            const response = await fetch('/api/scan', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if (response.ok && data.success) {
                renderScanResults(data);
                refreshHistory();
            } else {
                alert(`Scan failed: ${data.message || data.error || 'Unknown error'}`);
                loadingState.classList.add('d-none');
                emptyResultState.classList.remove('d-none');
            }
        } catch (error) {
            console.error('Scan error:', error);
            alert(`Error processing receipt: ${error.message}`);
            loadingState.classList.add('d-none');
            emptyResultState.classList.remove('d-none');
        } finally {
            scanBtn.disabled = false;
            scanBtnText.textContent = 'Scan Receipt';
        }
    });

    function renderScanResults(data) {
        loadingState.classList.add('d-none');
        resultsContent.classList.remove('d-none');
        confidenceIndicator.classList.remove('d-none');

        const merchant = data.merchant || (data.data && data.data.merchant) || 'Unknown Merchant';
        const dateStr = data.date || (data.data && data.data.date) || '—';
        const total = (data.total !== null && data.total !== undefined) ? `₹${parseFloat(data.total).toFixed(2)}` : '₹0.00';
        const tax = (data.tax !== null && data.tax !== undefined) ? `₹${parseFloat(data.tax).toFixed(2)}` : '—';
        const confScore = (data.data && data.data.confidence_score) || (data.receipt && data.receipt.confidence) || 0.85;

        resMerchant.textContent = merchant;
        resDate.textContent = dateStr;
        resTotal.textContent = total;
        resTax.textContent = tax;

        // Confidence badge
        const pct = Math.round(parseFloat(confScore) * 100);
        confidenceScore.textContent = `${pct}% Match`;

        // Render Items Table
        const items = data.items || (data.data && data.data.items) || [];
        itemsCountBadge.textContent = items.length;
        itemsTableBody.innerHTML = '';

        if (items.length > 0) {
            items.forEach(item => {
                const tr = document.createElement('tr');
                const name = item.name || 'Item';
                const qty = item.quantity || 1;
                const price = (item.unit_price || item.price || 0).toFixed(2);
                const tot = (item.total_price || item.totalPrice || (qty * price)).toFixed(2);

                tr.innerHTML = `
                    <td class="font-bold">${escapeHtml(name)}</td>
                    <td>${qty}</td>
                    <td>₹${price}</td>
                    <td class="text-emerald font-bold">₹${tot}</td>
                `;
                itemsTableBody.appendChild(tr);
            });
        } else {
            itemsTableBody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center text-muted" style="padding: 1.5rem;">
                        No itemized list extracted. Full text available in "Raw OCR Text" tab.
                    </td>
                </tr>
            `;
        }

        // Raw Text & JSON
        rawTextView.textContent = data.raw_text || data.text || 'No text extracted';
        jsonCodeView.textContent = JSON.stringify(data, null, 2);
    }

    // --- Sample Chips Click ---
    sampleChips.forEach(chip => {
        chip.addEventListener('click', async () => {
            const sampleName = chip.getAttribute('data-sample');
            chip.style.opacity = '0.5';

            try {
                // UI Loading State
                scanBtn.disabled = true;
                scanBtnText.textContent = `Scanning ${sampleName}...`;
                emptyResultState.classList.add('d-none');
                resultsContent.classList.add('d-none');
                loadingState.classList.remove('d-none');

                // Trigger sample test or scan
                const response = await fetch(`/api/test`);
                const result = await response.json();

                if (result.success && result.results && result.results.length > 0) {
                    const match = result.results.find(r => r.sample_file === sampleName) || result.results[0];
                    if (match && match.data) {
                        renderScanResults({
                            merchant: match.data.merchant,
                            date: match.data.date,
                            total: match.data.total,
                            tax: match.data.tax,
                            items: match.data.items,
                            raw_text: match.data.raw_text,
                            data: match.data
                        });
                        refreshHistory();
                    }
                }
            } catch (err) {
                console.error('Error loading sample bill:', err);
                alert(`Error loading sample: ${err.message}`);
                loadingState.classList.add('d-none');
                emptyResultState.classList.remove('d-none');
            } finally {
                chip.style.opacity = '1';
                scanBtn.disabled = false;
                scanBtnText.textContent = 'Scan Receipt';
            }
        });
    });

    if (runAllSamplesBtn) {
        runAllSamplesBtn.addEventListener('click', async () => {
            runAllSamplesBtn.textContent = 'Running...';
            runAllSamplesBtn.disabled = true;
            try {
                const res = await fetch('/api/test');
                const data = await res.json();
                if (data.success) {
                    alert(`Batch test complete! Processed ${data.count} sample receipts successfully.`);
                    refreshHistory();
                    if (data.results && data.results.length > 0) {
                        const first = data.results[0];
                        if (first.data) {
                            renderScanResults({
                                merchant: first.data.merchant,
                                date: first.data.date,
                                total: first.data.total,
                                tax: first.data.tax,
                                items: first.data.items,
                                raw_text: first.data.raw_text,
                                data: first.data
                            });
                        }
                    }
                }
            } catch (err) {
                alert(`Test failed: ${err.message}`);
            } finally {
                runAllSamplesBtn.textContent = 'Run Batch Test';
                runAllSamplesBtn.disabled = false;
            }
        });
    }

    // --- Tab Switching ---
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

            btn.classList.add('active');
            const target = btn.getAttribute('data-tab');
            const pane = document.getElementById(target);
            if (pane) pane.classList.add('active');
        });
    });

    // --- Refresh History Table ---
    async function refreshHistory() {
        try {
            const res = await fetch('/api/receipts');
            const data = await res.json();

            if (data.success && data.receipts) {
                totalScannedCount.textContent = data.count || data.receipts.length;
                historyTableBody.innerHTML = '';

                if (data.receipts.length === 0) {
                    historyTableBody.innerHTML = `
                        <tr>
                            <td colspan="9" class="text-center text-muted" style="padding: 2.5rem 1rem;">
                                No receipts recorded in the database yet. Scan your first receipt above!
                            </td>
                        </tr>
                    `;
                    return;
                }

                data.receipts.forEach(r => {
                    const tr = document.createElement('tr');
                    tr.id = `receipt-row-${r.id}`;
                    const totalFormatted = (r.total !== null && r.total !== undefined) ? `₹${parseFloat(r.total).toFixed(2)}` : '—';
                    const conf = (r.confidence !== null && r.confidence !== undefined) ? parseFloat(r.confidence).toFixed(2) : '0.85';
                    const dateFormatted = r.created ? new Date(r.created).toLocaleDateString(undefined, {
                        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                    }) : '—';

                    tr.innerHTML = `
                        <td>#${r.id || '—'}</td>
                        <td class="font-bold">${escapeHtml(r.merchant || 'Unknown')}</td>
                        <td>${escapeHtml(r.date || '—')}</td>
                        <td class="text-emerald font-bold">${totalFormatted}</td>
                        <td><span class="confidence-pill">${conf}</span></td>
                        <td><span class="method-tag">${escapeHtml(r.scanner_method || 'ocr')}</span></td>
                        <td><span class="status-tag status-${r.status || 'processed'}">${r.status || 'processed'}</span></td>
                        <td class="text-muted">${dateFormatted}</td>
                        <td>
                            ${r.id ? `
                            <button class="btn-icon delete-receipt-btn" data-id="${r.id}" title="Delete Receipt">
                                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="3 6 5 6 21 6"></polyline>
                                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                </svg>
                            </button>` : '—'}
                        </td>
                    `;
                    historyTableBody.appendChild(tr);
                });

                attachDeleteHandlers();
            }
        } catch (e) {
            console.error('Failed to refresh history:', e);
        }
    }

    function attachDeleteHandlers() {
        document.querySelectorAll('.delete-receipt-btn').forEach(btn => {
            btn.onclick = async (e) => {
                e.stopPropagation();
                const id = btn.getAttribute('data-id');
                if (!confirm(`Are you sure you want to delete Receipt #${id}?`)) return;

                try {
                    const res = await fetch(`/api/receipts/${id}/`, { method: 'DELETE' });
                    const resData = await res.json();
                    if (resData.success) {
                        const row = document.getElementById(`receipt-row-${id}`);
                        if (row) row.remove();
                        refreshHistory();
                    } else {
                        alert('Failed to delete receipt');
                    }
                } catch (err) {
                    alert(`Error deleting receipt: ${err.message}`);
                }
            };
        });
    }

    refreshHistoryBtn.addEventListener('click', refreshHistory);
    attachDeleteHandlers();

    function escapeHtml(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }
});
