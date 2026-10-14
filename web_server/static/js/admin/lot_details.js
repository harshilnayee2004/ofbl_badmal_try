document.addEventListener('DOMContentLoaded', function () {
    if (typeof currentLotId !== 'undefined') {
        fetchLotDetails(currentLotId);
        fetchBoxes(currentLotId);
        fetchFuzes(currentLotId);
    }
});

async function fetchLotDetails(lotId) {
    try {
        // Fetch lot info
        const response = await fetch(`/lots/get_lot_by_id/${lotId}`);
        const data = await response.json();

        if (data.status) {
            renderLotDetails(data.object);
        } else {
            document.getElementById('lotInfoContainer').innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
        }
    } catch (error) {
        console.error('Error fetching lot details:', error);
        document.getElementById('lotInfoContainer').innerHTML = `<div class="alert alert-danger">Failed to load lot details.</div>`;
    }
}

function renderLotDetails(lot) {
    const container = document.getElementById('lotInfoContainer');

    let statusBadgeClass = 'secondary';
    if (lot.inspection_status === 'Completed') statusBadgeClass = 'success';
    if (lot.inspection_status === 'Inspecting') statusBadgeClass = 'warning';
    if (lot.inspection_status === 'Pending') statusBadgeClass = 'info';

    let boxInspected = Math.max(0, lot.box_current_sequence - 1);
    if (lot.box_acceptance_status !== null || lot.inspection_status === 'Completed') boxInspected = lot.number_of_box_to_inspect;

    let fuzeInspected = Math.max(0, lot.fuze_current_sequence - 1);
    if (lot.fuze_acceptance_status !== null || lot.inspection_status === 'Completed') fuzeInspected = lot.number_of_fuze_to_inspect;

    container.innerHTML = `
        <div class="row g-3">
            <div class="col-md-6 col-lg-3">
                <div class="border rounded p-3 bg-light h-100">
                    <div class="text-muted small mb-1">Lot Number</div>
                    <div class="fw-bold fs-5">${lot.lot_number || '-'}</div>
                </div>
            </div>
            <div class="col-md-6 col-lg-3">
                <div class="border rounded p-3 bg-light h-100">
                    <div class="text-muted small mb-1">Lot Status</div>
                    <div class="mb-1">Lot: <span class="badge bg-${statusBadgeClass}">${lot.inspection_status}</span></div>
                    <div class="mb-1">Boxes: <span class="badge bg-${lot.box_inspection_status === 'Completed' ? 'success' : (lot.box_inspection_status === 'Inspecting' ? 'warning' : 'primary')}">${lot.box_inspection_status}</span></div>
                    <div>Primers: <span class="badge bg-${lot.fuze_inspection_status === 'Completed' ? 'success' : (lot.fuze_inspection_status === 'Inspecting' ? 'warning' : 'primary')}">${lot.fuze_inspection_status}</span></div>
                </div>
            </div>
            <div class="col-md-6 col-lg-3">
                <div class="border rounded p-3 bg-light h-100">
                    <div class="text-muted small mb-1">Created At</div>
                    <div class="fw-bold">${lot.created_at || '-'}</div>
                </div>
            </div>
            <div class="col-md-6 col-lg-3">
                <div class="border rounded p-3 bg-light h-100">
                    <div class="text-muted small mb-1">Created By</div>
                    <div class="fw-bold">${lot.created_by || '-'}</div>
                </div>
            </div>

            <!-- Box Info -->
            <div class="col-md-6 col-lg-3">
                <div class="border rounded p-3 bg-light h-100">
                    <div class="text-muted small mb-1"><span class="material-symbols-outlined align-text-bottom fs-6 me-1">box</span>Box Type & Count</div>
                    <div class="small">Type: <strong>${lot.box_type || '-'}</strong></div>
                    <div class="small">Total: <strong>${lot.number_of_box !== null ? lot.number_of_box : '-'}</strong></div>
                    <div class="small">Confirmed: <strong>${lot.box_count_confirmation !== null ? lot.box_count_confirmation : '-'}</strong></div>
                </div>
            </div>
            <div class="col-md-6 col-lg-3">
                <div class="border rounded p-3 bg-light h-100">
                    <div class="text-muted small mb-1"><span class="material-symbols-outlined align-text-bottom fs-6 me-1">fact_check</span>Box Inspection details</div>
                    <div class="small mb-1">Inspected: <strong>${lot.box_current_sequence - 1} / ${lot.number_of_box_to_inspect !== null ? lot.number_of_box_to_inspect : '-'}</strong></div>
                    <div class="progress mb-2" style="height: 5px;">
                        <div class="progress-bar ${lot.box_current_sequence - 1 === lot.number_of_box_to_inspect ? 'bg-success' : 'bg-primary'}" role="progressbar" style="width: ${(lot.number_of_box_to_inspect > 0 ? ((lot.box_current_sequence - 1) / lot.number_of_box_to_inspect) * 100 : 0)}%;" aria-valuenow="${lot.box_current_sequence - 1}" aria-valuemin="0" aria-valuemax="${lot.number_of_box_to_inspect}"></div>
                    </div>
                    <div class="small">Acceptance: <span class="badge bg-${lot.box_acceptance_status === 'Passed' ? 'success' : (lot.box_acceptance_status === 'Rejected' ? 'danger' : 'secondary')}">${lot.box_acceptance_status === 'Passed' ? 'Passed' : (lot.box_acceptance_status === 'Rejected' ? 'Rejected' : 'Not Answered')}</span></div>
                </div>
            </div>

            <!-- Primer Info -->
            <div class="col-md-6 col-lg-3">
                <div class="border rounded p-3 bg-light h-100">
                    <div class="text-muted small mb-1"><span class="material-symbols-outlined align-text-bottom fs-6 me-1">military_tech</span>Primer Type & Count</div>
                    <div class="small text-truncate" title="${lot.fuze_type || '-'}">Type: <strong>${lot.fuze_type || '-'}</strong></div>
                    <div class="small">Total: <strong>${lot.number_of_fuze !== null ? lot.number_of_fuze : '-'}</strong></div>
                    <div class="small">Confirmed: <strong>${lot.fuze_count_confirmation !== null ? lot.fuze_count_confirmation : '-'}</strong></div>
                </div>
            </div>
            <div class="col-md-6 col-lg-3">
                <div class="border rounded p-3 bg-light h-100">
                    <div class="text-muted small mb-1"><span class="material-symbols-outlined align-text-bottom fs-6 me-1">fact_check</span>Primer Inspection Details</div>
                    <div class="small mb-1">Inspected: <strong>${lot.fuze_current_sequence - 1} / ${lot.number_of_fuze_to_inspect !== null ? lot.number_of_fuze_to_inspect : '-'}</strong></div>
                    <div class="progress mb-2" style="height: 5px;">
                        <div class="progress-bar ${lot.fuze_current_sequence - 1 === lot.number_of_fuze_to_inspect ? 'bg-success' : 'bg-primary'}" role="progressbar" style="width: ${(lot.number_of_fuze_to_inspect > 0 ? ((lot.fuze_current_sequence - 1) / lot.number_of_fuze_to_inspect) * 100 : 0)}%;" aria-valuenow="${lot.fuze_current_sequence - 1}" aria-valuemin="0" aria-valuemax="${lot.number_of_fuze_to_inspect}"></div>
                    </div>
                    <div class="small">Acceptance: <span class="badge bg-${lot.fuze_acceptance_status === 'Passed' ? 'success' : (lot.fuze_acceptance_status === 'Rejected' ? 'danger' : 'secondary')}">${lot.fuze_acceptance_status === 'Passed' ? 'Passed' : (lot.fuze_acceptance_status === 'Rejected' ? 'Rejected' : 'Not Answered')}</span></div>
                </div>
            </div>
            
            ${lot.inspection_status === 'Completed' ? `
            <div class="col-12 mt-3">
                <div class="border border-primary rounded p-3 bg-white d-flex flex-wrap justify-content-between align-items-center shadow-sm">
                    <div class="mb-2 mb-md-0">
                        <div class="text-dark fs-5 fw-bold"><span class="material-symbols-outlined align-text-bottom fs-4 me-2 text-primary">verified</span>Final Lot Acceptance Status</div>
                        <div class="small text-muted">Set the final acceptance status for this lot now that all inspections are complete.</div>
                    </div>
                    <div class="d-flex align-items-center gap-3">
                        <select class="form-select form-select-lg fw-bold w-auto" id="lotAcceptanceSelect" onchange="updateLotAcceptanceStatus(${lot.lot_id}, this.value)">
                            <option value="Pending" ${lot.acceptance_status === 'Pending' ? 'selected' : ''}>Pending</option>
                            <option value="Passed" class="text-success" ${lot.acceptance_status === 'Passed' ? 'selected' : ''}>Passed</option>
                            <option value="Rejected" class="text-danger" ${lot.acceptance_status === 'Rejected' ? 'selected' : ''}>Rejected</option>
                        </select>
                        <button id="lotZipDownloadBtn" class="btn btn-primary shadow-sm d-flex align-items-center" onclick="downloadLotZipReport(${lot.lot_id}, '${lot.lot_number}')">
                            <span class="material-symbols-outlined align-text-bottom me-2">folder_zip</span> Download Full Report (ZIP)
                        </button>
                    </div>
                </div>
            </div>
            ` : `
            <div class="col-12 mt-3">
                <div class="border rounded p-3 bg-light d-flex justify-content-between align-items-center text-muted">
                    <div>
                        <div class="small fw-bold"><span class="material-symbols-outlined align-text-bottom fs-6 me-1">verified</span>Final Lot Acceptance Status</div>
                        <div class="small">Pending completion of carrier, box and primer inspections.</div>
                    </div>
                    <span class="badge bg-secondary fs-6">Pending</span>
                </div>
            </div>
            `}

        </div>
    `;
}

async function updateLotAcceptanceStatus(lotId, status) {
    try {
        const response = await fetch(`/lots/update_acceptance_status/${lotId}?status=${encodeURIComponent(status)}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();

        if (data.status) {
            if (typeof showToast === 'function') {
                showToast('Lot acceptance status updated successfully!', 'success');
            } else {
                alert('Lot acceptance status updated successfully!');
            }
        } else {
            alert('Error updating status: ' + data.message);
        }
    } catch (err) {
        console.error('Error updating lot acceptance status:', err);
        alert('Failed to update status.');
    }
}

async function fetchBoxes(lotId) {
    try {
        const response = await fetch(`/lots/get_box_by_lot_id/${lotId}`);
        const data = await response.json();

        if (data.status) {
            renderBoxAccordion(data.object);
        } else {
            document.getElementById('boxAccordion').innerHTML = `<div class="alert alert-danger"> ${data.message}</div> `;
        }
    } catch (error) {
        console.error('Error fetching boxes:', error);
        document.getElementById('boxAccordion').innerHTML = `<div class="alert alert-danger"> Failed to load boxes.</div> `;
    }
}

function renderBoxAccordion(boxes) {
    const boxAccordion = document.getElementById('boxAccordion');

    if (!boxes || boxes.length === 0) {
        boxAccordion.innerHTML = `<div class="p-3 text-muted text-center border rounded"> No box details found or available yet.</div> `;
        return;
    }

    boxes.sort((a, b) => a.sequence_number - b.sequence_number);

    let boxHtml = '';

    boxes.forEach((box, index) => {

        let badgeColor = box.box_inspection_status === 'Completed' ? 'success' : (box.box_inspection_status === 'Pending' ? 'primary' : 'warning');

        let carouselId = `boxCarousel${box.id}`;
        let mediaHtml = '';
        if (box.media_files && box.media_files.length > 0) {
            let indicators = '';
            let items = '';
            let videoHtml = '';
            let imageIdx = 0;

            box.media_files.forEach((fileUrl) => {
                let isVideo = fileUrl.match(/\.(mp4|avi|mov|mkv|webm)(?:[\?#].*)?$/i) || fileUrl.toLowerCase().includes('.mp4') || fileUrl.toLowerCase().includes('.avi');

                if (isVideo) {
                    videoHtml += `
        <div class="mt-4">
                        <h6 class="text-muted small fw-bold mb-2 text-uppercase d-flex align-items-center"><span class="material-symbols-outlined fs-5 me-1">videocam</span> Video Recording</h6>
                        <video class="d-block w-100 rounded shadow-sm border bg-dark" style="max-height: 350px; object-fit: contain;" controls preload="metadata"><source src="${fileUrl}"></video>
                    </div> `;
                } else {
                    let activeClass = imageIdx === 0 ? 'active' : '';
                    indicators += `<button type="button" data-bs-target="#${carouselId}" data-bs-slide-to="${imageIdx}" class="${activeClass}" aria-current="${imageIdx === 0 ? 'true' : 'false'}" aria-label="Slide ${imageIdx + 1}"></button> `;
                    items += `
            <div class="carousel-item ${activeClass} bg-dark rounded" style="position: relative;">
                <img src="${fileUrl}" class="d-block w-100 rounded" style="max-height: 300px; object-fit: contain;" alt="Box Image">
                </div>`;
                    imageIdx++;
                }
            });

            if (imageIdx > 0) {
                let controlsHtml = '';
                if (imageIdx > 1) {
                    controlsHtml = `
                    <button class="carousel-control-prev" type="button" data-bs-target="#${carouselId}" data-bs-slide="prev">
                        <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                        <span class="visually-hidden">Previous</span>
                    </button>
            <button class="carousel-control-next" type="button" data-bs-target="#${carouselId}" data-bs-slide="next">
                <span class="carousel-control-next-icon" aria-hidden="true"></span>
                <span class="visually-hidden">Next</span>
            </button>
        `;
                }

                mediaHtml = `
            <div id="${carouselId}" class="carousel slide border rounded shadow-sm" data-bs-ride="carousel">
                    <div class="carousel-indicators">
                        ${indicators}
                    </div>
                    <div class="carousel-inner rounded">
                        ${items}
                    </div>
                    ${controlsHtml}
                </div>
            ${videoHtml}
        `;
            } else {
                mediaHtml = `
            <div class="bg-light d-flex align-items-center justify-content-center rounded text-muted" style="min-height: 200px; border: 2px dashed #dee2e6;">
                <div class="text-center">
                    <span class="material-symbols-outlined fs-2 d-block mb-2">image_not_supported</span>
                    <span>No images available</span>
                </div>
                </div>
            ${videoHtml}
        `;
            }
        } else {
            mediaHtml = `
            <div class="bg-light d-flex align-items-center justify-content-center rounded text-muted h-100" style="min-height: 200px; border: 2px dashed #dee2e6;">
                <div class="text-center">
                    <span class="material-symbols-outlined fs-2 d-block mb-2">image_not_supported</span>
                    <span>No media available</span>
                </div>
            </div> `;
        }

        let inspectionHtml = '';
        if (box.inspection && Object.keys(box.inspection).length > 0) {
            inspectionHtml = '<ul class="list-group list-group-flush border rounded mt-2">';
            for (const [key, value] of Object.entries(box.inspection)) {
                if (key === 'id') continue;
                let prettyKey = key.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase());
                let icon = '';
                if (value === true) {
                    icon = '<span class="material-symbols-outlined text-success align-text-bottom fs-5">check_circle</span>';
                } else if (value === false) {
                    icon = '<span class="material-symbols-outlined text-danger align-text-bottom fs-5">cancel</span>';
                } else {
                    icon = '<span class="text-muted">N/A</span>';
                }
                inspectionHtml += `
            <li class="list-group-item d-flex justify-content-between align-items-center py-1 bg-transparent">
                    <span class="text-secondary small">${prettyKey}</span>
                    <span>${icon}</span>
                </li> `;
            }
            inspectionHtml += '</ul>';
        } else {
            inspectionHtml = '<div class="text-muted mt-2 fst-italic small">No inspection checklist data</div>';
        }

        let startTime = box.start_time ? new Date(box.start_time).toLocaleString() : 'N/A';
        let endTime = box.end_time ? new Date(box.end_time).toLocaleString() : 'N/A';

        boxHtml += `
            <div class="accordion-item shadow-sm mb-2 border rounded">
            <h2 class="accordion-header" id="flush-headingBox${box.id}">
                <button class="accordion-button collapsed rounded" type="button" data-bs-toggle="collapse" data-bs-target="#flush-collapseBox${box.id}" aria-expanded="false" aria-controls="flush-collapseBox${box.id}">
                    <div class="d-flex justify-content-between align-items-center w-100 me-3">
                        <span class="fw-bold d-flex align-items-center"><span class="material-symbols-outlined align-text-bottom me-2 text-primary">box</span> Box Sequence #${box.sequence_number} | Box Number: ${box.box_number || 'N/A'} | Acceptance Status:  <span class="ms-2 badge bg-${box.acceptance_status === true ? 'success' : (box.acceptance_status === false ? 'danger' : 'secondary')}">${box.acceptance_status === true ? 'Passed' : (box.acceptance_status === false ? 'Rejected' : 'Not Answered')}</span></span>
                        <div class="d-flex align-items-center gap-2">
                            <span class="badge bg-${badgeColor}">${box.box_inspection_status}</span>
                        </div>
                    </div>
                </button>
            </h2>
            <div id="flush-collapseBox${box.id}" class="accordion-collapse collapse" aria-labelledby="flush-headingBox${box.id}" data-bs-parent="#boxAccordion">
                <div class="accordion-body bg-light">
                    <div class="row g-4">
                        <div class="col-lg-6">
                            <h6 class="text-muted small fw-bold mb-3 text-uppercase">Media Gallery</h6>
                            ${mediaHtml}
                        </div>
                        <div class="col-lg-6">
                            <h6 class="text-muted small fw-bold mb-3 text-uppercase">Inspection Details</h6>
                            <div class="row g-2 mb-3">
                                <div class="col-sm-6">
                                    <div class="bg-white p-2 rounded border">
                                        <div class="text-muted" style="font-size: 0.75rem;">Box Type</div>
                                        <div class="fw-bold">${box.box_type || '-'}</div>
                                    </div>
                                </div>
                                <div class="col-sm-6">
                                    <div class="bg-white p-2 rounded border">
                                        <div class="text-muted" style="font-size: 0.75rem;">Duration</div>
                                        <div class="small text-truncate" title="Start: ${startTime}&#10;End: ${endTime}">
                                            ${startTime.split(',')[1] || startTime} - ${endTime.split(',')[1] || endTime}
                                        </div>
                                    </div>
                                </div>
                                <div class="col-sm-12">
                                    <div class="bg-white p-2 rounded border">
                                        <div class="text-muted" style="font-size: 0.75rem;">Acceptance Status</div>
                                        <div class="mt-1"><span class="badge bg-${box.acceptance_status === true ? 'success' : (box.acceptance_status === false ? 'danger' : 'secondary')}">${box.acceptance_status === true ? 'Passed' : (box.acceptance_status === false ? 'Rejected' : 'Not Answered')}</span></div>
                                    </div>
                                </div>
                            </div>
                            <h6 class="text-muted small fw-bold mb-2">Checklist Parameters</h6>
                            ${inspectionHtml}
                            ${box.box_inspection_status === "Completed" ? `<div class="mt-2 d-flex justify-content-end gap-2">
                                <button class="btn btn-sm btn-outline-primary shadow-sm" style="font-size: 0.75rem" onclick="event.stopPropagation(); downloadBoxReport(${box.id}, '${box.box_number || 'N/A'}')"><span class="material-symbols-outlined align-text-bottom fs-6 me-1">table_chart</span> Excel</button>
                                <button class="btn btn-sm btn-outline-primary shadow-sm" style="font-size: 0.75rem" onclick="event.stopPropagation(); downloadBoxPdfReport(${box.id}, '${box.box_number || 'N/A'}')"><span class="material-symbols-outlined align-text-bottom fs-6 me-1">picture_as_pdf</span> PDF</button>
                            </div>` : ''}
                        </div>
                    </div>
                </div>
            </div>
        </div>
            `;
    });

    boxAccordion.innerHTML = boxHtml;
}

async function fetchFuzes(lotId) {
    try {
        const response = await fetch(`/lots/get_fuze_by_lot_id/${lotId}`);
        const data = await response.json();

        if (data.status) {
            renderFuzeAccordion(data.object);
        } else {
            document.getElementById('fuzeAccordion').innerHTML = `<div class="alert alert-danger"> ${data.message}</div> `;
        }
    } catch (error) {
        console.error('Error fetching fuzes:', error);
        document.getElementById('fuzeAccordion').innerHTML = `<div class="alert alert-danger"> Failed to load fuzes.</div> `;
    }
}

function renderFuzeAccordion(fuzes) {
    const fuzeAccordion = document.getElementById('fuzeAccordion');

    if (!fuzes || fuzes.length === 0) {
        fuzeAccordion.innerHTML = `<div class="p-3 text-muted text-center border rounded"> No primer details found or available yet.</div> `;
        return;
    }

    fuzes.sort((a, b) => a.sequence_number - b.sequence_number);

    let fuzeHtml = '';

    fuzes.forEach((fuze) => {
        let badgeColor = fuze.fuze_inspection_status === 'Completed' ? 'success' : (fuze.fuze_inspection_status === 'Pending' ? 'primary' : 'warning');

        let carouselId = `fuzeCarousel${fuze.id}`;
        let mediaHtml = '';
        if (fuze.media_files && fuze.media_files.length > 0) {
            let indicators = '';
            let items = '';
            let videoHtml = '';
            let imageIdx = 0;

            fuze.media_files.forEach((fileUrl) => {
                let isVideo = fileUrl.match(/\.(mp4|avi|mov|mkv|webm)(?:[\?#].*)?$/i) || fileUrl.toLowerCase().includes('.mp4') || fileUrl.toLowerCase().includes('.avi');

                if (isVideo) {
                    videoHtml += `
            <div class="mt-4">
                        <h6 class="text-muted small fw-bold mb-2 text-uppercase d-flex align-items-center"><span class="material-symbols-outlined fs-5 me-1">videocam</span> Video Recording</h6>
                        <video class="d-block w-100 rounded shadow-sm border bg-dark" style="max-height: 350px; object-fit: contain;" controls preload="metadata"><source src="${fileUrl}"></video>
                    </div> `;
                } else {
                    let activeClass = imageIdx === 0 ? 'active' : '';
                    indicators += `<button type="button" data-bs-target="#${carouselId}" data-bs-slide-to="${imageIdx}" class="${activeClass}" aria-current="${imageIdx === 0 ? 'true' : 'false'}" aria-label="Slide ${imageIdx + 1}"></button> `;
                    items += `
            <div class="carousel-item ${activeClass} bg-dark rounded" style="position: relative;">
                <img src="${fileUrl}" class="d-block w-100 rounded" style="max-height: 300px; object-fit: contain;" alt="Primer Image">
                </div>`;
                    imageIdx++;
                }
            });

            if (imageIdx > 0) {
                let controlsHtml = '';
                if (imageIdx > 1) {
                    controlsHtml = `
                    <button class="carousel-control-prev" type="button" data-bs-target="#${carouselId}" data-bs-slide="prev">
                        <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                        <span class="visually-hidden">Previous</span>
                    </button>
            <button class="carousel-control-next" type="button" data-bs-target="#${carouselId}" data-bs-slide="next">
                <span class="carousel-control-next-icon" aria-hidden="true"></span>
                <span class="visually-hidden">Next</span>
            </button>
        `;
                }

                mediaHtml = `
            <div id="${carouselId}" class="carousel slide border rounded shadow-sm" data-bs-ride="carousel">
                    <div class="carousel-indicators">
                        ${indicators}
                    </div>
                    <div class="carousel-inner rounded">
                        ${items}
                    </div>
                    ${controlsHtml}
                </div>
            ${videoHtml}
        `;
            } else {
                mediaHtml = `
            <div class="bg-light d-flex align-items-center justify-content-center rounded text-muted" style="min-height: 200px; border: 2px dashed #dee2e6;">
                <div class="text-center">
                    <span class="material-symbols-outlined fs-2 d-block mb-2">image_not_supported</span>
                    <span>No images available</span>
                </div>
                </div>
            ${videoHtml}
        `;
            }
        } else {
            mediaHtml = `
            <div class="bg-light d-flex align-items-center justify-content-center rounded text-muted h-100" style="min-height: 200px; border: 2px dashed #dee2e6;">
                <div class="text-center">
                    <span class="material-symbols-outlined fs-2 d-block mb-2">image_not_supported</span>
                    <span>No media available</span>
                </div>
            </div> `;
        }

        let inspectionHtml = '';
        if (fuze.inspection && Object.keys(fuze.inspection).length > 0) {
            inspectionHtml = '<ul class="list-group list-group-flush border rounded mt-2">';
            for (const [key, value] of Object.entries(fuze.inspection)) {
                if (key === 'id') continue;
                let prettyKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                let icon = '';
                if (value === true) {
                    icon = '<span class="material-symbols-outlined text-success align-text-bottom fs-5">check_circle</span>';
                } else if (value === false) {
                    icon = '<span class="material-symbols-outlined text-danger align-text-bottom fs-5">cancel</span>';
                } else {
                    icon = '<span class="text-muted">N/A</span>';
                }
                inspectionHtml += `
            <li class="list-group-item d-flex justify-content-between align-items-center py-1 bg-transparent">
                    <span class="text-secondary small">${prettyKey}</span>
                    <span>${icon}</span>
                </li> `;
            }
            inspectionHtml += '</ul>';
        } else {
            inspectionHtml = '<div class="text-muted mt-2 fst-italic small">No inspection checklist data</div>';
        }

        let startTime = fuze.start_time ? new Date(fuze.start_time).toLocaleString() : 'N/A';
        let endTime = fuze.end_time ? new Date(fuze.end_time).toLocaleString() : 'N/A';

        fuzeHtml += `
            <div class="accordion-item shadow-sm mb-2 border rounded">
            <h2 class="accordion-header" id="flush-headingFuze${fuze.id}">
                <button class="accordion-button collapsed rounded" type="button" data-bs-toggle="collapse" data-bs-target="#flush-collapseFuze${fuze.id}" aria-expanded="false" aria-controls="flush-collapseFuze${fuze.id}">
                    <div class="d-flex justify-content-between align-items-center w-100 me-3">
                        <span class="fw-bold d-flex align-items-center"><span class="material-symbols-outlined align-text-bottom me-2 text-primary">military_tech</span> Primer Sequence #${fuze.sequence_number} | Box Number: ${fuze.box_number || 'N/A'} | Acceptance Status:  <span class="ms-2 badge bg-${fuze.acceptance_status === true ? 'success' : (fuze.acceptance_status === false ? 'danger' : 'secondary')}">${fuze.acceptance_status === true ? 'Passed' : (fuze.acceptance_status === false ? 'Rejected' : 'Not Answered')}</span></span>
                        <div class="d-flex align-items-center gap-2">
                            <span class="badge bg-${badgeColor}">${fuze.fuze_inspection_status}</span>
                        </div>
                    </div>
                </button>
            </h2>
            <div id="flush-collapseFuze${fuze.id}" class="accordion-collapse collapse" aria-labelledby="flush-headingFuze${fuze.id}" data-bs-parent="#fuzeAccordion">
                <div class="accordion-body bg-light">
                    <div class="row g-4">
                        <div class="col-lg-6">
                            <h6 class="text-muted small fw-bold mb-3 text-uppercase">Media Gallery</h6>
                            ${mediaHtml}
                        </div>
                        <div class="col-lg-6">
                            <h6 class="text-muted small fw-bold mb-3 text-uppercase">Inspection Details</h6>
                            <div class="row g-2 mb-3">
                                <div class="col-sm-6">
                                    <div class="bg-white p-2 rounded border">
                                        <div class="text-muted" style="font-size: 0.75rem;">Primer Type</div>
                                        <div class="fw-bold">${fuze.fuze_type || '-'}</div>
                                    </div>
                                </div>
                                <div class="col-sm-6">
                                    <div class="bg-white p-2 rounded border">
                                        <div class="text-muted" style="font-size: 0.75rem;">Duration</div>
                                        <div class="small text-truncate" title="Start: ${startTime}&#10;End: ${endTime}">
                                            ${startTime.split(',')[1] || startTime} - ${endTime.split(',')[1] || endTime}
                                        </div>
                                    </div>
                                </div>
                                <div class="col-sm-12">
                                    <div class="bg-white p-2 rounded border">
                                        <div class="text-muted" style="font-size: 0.75rem;">Acceptance Status</div>
                                        <div class="mt-1"><span class="badge bg-${fuze.acceptance_status === true ? 'success' : (fuze.acceptance_status === false ? 'danger' : 'secondary')}">${fuze.acceptance_status === true ? 'Passed' : (fuze.acceptance_status === false ? 'Rejected' : 'Not Answered')}</span></div>
                                    </div>
                                </div>
                            </div>
                            <h6 class="text-muted small fw-bold mb-2">Checklist Parameters</h6>
                            ${inspectionHtml}
                            ${fuze.fuze_inspection_status === "Completed" ? `<div class="mt-2 d-flex justify-content-end gap-2">
                                <button class="btn btn-sm btn-outline-primary shadow-sm" style="font-size: 0.75rem" onclick="event.stopPropagation(); downloadFuzeReport(${fuze.id}, '${fuze.sequence_number || 'N/A'}')"><span class="material-symbols-outlined align-text-bottom fs-6 me-1">table_chart</span> Excel</button>
                                <button class="btn btn-sm btn-outline-primary shadow-sm" style="font-size: 0.75rem" onclick="event.stopPropagation(); downloadFuzePdfReport(${fuze.id}, '${fuze.sequence_number || 'N/A'}')"><span class="material-symbols-outlined align-text-bottom fs-6 me-1">picture_as_pdf</span> PDF</button>
                            </div>` : ''}
                        </div>
                    </div>
                </div>
            </div>
        </div>
            `;
    });

    fuzeAccordion.innerHTML = fuzeHtml;
}

function downloadBoxReport(boxId, boxNumber) {
    if (typeof showToast === 'function') {
        showToast(`Generating Excel report for box ${boxNumber}...`, 'info');
    }

    // Create a temporary hidden link to trigger the download
    const link = document.createElement('a');
    link.href = `/reports/box/${boxId}/excel`;
    link.download = `box_report_${boxId}.xlsx`; // Browser might override with header
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function downloadBoxPdfReport(boxId, boxNumber) {
    if (typeof showToast === 'function') {
        showToast(`Generating PDF report for box ${boxNumber}...`, 'info');
    }

    // Create a temporary hidden link to trigger the download
    const link = document.createElement('a');
    link.href = `/reports/box/${boxId}/pdf`;
    link.download = `box_report_${boxId}.pdf`; // Browser might override with header
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function downloadFuzeReport(fuzeId, fuzeSequence) {
    if (typeof showToast === 'function') {
        showToast(`Generating Excel report for primer sequence ${fuzeSequence}...`, 'info');
    }

    // Create a temporary hidden link to trigger the download
    const link = document.createElement('a');
    link.href = `/reports/fuze/${fuzeId}/excel`;
    link.download = `primer_report_${fuzeId}.xlsx`; // Browser might override with header
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function downloadFuzePdfReport(fuzeId, fuzeSequence) {
    if (typeof showToast === 'function') {
        showToast(`Generating PDF report for primer sequence ${fuzeSequence}...`, 'info');
    }

    // Create a temporary hidden link to trigger the download
    const link = document.createElement('a');
    link.href = `/reports/fuze/${fuzeId}/pdf`;
    link.download = `primer_report_${fuzeId}.pdf`; // Browser might override with header
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}


async function downloadLotZipReport(lotId, lotNumber) {
    const btn = document.getElementById('lotZipDownloadBtn');

    // Disable button and show spinner
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Generating ZIP...`;
    }

    if (typeof showToast === 'function') {
        showToast(`Generating comprehensive ZIP report for Lot ${lotNumber}. This may take a moment...`, 'info', null, 5000);
    }

    try {
        const response = await fetch(`/reports/lot/${lotId}/export-zip`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const blob = await response.blob();

        // Create an object URL containing the blob data and trigger download
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `Lot_${lotNumber}.zip`;
        document.body.appendChild(link);
        link.click();

        // Cleanup
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);

        if (typeof showToast === 'function') {
            showToast(`Lot ${lotNumber} ZIP report downloaded successfully.`, 'success');
        }

    } catch (e) {
        console.error('Error downloading ZIP:', e);
        if (typeof showToast === 'function') {
            showToast(`Failed to generate ZIP report. Please try again.`, 'error');
        } else {
            alert('Failed to generate ZIP report. Please try again.');
        }
    } finally {
        // Restore button state
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<span class="material-symbols-outlined align-text-bottom me-2">folder_zip</span> Download Full Report (ZIP)`;
        }
    }
}
