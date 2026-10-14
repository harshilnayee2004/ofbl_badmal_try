document.addEventListener('DOMContentLoaded', function () {
    checkForCurrentInspection();
    loadLots();
});

function checkForCurrentInspection() {
    let lotId = localStorage.getItem("box_inspection_lot_id");
    if (lotId) {
        window.location.href = `/user/inspect_box?lot_id=${lotId}`;
    }
}

function renderBoxInspectionStatus(status) {
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
        const response = await fetch('/lots/get_lots_for_inspection?inspection_type=box');
        if (!response.ok) throw new Error("Failed to fetch lots");
        const data = await response.json();

        if (data.object && data.object.length > 0) {
            lotsListBody.innerHTML = '';
            data.object.forEach(lot => {
                const createdDate = lot.created_at ? new Date(lot.created_at).toLocaleString('sv-SE', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).replace(',', '') : 'N/A';

                const tr = document.createElement('tr');
                tr.className = 'align-middle cursor-pointer';

                const boxSeq = lot.box_current_sequence || 0;
                const totalBoxes = lot.number_of_box_to_inspect || 0;
                const progressPercent = totalBoxes > 0 ? (boxSeq / totalBoxes) * 100 : 0;
                const progressBarClass = boxSeq === totalBoxes ? 'bg-success' : 'bg-primary';

                let actionHtml = '';
                if (lot.box_inspection_status === 'Pending' || lot.box_inspection_status === 'Inspecting') {
                    actionHtml = `
                        <form action="/user/inspect_box" method="GET" class="m-0">
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
                    <td>${renderBoxInspectionStatus(lot.box_inspection_status)}</td>
                    <td>
                        <strong>${boxSeq}/${totalBoxes}</strong>
                        <div class="progress mt-1" style="height: 5px;">
                            <div class="progress-bar ${progressBarClass}" role="progressbar" style="width: ${progressPercent}%" aria-valuenow="${boxSeq}" aria-valuemin="0" aria-valuemax="${totalBoxes}"></div>
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