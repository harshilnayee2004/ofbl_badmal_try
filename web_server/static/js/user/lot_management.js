let allLots = [];

document.addEventListener('DOMContentLoaded', function () {
    loadLots();
});

function renderStatus(status) {
    if (!status) {
        return `<span class="badge bg-secondary">N/A</span>`;
    }
    const s = String(status).toUpperCase();
    if (s === "INSPECTING") {
        return `<span class="badge bg-warning text-dark"><span class="spinner-grow spinner-grow-sm me-1" style="width: 0.5rem; height: 0.5rem;" role="status"></span>INSPECTING</span>`;
    } else if (s === "PENDING" || s === "NOT ANSWERED") {
        return `<span class="badge bg-secondary">PENDING</span>`;
    } else if (s === "COMPLETED" || s === "PASSED") {
        return `<span class="badge bg-success">PASSED</span>`;
    } else if (s === "REJECTED") {
        return `<span class="badge bg-danger">REJECTED</span>`;
    } else {
        return `<span class="badge bg-dark">${status}</span>`;
    }
}

function loadLots() {
    fetch('/lots/')
        .then(response => response.json())
        .then(data => {
            allLots = data.object || [];
            renderLotsTable(allLots);
        })
        .catch(error => {
            console.error('Error loading lots:', error);
            const tbody = document.querySelector('#lotsTable tbody');
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="9" class="text-center text-danger py-4">Error loading lots from server</td></tr>';
            }
        });
}

function renderLotsTable(lots) {
    const tbody = document.querySelector('#lotsTable tbody');
    if (!tbody) return;

    tbody.innerHTML = '';
    const badge = document.getElementById('lotCountBadge');
    if (badge) {
        badge.textContent = `${lots.length} Lot${lots.length === 1 ? '' : 's'} Found`;
    }

    if (lots.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted py-4">No inspection lots registered yet. Click "+ Create New Ordnance Lot" to initialize one.</td></tr>';
        return;
    }

    lots.forEach((lot, index) => {
        const tr = document.createElement('tr');

        const createdDate = lot.created_at ? new Date(lot.created_at).toLocaleString('en-US', {
            month: 'short',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        }) : 'N/A';

        const isPrimer = lot.fuze_type === "Primer Electric 1A/L" || lot.carrier_type === "Carrier 6A/L";
        const totalUnits = (lot.total_quantity || lot.number_of_fuze || 0).toLocaleString();

        // Carrier Inspection
        let carrierProgress = '-';
        if (lot.number_of_carrier_to_inspect && lot.number_of_carrier_to_inspect > 0) {
            const currentCarrier = Math.max(0, (lot.carrier_current_sequence || 1) - 1);
            carrierProgress = `
                <div class="fw-bold">${currentCarrier}/${lot.number_of_carrier_to_inspect}</div>
                <div class="mt-1">${renderStatus(lot.carrier_acceptance_status || lot.carrier_inspection_status)}</div>
            `;
        } else if (isPrimer) {
            carrierProgress = `<span class="text-muted small">0 Sampled</span>`;
        } else {
            carrierProgress = `<span class="text-muted small">N/A</span>`;
        }

        // Box Inspection (H2A)
        const currentBox = Math.max(0, (lot.box_current_sequence || 1) - 1);
        const boxTarget = lot.number_of_box_to_inspect !== null ? lot.number_of_box_to_inspect : 0;
        const boxProgress = `
            <div class="fw-bold">${currentBox}/${boxTarget}</div>
            <div class="mt-1">${renderStatus(lot.box_acceptance_status || lot.box_inspection_status)}</div>
        `;

        // Primer / Fuze Inspection
        const currentFuze = Math.max(0, (lot.fuze_current_sequence || 1) - 1);
        const fuzeTarget = lot.number_of_fuze_to_inspect !== null ? lot.number_of_fuze_to_inspect : 0;
        const primerProgress = `
            <div class="fw-bold">${currentFuze}/${fuzeTarget}</div>
            <div class="mt-1">${renderStatus(lot.fuze_acceptance_status || lot.fuze_inspection_status)}</div>
        `;

        // Packaging tag
        let packagingTag = '';
        if (isPrimer) {
            packagingTag = `<div class="small text-muted">Carrier 6A/L &bull; H2A</div>`;
        } else {
            packagingTag = `<div class="small text-muted">${lot.box_type || 'Box'} &bull; ${lot.container_type || 'Container'}</div>`;
        }

        tr.innerHTML = `
            <td class="px-3 text-muted">${index + 1}</td>
            <td>
                <div class="fw-bold fs-6 text-dark">${lot.lot_number}</div>
            </td>
            <td>
                <span class="badge ${isPrimer ? 'bg-primary' : 'bg-secondary'}">${lot.fuze_type || 'Unknown'}</span>
                ${packagingTag}
            </td>
            <td class="text-end fw-bold">${totalUnits}</td>
            <td class="text-center">${carrierProgress}</td>
            <td class="text-center">${boxProgress}</td>
            <td class="text-center">${primerProgress}</td>
            <td class="text-center">${renderStatus(lot.acceptance_status || lot.inspection_status)}</td>
            <td class="text-end px-3">
                <div class="small fw-semibold text-dark">${createdDate}</div>
                <div class="small text-muted">${lot.created_by || ''}</div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function filterLotsTable() {
    const query = (document.getElementById('lotSearchInput')?.value || '').toLowerCase().trim();
    const status = (document.getElementById('statusFilter')?.value || '').toLowerCase().trim();

    const filtered = allLots.filter(lot => {
        const matchQuery = !query || 
            (lot.lot_number && lot.lot_number.toLowerCase().includes(query)) ||
            (lot.created_by && lot.created_by.toLowerCase().includes(query)) ||
            (lot.fuze_type && lot.fuze_type.toLowerCase().includes(query));

        const matchStatus = !status || 
            (lot.inspection_status && lot.inspection_status.toLowerCase() === status) ||
            (lot.acceptance_status && lot.acceptance_status.toLowerCase() === status);

        return matchQuery && matchStatus;
    });

    renderLotsTable(filtered);
}

function resetLotForm() {
    const form = document.getElementById('lotForm');
    if (form) {
        form.reset();
        form.classList.remove('was-validated');
    }
    const lotNumberInput = document.getElementById('lotNumber');
    if (lotNumberInput) lotNumberInput.value = '';
    const fuzeType = document.getElementById('fuzeType');
    if (fuzeType) fuzeType.value = "Primer Electric 1A/L";
    const carrierInput = document.getElementById('carrierSample');
    if (carrierInput) carrierInput.value = 20;
    const boxInput = document.getElementById('boxSample');
    if (boxInput) boxInput.value = 60;
    const primerInput = document.getElementById('primerSample');
    if (primerInput) primerInput.value = 315;
}

function saveLot() {
    const form = document.getElementById('lotForm');
    if (!form) return;

    if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return;
    }

    const lotNumberInput = document.getElementById('lotNumber');
    let lotNumber = lotNumberInput ? lotNumberInput.value.trim() : '';
    if (!lotNumber) return;
    if (!lotNumber.toUpperCase().startsWith('LOT-')) {
        lotNumber = 'LOT-' + lotNumber;
    }

    const fuzeType = document.getElementById('fuzeType')?.value || "Primer Electric 1A/L";
    const carrierSample = parseInt(document.getElementById('carrierSample')?.value, 10) || 20;
    const boxSample = parseInt(document.getElementById('boxSample')?.value, 10) || 60;
    const primerSample = parseInt(document.getElementById('primerSample')?.value, 10) || 315;

    const payload = {
        lot_number: lotNumber,
        fuze_type: fuzeType,
        carrier_type: "Carrier 6A/L",
        box_type: "H2A",
        number_of_carrier_to_inspect: carrierSample,
        number_of_box_to_inspect: boxSample,
        number_of_fuze_to_inspect: primerSample,
        number_of_carrier: carrierSample,
        number_of_box: boxSample,
        number_of_fuze: primerSample,
        total_quantity: primerSample
    };

    const saveBtn = document.getElementById('saveLotBtn');
    const saveSpinner = document.getElementById('saveLotSpinner');
    const saveText = document.getElementById('saveLotText');

    saveBtn.disabled = true;
    saveSpinner.classList.remove('d-none');
    if (saveText) saveText.textContent = "Creating...";

    fetch('/lots/create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
        .then(async response => {
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || err.message || 'Failed to create lot');
            }
            return response.json();
        })
        .then(data => {
            const modalEl = document.getElementById('lotModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();

            resetLotForm();
            loadLots();

            if (typeof showToast === 'function') {
                showToast(`Lot ${lotNumber} created successfully!`, 'success');
            } else {
                alert(`Lot ${lotNumber} created successfully!`);
            }
        })
        .catch(error => {
            console.error('Error creating lot:', error);
            if (typeof showToast === 'function') {
                showToast(error.message, 'error');
            } else {
                alert(error.message);
            }
        })
        .finally(() => {
            saveBtn.disabled = false;
            saveSpinner.classList.add('d-none');
            if (saveText) saveText.textContent = "Create Lot";
        });
}

