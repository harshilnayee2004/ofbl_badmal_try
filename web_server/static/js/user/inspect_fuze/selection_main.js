document.addEventListener('DOMContentLoaded', function () {
    checkForCurrentInspection();
    loadLots();
    // Assuming connectLotInspectionSocket is defined in fuze_inspection_sockets.js
    if (typeof connectLotInspectionSocket === 'function') {
        connectLotInspectionSocket();
    }
});

function checkForCurrentInspection() {
    let lotId = localStorage.getItem("fuze_inspection_lot_id");
    if (lotId) {
        window.location.href = `/user/inspect_fuze?lot_id=${lotId}`;
    }
}

function renderFuzeInspectionStatus(status) {
    if (status === "Pending") {
        return "<span class='badge bg-primary'>Pending</span>"
    } else if (status === "Inspecting") {
        return "<span class='badge bg-warning text-dark'>Inspecting</span>"
    } else if (status === "Completed") {
        return "<span class='badge bg-success'>Completed</span>"
    }
    return `<span class='badge bg-secondary'>${status}</span>`;
}

async function loadLots() {
    const lotsListBody = document.getElementById('lotsListBody');
    try {
        const response = await fetch('/lots/get_lots_for_inspection?inspection_type=fuze');
        if (!response.ok) throw new Error("Failed to fetch lots");
        const data = await response.json();

        if (data.object && data.object.length > 0) {
            lotsListBody.innerHTML = ''; // clear loading
            data.object.forEach(lot => {
                const createdDate = lot.created_at ? new Date(lot.created_at).toLocaleString('sv-SE', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).replace(',', '') : 'N/A';

                const tr = document.createElement('tr');
                tr.className = 'cursor-pointer align-middle';
                tr.addEventListener('click', () => {
                    const radioBtn = document.getElementById(`lotRadio_${lot.id}`);
                    if (radioBtn) {
                        radioBtn.checked = true;
                        radioBtn.dispatchEvent(new Event('change'));
                    }
                });

                if (lot.fuze_inspection_status === 'Pending' || lot.fuze_inspection_status === 'Inspecting') {
                    actionHtml = `
                        <form action="/user/inspect_fuze" method="GET" class="m-0">
                            <input type="hidden" name="lot_id" value="${lot.id}">
                            <button type="submit" class="btn btn-sm btn-primary rounded-pill px-3">Start</button>
                        </form>
                    `;
                }

                tr.innerHTML = `
                    <td class="fw-bold py-3">${lot.lot_number}</td>
                    <td>
                        <div class="d-flex flex-column">
                            <small><span class="text-muted fw-bold">Box:</span> ${lot.box_type || 'N/A'}</small>
                            <small><span class="text-muted fw-bold">Primer:</span> ${lot.fuze_type || 'N/A'}</small>
                        </div>
                    </td>
                    <td>${createdDate}</td>
                    <td>${renderFuzeInspectionStatus(lot.fuze_inspection_status)}</td>
                    <td>
                        <strong>${lot.fuze_current_sequence}/${lot.number_of_fuze_to_inspect}</strong>
                        <div class="progress mt-1" style="height: 5px;">
                            <div class="progress-bar ${lot.fuze_current_sequence === lot.number_of_fuze_to_inspect ? 'bg-success' : 'bg-primary'}" 
                                 role="progressbar" 
                                 style="width: ${(lot.number_of_fuze_to_inspect > 0 ? (lot.fuze_current_sequence / lot.number_of_fuze_to_inspect) * 100 : 0)}%" 
                                 aria-valuenow="${lot.fuze_current_sequence}" 
                                 aria-valuemin="0" 
                                 aria-valuemax="${lot.number_of_fuze_to_inspect}">
                            </div>
                        </div>
                    </td>
                    <td>
                        <div class="d-flex justify-content-center m-0">
                            ${actionHtml}
                        </div>
                    </td>
                `;
                lotsListBody.appendChild(tr);
            });
        } else {
            lotsListBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted py-5">
                        <span class="material-symbols-outlined mb-2" style="font-size: 32px; opacity: 0.5;">info</span><br>
                        No lots currently available for inspection.
                    </td>
                </tr>`;
        }
    } catch (error) {
        console.error("Error loading lots:", error);
        lotsListBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-danger py-5">
                    <span class="material-symbols-outlined mb-2" style="font-size: 32px;">error</span><br>
                    Error loading lots.
                </td>
            </tr>`;
    }
}