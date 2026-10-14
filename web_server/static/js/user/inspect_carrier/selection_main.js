document.addEventListener('DOMContentLoaded', function () {
    checkForCurrentInspection();
    loadLots();
});

function checkForCurrentInspection() {
    let lotId = localStorage.getItem("carrier_inspection_lot_id");
    if (lotId) {
        window.location.href = `/user/inspect_carrier?lot_id=${lotId}`;
    }
}

function renderCarrierInspectionStatus(status) {
    if (status === "Pending") {
        return "<span class='badge bg-primary'>Pending</span>";
    } else if (status === "Inspecting") {
        return "<span class='badge bg-warning text-dark'>Inspecting</span>";
    } else if (status === "Completed") {
        return "<span class='badge bg-success'>Completed</span>";
    }
    return `<span class='badge bg-secondary'>${status}</span>`;
}

async function loadLots() {
    const lotsListBody = document.getElementById('lotsListBody');
    try {
        const response = await fetch('/lots/get_lots_for_inspection?inspection_type=carrier');
        if (!response.ok) throw new Error("Failed to fetch lots");
        const data = await response.json();

        if (data.object && data.object.length > 0) {
            lotsListBody.innerHTML = '';
            data.object.forEach(lot => {
                const createdDate = lot.created_at ? new Date(lot.created_at).toLocaleString('sv-SE', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).replace(',', '') : 'N/A';

                const tr = document.createElement('tr');
                tr.className = 'align-middle cursor-pointer';

                const carrierSeq = lot.carrier_current_sequence || 0;
                const totalCarriers = lot.number_of_carrier_to_inspect || lot.number_of_carrier || 0;
                const progressPercent = totalCarriers > 0 ? (carrierSeq / totalCarriers) * 100 : 0;
                const progressBarClass = (carrierSeq === totalCarriers && totalCarriers > 0) ? 'bg-success' : 'bg-primary';

                let actionHtml = '';
                if (lot.carrier_inspection_status === 'Pending' || lot.carrier_inspection_status === 'Inspecting') {
                    actionHtml = `
                        <form action="/user/inspect_carrier" method="GET" class="m-0">
                            <input type="hidden" name="lot_id" value="${lot.id}">
                            <button type="submit" class="btn btn-sm btn-primary rounded-pill px-3">${lot.carrier_inspection_status === 'Inspecting' ? 'Resume' : 'Start'}</button>
                        </form>
                    `;
                }

                tr.innerHTML = `
                    <td class="fw-bold py-3 ps-3">${lot.lot_number}</td>
                    <td>
                        <div class="d-flex flex-column">
                            <small><span class="text-muted fw-bold">Carrier:</span> ${lot.carrier_type || 'Carrier 6A/L'}</small>
                        </div>
                    </td>
                    <td>${createdDate}</td>
                    <td>${renderCarrierInspectionStatus(lot.carrier_inspection_status)}</td>
                    <td>
                        <strong>${carrierSeq}/${totalCarriers}</strong>
                        <div class="progress mt-1" style="height: 5px;">
                            <div class="progress-bar ${progressBarClass}" role="progressbar" style="width: ${progressPercent}%" aria-valuenow="${carrierSeq}" aria-valuemin="0" aria-valuemax="${totalCarriers}"></div>
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
