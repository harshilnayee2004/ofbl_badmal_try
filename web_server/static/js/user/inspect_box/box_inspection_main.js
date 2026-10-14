// When the Page loads
document.addEventListener('DOMContentLoaded', function () {
    loadLot();
    initSuppressCameraErrorState();
});

function backToSelection() {
    localStorage.removeItem("box_inspection_lot_id");
    window.location.href = "/user/inspect_box";
}

// Search lots
function searchLots() {
    const query = document.getElementById('lotSearchInput').value;
    const resultsContainer = document.getElementById('lotSearchResults');

    if (query.length < 1) {
        resultsContainer.innerHTML = '<div class="text-center text-muted p-3">Type to search for lots</div>';
        return;
    }

    fetch(`/lots/search?query=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            if (data.status && data.object) {
                let html = '';
                if (data.object.length === 0) {
                    html = '<div class="text-center text-muted p-3">No lots found</div>';
                } else {
                    data.object.forEach(lot => {
                        html += `
                            <button type="button" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center" onclick="proceedWithLot(${lot.id})">
                                <div>
                                    <div class="fw-bold">${lot.lot_number}</div>
                                    <small class="text-muted">${lot.fuze_type}</small>
                                </div>
                                <span class="badge bg-primary rounded-pill">${lot.inspection_status}</span>
                            </button>
                        `;
                    });
                }
                resultsContainer.innerHTML = html;
            }
        })
        .catch(error => {
            console.error('Error searching lots:', error);
        });
}

// Select Lot number after search
function proceedWithLot(lotId) {
    window.location.href = `/user/inspect_box?lot_id=${lotId}`;
}

// Load Lots
function loadLot() {
    const lotId = document.getElementById('lotId').value;
    console.log("Current Lot ID:", lotId);
    localStorage.setItem("box_inspection_lot_id", lotId);

    // if (lotId === "") {
    //     const modalElement = document.getElementById('staticBackdrop');
    //     const modal = new bootstrap.Modal(modalElement);
    //     modal.show();
    //     return;
    // }

    fetch(`/lots/get_lot_by_id/${lotId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status) {
                setLotDetails(data);
            } else {
                console.error('Error fetching lot info:', data.message);
                alert("Error loading lot info: " + data.message);
            }
        })
        .catch(error => {
            console.error('Error loading lot:', error);
        });
}

// Set Lot Details
function setLotDetails(data) {
    console.log(data.object);
    let lot_details = data.object
    document.getElementById('lotNumber').innerText = lot_details.lot_number
    getBoxDetails(lot_details.lot_id)
}

function getBoxDetails(lotId) {
    fetch(`/box/get_box_current_details/${lotId}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        },
    })
        .then(response => response.json())
        .then(data => {
            if (data.status && data.object) {
                setBoxDetails(data);
            } else {
                console.error('Error fetching box details:', data.message);
                setH2AInspectionDetails({});
            }
        })
        .catch(error => {
            console.error('Error loading inspection:', error);
            setH2AInspectionDetails({});
        });
}


// Set Box Details
function setBoxDetails(data) {
    let box_details = data.object || {};
    const boxId = box_details.box_id || "";

    document.getElementById('boxId').value = boxId;

    const boxNumberEl = document.getElementById('boxNumber');
    if (boxNumberEl) {
        boxNumberEl.innerText = box_details.box_number === null || box_details.box_number === undefined ? "- -" : box_details.box_number;
        boxNumberEl.classList.remove('placeholder-glow');
    }

    const boxSequenceEl = document.getElementById('boxSequence');
    if (boxSequenceEl) {
        boxSequenceEl.innerText = box_details.box_sequence || "1";
        boxSequenceEl.classList.remove('placeholder-glow');
    }

    const boxTypeEl = document.getElementById('boxType');
    if (boxTypeEl) {
        boxTypeEl.innerText = box_details.box_type || "H2A";
        boxTypeEl.classList.remove('placeholder-glow');
    }

    const inspectionStatusEl = document.getElementById('inspectionStatus');
    if (inspectionStatusEl) {
        inspectionStatusEl.innerText = box_details.box_inspection_status || "Pending";
        inspectionStatusEl.classList.remove('placeholder-glow');
    }


    if (box_details.box_inspection_status == "Completed") {
        document.getElementById('postInspectionActions').classList.remove('d-none');
        document.getElementById('activeInspectionActions').classList.add('d-none');
        document.getElementById('preInspectionActions').classList.add('d-none');

        // Update Status Badge
        const statusBadge = document.getElementById('inspectionStatus');
        statusBadge.classList.remove('bg-info', 'bg-danger', 'bg-warning', 'bg-secondary');
        statusBadge.classList.add('bg-success');
        statusBadge.innerText = "Completed";
    } else if (box_details.box_inspection_status == "Failed") {
        document.getElementById('postInspectionActions').classList.add('d-none');
        document.getElementById('activeInspectionActions').classList.add('d-none');
        document.getElementById('preInspectionActions').classList.remove('d-none');

        // Update Status Badge
        const statusBadge = document.getElementById('inspectionStatus');
        statusBadge.classList.remove('bg-info', 'bg-success', 'bg-warning', 'bg-secondary');
        statusBadge.classList.add('bg-danger');
        statusBadge.innerText = "Failed";
    } else if (box_details.box_inspection_status == "Stopped") {
        document.getElementById('postInspectionActions').classList.add('d-none');
        document.getElementById('activeInspectionActions').classList.add('d-none');
        document.getElementById('preInspectionActions').classList.remove('d-none');

        // Update Status Badge
        const statusBadge = document.getElementById('inspectionStatus');
        statusBadge.classList.remove('bg-info', 'bg-success', 'bg-warning', 'bg-secondary');
        statusBadge.classList.add('bg-danger');
        statusBadge.innerText = "Stopped";
    }
    else if (box_details.box_inspection_status == "Paused") {

        document.getElementById('postInspectionActions').classList.add('d-none');
        document.getElementById('activeInspectionActions').classList.remove('d-none');
        document.getElementById('preInspectionActions').classList.add('d-none');
        document.getElementById('pauseBtn').classList.add('d-none');
        document.getElementById('resumeBtn').classList.remove('d-none');

        // Update Status Badge
        const statusBadge = document.getElementById('inspectionStatus');
        statusBadge.classList.remove('bg-info', 'bg-success', 'bg-warning', 'bg-danger');
        statusBadge.classList.add('bg-secondary');
        statusBadge.innerText = "Paused";
        fetchCurrentState();
    }
    else if (box_details.box_inspection_status == "Inspecting") {
        document.getElementById('postInspectionActions').classList.add('d-none');
        document.getElementById('preInspectionActions').classList.add('d-none');
        document.getElementById('activeInspectionActions').classList.remove('d-none');

        // Update Status Badge
        const statusBadge = document.getElementById('inspectionStatus');
        statusBadge.classList.remove('bg-info', 'bg-success', 'bg-secondary', 'bg-danger');
        statusBadge.classList.add('bg-warning');
        statusBadge.innerText = "Inspecting";

        fetchCurrentState();
    } else {
        document.getElementById('postInspectionActions').classList.add('d-none');
        document.getElementById('preInspectionActions').classList.remove('d-none');
        document.getElementById('activeInspectionActions').classList.add('d-none');

        // Update Status Badge
        const statusBadge = document.getElementById('inspectionStatus');
        statusBadge.classList.remove('bg-info', 'bg-success', 'bg-secondary', 'bg-danger');
        statusBadge.classList.add('bg-primary');
        statusBadge.innerText = "Pending";

        fetchCurrentState();
    }

    // Fetch historical logs
    if (boxId) {
        fetchLogs(boxId);
        connectLogWebSocket(boxId);
    }

    setH2AInspectionDetails(box_details.inspection || {});
}

function setH2AInspectionDetails(data) {
    const parameters = [
        { label: "Incorrect Stenciling on Box", subtext: "Check OCR of 5 sides of the box", key: "stenciling_5_sides", status: data.stenciling_5_sides },
        { label: "Explosive Label Missing", subtext: "Check whether the explosive label is missing", key: "explosive_label", status: data.explosive_label },
        { label: "Wooden Sheet", subtext: "Check whether the wooden sheet is present or not", key: "wooden_sheet", status: data.wooden_sheet },
        { label: "Packing Slip", subtext: "Check whether the white/brown packing slip is present or not", key: "packing_slip", status: data.packing_slip },
        { label: "Cotton Sheet", subtext: "Check whether the cotton sheet is present or not", key: "cotton_sheet", status: data.cotton_sheet },
        { label: "More / Less Quantity in Box", subtext: "Count the total number of primers", key: "primer_quantity_count", status: data.primer_quantity_count },
        { label: "Wooden Sheet (18 Holes)", subtext: "Check whether 2 wooden sheets with 18 holes are present or not", key: "wooden_sheet_18_holes", status: data.wooden_sheet_18_holes },
        { label: "Rust and Peeling Paint Inside the Boxes", subtext: "Check whether the paint is proper or not inside the boxes", key: "interior_rust_peeling_paint", status: data.interior_rust_peeling_paint !== null && data.interior_rust_peeling_paint !== undefined ? !data.interior_rust_peeling_paint : null, isNegative: true }
    ];

    const container = document.getElementById("inspectionParameters");
    container.innerHTML = "";

    parameters.forEach(param => {
        const isChecked = param.status === true;
        const badgeClass = param.status === true ? "badge-passed" : (param.status === false ? "badge-rejected" : "badge-pending");
        const statusText = param.status === true ? "PASSED" : (param.status === false ? "REJECTED" : "PENDING");
        const subtextHtml = param.subtext ? `<small class="param-subtext d-block text-truncate" title="${param.subtext}">${param.subtext}</small>` : '';

        const item = `
            <div class="col-12 col-sm-6">
                <div class="param-card d-flex justify-content-between align-items-center h-100 gap-2">
                    <div class="flex-grow-1" style="min-width: 0;">
                        <span class="param-title d-block text-truncate" title="${param.label}">${param.label}</span>
                        ${subtextHtml}
                        <span class="badge ${badgeClass} font-monospace mt-1" style="font-size: 0.7rem;" id="${param.key}_status_badge">${statusText}</span>
                    </div>
                    <div class="form-check form-switch m-0 flex-shrink-0" id="${param.key}_div">
                        <input 
                            class="form-check-input param-switch" 
                            type="checkbox" 
                            id="${param.key}_checkbox"
                            ${isChecked ? "checked" : ""}
                            onchange="handleParameterChange(event, '${param.key}', ${param.isNegative || false})"
                        >
                    </div>
                </div>
            </div>
        `;
        container.innerHTML += item;
    });
}

function handleParameterChange(event, paramKey, isNegative = false) {
    const isChecked = event.target.checked;
    const dbValue = isNegative ? !isChecked : isChecked;
    const boxId = document.getElementById("boxId").value;

    fetch("/box/update_parameter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            box_id: parseInt(boxId),
            parameter_key: paramKey,
            value: dbValue
        })
    })
    .then(res => res.json())
    .then(data => {
        const badge = document.getElementById(`${paramKey}_status_badge`);
        if (badge) {
            badge.className = `badge ${isChecked ? "badge-passed" : "badge-rejected"} font-monospace mt-1`;
            badge.innerText = isChecked ? "PASSED (MANUAL)" : "REJECTED (MANUAL)";
        }
    })
    .catch(err => console.error("Error updating box parameter:", err));
}

function setM104InspectionDetails(data) {
    console.log(data);
    const parameters = [
        { label: "Rusting", status: data.rusting, key: "rusting" },
        { label: "Paint", status: data.paint, key: "paint" },
        { label: "Stenciling", status: data.stenciling, key: "stenciling" },
        { label: "Explosive Sticker", status: data.explosive_sticker, key: "explosive_sticker" },
        { label: "Packing Slip", status: data.packing_slip, key: "packing_slip" },
        { label: "Seals", status: data.seals, key: "seals" },
        { label: "Top Foam", status: data.top_foam, key: "top_foam" },
        { label: "Wooden grid", status: data.wooden_grid, key: "wooden_grid" },
        { label: "Bottom Foam", status: data.bottom_foam, key: "bottom_foam" },
        { label: "Container Count 10", status: data.container_count_10, key: "container_count_10" },
    ];

    const container = document.getElementById("inspectionParameters");
    container.innerHTML = "";

    parameters.forEach(param => {
        // Condition: if both AI and Manual are null
        // const isDisabled = (param.status === null);
        // ${isDisabled ? "disabled" : ""}


        // Create grid item
        const item = `
            <div class="col-12 col-sm-6">
                <div class="p-2 border rounded bg-white shadow-sm d-flex justify-content-between align-items-center param-card h-100 gap-2">
                    <span class="fw-bold small flex-grow-1 text-truncate" title="${param.label}">${param.label}</span>
                    <div class="form-check m-0 flex-shrink-0" id="${param.key}_div">
                        <input 
                            class="form-check-input inspection-checkbox border-dark param-switch" 
                            type="checkbox" 
                            id="${param.key}_checkbox"
                            ${param.status === true ? "checked" : ""}
                            onchange="handleParameterChange(event, '${param.key}')"
                        >
                    </div>
                </div>
            </div>
        `;

        container.innerHTML += item;
    });
}


function fetchCurrentState() {
    fetch('/box/get_current_inspection_state')
        .then(response => response.json())
        .then(data => {
            if (data.status && data.object) {
                const instructionText = document.getElementById('instructionText');
                const waitingTime = document.getElementById('waitingTime');

                if (instructionText && data.object.instruction) {
                    instructionText.innerText = data.object.instruction;
                }

                if (waitingTime && data.object.wait_time !== undefined) {
                    waitingTime.innerText = data.object.wait_time + "s";
                }

                const indicator = document.getElementById('recordingIndicator');
                if (indicator && data.object.recording_status !== undefined) {
                    if (data.object.recording_status) {
                        indicator.classList.remove('d-none');
                    } else {
                        indicator.classList.add('d-none');
                    }
                }
            }
        })
        .catch(error => {
            console.error('Error fetching current state:', error);
        });
}

function handleParameterChange(event, parameterKey) {
    const boxId = document.getElementById('boxId').value;
    const isChecked = event.target.checked;

    console.log(`Updating parameter ${parameterKey} to ${isChecked} for box ${boxId}`);

    fetch('/box/update_parameter', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            box_id: parseInt(boxId),
            parameter_key: parameterKey,
            value: isChecked
        })
    })
        .then(response => response.json())
        .then(data => {
            if (!data.status) {
                console.error('Error updating parameter:', data.message);
                // Revert checkbox if update failed
                event.target.checked = !isChecked;
                alert('Failed to update parameter: ' + data.message);
            } else {
                console.log('Parameter updated successfully');
            }
        })
        .catch(error => {
            console.error('Error updating parameter:', error);
            event.target.checked = !isChecked;
            alert('Error updating parameter. Please check your connection.');
        });
}


function startInspection() {
    document.getElementById('postInspectionActions').classList.add('d-none');
    document.getElementById('preInspectionActions').classList.add('d-none');
    document.getElementById('activeInspectionActions').classList.remove('d-none');

    // Update Status Badge
    const statusBadge = document.getElementById('inspectionStatus');
    statusBadge.classList.remove('bg-info', 'bg-success', 'bg-secondary', 'bg-danger');
    statusBadge.classList.add('bg-warning');
    statusBadge.innerText = "Inspecting";


    fetch(`/box/start_inspection`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            box_id: Number(document.getElementById('boxId').value),
            box_type: document.getElementById('boxType').innerText.trim() || document.getElementById('boxType').innerHTML.trim(),
            lot_id: Number(document.getElementById('lotId').value),
            suppress_cam_error: Boolean(window.isCameraErrorSuppressed)
        })
    })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            if (data.status) {
                document.getElementById('pauseBtn').classList.remove('d-none');
                document.getElementById('resumeBtn').classList.add('d-none');
                document.getElementById('postInspectionActions').classList.add('d-none');
                document.getElementById('preInspectionActions').classList.add('d-none');
                document.getElementById('activeInspectionActions').classList.remove('d-none');

                // Update Status Badge
                const statusBadge = document.getElementById('inspectionStatus');
                statusBadge.classList.remove('bg-info', 'bg-success', 'bg-secondary', 'bg-danger');
                statusBadge.classList.add('bg-warning');
                statusBadge.innerText = "Inspecting";

                if (typeof showToast === 'function') {
                    showToast("Inspection started.", "success");
                }
            } else {
                // If error, revert UI changes
                revertInspectionUI();
                console.error('Error starting inspection:', data.message);
                if (typeof showToast === 'function') {
                    showToast(data.message || "Error starting inspection.", "error");
                } else {
                    alert("Error starting inspection: " + data.message);
                }
            }
        })
        .catch(error => {
            console.error('Error loading inspection:', error);
            revertInspectionUI();
            if (typeof showToast === 'function') {
                showToast("Error starting inspection. Please check your connection.", "error");
            }
        });
}

function updateStatus(status) {
    const boxId = Number(document.getElementById('boxId').value);

    fetch(`/box/update_status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            box_id: boxId,
            status: status
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status) {
                const newStatus = (data.object && typeof data.object.status === 'string') ? data.object.status : status;
                console.log(`Status updated to ${newStatus}`);
                updateUIForStatus(newStatus);
                if (typeof showToast === 'function') {
                    showToast(`Inspection ${newStatus === 'Paused' ? 'paused' : newStatus === 'Inspecting' ? 'resumed' : String(newStatus).toLowerCase()}.`, "success");
                }
            } else {
                if (typeof showToast === 'function') {
                    showToast(data.message || "Error updating status.", "error");
                } else {
                    alert("Error updating status: " + data.message);
                }
            }
        })
        .catch(error => {
            console.error('Error updating status:', error);
            if (typeof showToast === 'function') {
                showToast("Error updating status. Please check your connection.", "error");
            }
        });
}

function updateUIForStatus(status) {
    const pauseBtn = document.getElementById('pauseBtn');
    const resumeBtn = document.getElementById('resumeBtn');
    const statusBadge = document.getElementById('inspectionStatus');

    if (status === "Paused") {
        pauseBtn.classList.add('d-none');
        resumeBtn.classList.remove('d-none');
        statusBadge.innerText = "Paused";
        statusBadge.classList.replace('bg-warning', 'bg-secondary');
        stopCountdown();
    } else if (status === "Inspecting") {
        resumeBtn.classList.add('d-none');
        pauseBtn.classList.remove('d-none');
        statusBadge.classList.replace('bg-secondary', 'bg-warning');
        statusBadge.innerText = "Inspecting";
        fetchCurrentState();
    } else if (status === "Stopped") {
        document.getElementById('postInspectionActions').classList.add('d-none');
        document.getElementById('activeInspectionActions').classList.add('d-none');
        document.getElementById('preInspectionActions').classList.remove('d-none');

        // Update Status Badge
        const statusBadge = document.getElementById('inspectionStatus');
        statusBadge.classList.remove('bg-info', 'bg-success', 'bg-warning', 'bg-secondary');
        statusBadge.classList.add('bg-danger');
        statusBadge.innerText = "Stopped";
    }
}

function revertInspectionUI() {
    document.getElementById('postInspectionActions').classList.add('d-none');
    document.getElementById('activeInspectionActions').classList.add('d-none');
    document.getElementById('preInspectionActions').classList.remove('d-none');

    // Update Status Badge
    const statusBadge = document.getElementById('inspectionStatus');
    statusBadge.classList.remove('bg-info', 'bg-success', 'bg-warning', 'bg-secondary');
    statusBadge.classList.add('bg-danger');
    statusBadge.innerText = "Stopped";
}

function openEditBoxNumberModal() {
    const boxNumberElement = document.getElementById('boxNumber');
    // Check if it's still a placeholder
    if (boxNumberElement.classList.contains('placeholder-glow') || boxNumberElement.querySelector('.placeholder')) {
        return; // Do nothing if data hasn't loaded
    }
    const currentBoxNumber = boxNumberElement.innerText;
    document.getElementById('newBoxNumberInput').value = currentBoxNumber;
    const modal = new bootstrap.Modal(document.getElementById('editBoxNumberModal'));
    modal.show();
}

function submitBoxNumberUpdate() {
    const boxId = document.getElementById('boxId').value;
    const newBoxNumber = document.getElementById('newBoxNumberInput').value;

    if (!newBoxNumber || newBoxNumber.trim() === "") {
        alert("Please enter a valid box number.");
        return;
    }

    fetch('/box/update_box_number', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            box_id: parseInt(boxId),
            lot_id: parseInt(document.getElementById('lotId').value),
            new_box_number: parseInt(newBoxNumber.trim())
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status) {
                document.getElementById('boxNumber').innerText = newBoxNumber.trim();
                // Close modal
                const modalEl = document.getElementById('editBoxNumberModal');
                const modal = bootstrap.Modal.getInstance(modalEl);
                modal.hide();
                // alert("Box number updated successfully.");
            } else {
                alert("Error updating box number: " + data.message);
            }
        })
        .catch(error => {
            console.error('Error updating box number:', error);
            alert("Error updating box number. Please check your connection.");
        });
}

function moveToNextBox() {
    triggerNextBoxSequence();
}

function triggerNextBoxSequence() {
    const lotId = document.getElementById('lotId').value;

    fetch(`/lots/increment_box_sequence/${lotId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.status) {
                window.location.reload();
            } else {
                if (typeof showToast === 'function') {
                    showToast("All boxes completed! Redirecting...", 'success');
                } else {
                    alert("All boxes completed! Redirecting...");
                }

                // Clear lot id from local storage if used

                setTimeout(() => {
                    backToSelection();
                }, 3000);
            }
        })
        .catch(error => {
            console.error('Error moving to next box:', error);
            alert("Error moving to next box. Please check your connection.");
            window.location.reload();
        });
}

function triggerPreviousBoxSequence() {
    const lotId = document.getElementById('lotId').value;

    fetch(`/lots/decrement_box_sequence/${lotId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.status) {
                window.location.reload();
            } else {
                alert("Error moving to previous box: " + data.message);
                window.location.reload();
            }
        })
        .catch(error => {
            console.error('Error moving to previous box:', error);
            alert("Error moving to previous box. Please check your connection.");
            window.location.reload();
        });
}

// ==========================================
// DEV ONLY: Camera Error Suppression Helper
// ==========================================
window.isCameraErrorSuppressed = false;

async function initSuppressCameraErrorState() {
    let isSuppressed = localStorage.getItem("dev_suppress_camera_error") === "true";

    try {
        const response = await fetch("/api/cameras/suppress_error_status");
        if (response.ok) {
            const data = await response.json();
            if (data.status && data.object && data.object.suppress_camera_error !== undefined) {
                isSuppressed = Boolean(data.object.suppress_camera_error);
            }
        }
    } catch (e) {
        console.warn("Could not fetch camera error suppression status from server:", e);
    }

    localStorage.setItem("dev_suppress_camera_error", String(isSuppressed));
    setCameraErrorSuppressionUI(isSuppressed);
}

async function onSuppressCameraErrorToggle(isChecked) {
    window.isCameraErrorSuppressed = Boolean(isChecked);
    localStorage.setItem("dev_suppress_camera_error", String(window.isCameraErrorSuppressed));
    setCameraErrorSuppressionUI(window.isCameraErrorSuppressed);

    try {
        const response = await fetch(`/api/cameras/toggle_suppress_error?enabled=${window.isCameraErrorSuppressed}`, {
            method: "POST"
        });
        const data = await response.json();
        if (data.status && data.object && data.object.suppress_camera_error !== undefined) {
            window.isCameraErrorSuppressed = Boolean(data.object.suppress_camera_error);
            localStorage.setItem("dev_suppress_camera_error", String(window.isCameraErrorSuppressed));
            setCameraErrorSuppressionUI(window.isCameraErrorSuppressed);
        }
    } catch (err) {
        console.error("Failed to sync camera suppression toggle with server:", err);
    }

    if (typeof showToast === 'function') {
        if (window.isCameraErrorSuppressed) {
            showToast("Camera error suppression enabled (Dev Mode).", "warning");
        } else {
            showToast("Camera error suppression disabled (Production Mode).", "info");
        }
    }
}

function toggleSuppressCameraError() {
    const sw = document.getElementById("suppressCameraErrorSwitch");
    if (sw) {
        sw.checked = !sw.checked;
        onSuppressCameraErrorToggle(sw.checked);
    } else {
        onSuppressCameraErrorToggle(!window.isCameraErrorSuppressed);
    }
}

function setCameraErrorSuppressionUI(enabled) {
    window.isCameraErrorSuppressed = Boolean(enabled);
    const sw = document.getElementById("suppressCameraErrorSwitch");
    const label = document.getElementById("suppressCameraErrorLabel");
    const overlay = document.getElementById("suppressedCameraOverlay");
    const img = document.getElementById("cameraViewImage");

    if (sw) {
        sw.checked = window.isCameraErrorSuppressed;
    }
    if (label) {
        label.innerText = window.isCameraErrorSuppressed ? "Cam Errors Suppressed [ON]" : "Suppress Cam Error [OFF]";
        label.className = window.isCameraErrorSuppressed ? "text-warning fw-bold font-monospace" : "text-muted font-monospace";
    }
    if (overlay) {
        if (window.isCameraErrorSuppressed) {
            overlay.classList.remove("d-none");
        } else {
            overlay.classList.add("d-none");
        }
    }
}

function handleCameraStreamError(imgElement) {
    if (window.isCameraErrorSuppressed) {
        const overlay = document.getElementById("suppressedCameraOverlay");
        if (overlay) {
            overlay.classList.remove("d-none");
        }
    } else {
        console.warn("[Camera] Live stream feed offline or error occurred.");
    }
}

