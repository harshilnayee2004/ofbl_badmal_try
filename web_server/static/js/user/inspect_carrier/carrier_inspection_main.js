// ==========================================
// Carrier 6A/L Inspection Main Logic
// ==========================================

document.addEventListener('DOMContentLoaded', function () {
    loadLot();
    initSuppressCameraErrorState();
});

function backToSelection() {
    localStorage.removeItem("carrier_inspection_lot_id");
    window.location.href = "/user/inspect_carrier";
}

// Load Lot Details
function loadLot() {
    const lotId = document.getElementById('lotId').value;
    if (!lotId) return;

    localStorage.setItem("carrier_inspection_lot_id", lotId);

    fetch(`/lots/get_lot_by_id/${lotId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status && data.object) {
                setLotDetails(data);
            } else {
                console.error('Error fetching lot info:', data.message);
                if (typeof showToast === 'function') {
                    showToast("Error loading lot info: " + data.message, "danger");
                }
            }
        })
        .catch(error => {
            console.error('Error loading lot:', error);
        });
}

// Set Lot Details
function setLotDetails(data) {
    const lot_details = data.object || {};
    const lotNumberEl = document.getElementById('lotNumber');
    if (lotNumberEl) {
        lotNumberEl.innerText = lot_details.lot_number || "--";
    }
    getCarrierDetails(lot_details.lot_id || lot_details.id);
}

// Get Carrier Details
function getCarrierDetails(lotId) {
    fetch(`/carrier/get_carrier_current_details/${lotId}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        },
    })
        .then(response => response.json())
        .then(data => {
            if (data.status && data.object) {
                setCarrierDetails(data);
            } else {
                console.error('Error fetching carrier details:', data.message);
                clearCarrierPlaceholders();
                setCarrierInspectionDetails({});
            }
        })
        .catch(error => {
            console.error('Error loading carrier inspection:', error);
            clearCarrierPlaceholders();
            setCarrierInspectionDetails({});
        });
}

function clearCarrierPlaceholders() {
    const fields = ['carrierType', 'carrierNumber', 'carrierSequence', 'instructionText'];
    fields.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.classList.remove('placeholder-glow');
            if (id === 'instructionText') {
                el.innerText = 'Ready for Inspection';
            } else if (id === 'carrierType') {
                el.innerText = 'Carrier 6A/L';
            } else if (id === 'carrierSequence') {
                el.innerText = '1';
            } else {
                el.innerText = '--';
            }
        }
    });
}

// Set Carrier Details
function setCarrierDetails(data) {
    const carrier_details = data.object || {};
    const carrierId = carrier_details.carrier_id || "";

    document.getElementById('carrierId').value = carrierId;

    const carrierNumberEl = document.getElementById('carrierNumber');
    if (carrierNumberEl) {
        carrierNumberEl.innerText = carrier_details.carrier_number === null || carrier_details.carrier_number === undefined 
            ? (carrier_details.carrier_sequence ? `CARRIER-${carrier_details.carrier_sequence}` : "- -")
            : carrier_details.carrier_number;
        carrierNumberEl.classList.remove('placeholder-glow');
    }

    const carrierSequenceEl = document.getElementById('carrierSequence');
    if (carrierSequenceEl) {
        carrierSequenceEl.innerText = carrier_details.carrier_sequence || "1";
        carrierSequenceEl.classList.remove('placeholder-glow');
    }

    const carrierSequenceBadge = document.getElementById('carrierSequenceBadge');
    if (carrierSequenceBadge) {
        carrierSequenceBadge.innerText = `Seq #${carrier_details.carrier_sequence || 1}`;
    }

    const carrierTypeEl = document.getElementById('carrierType');
    if (carrierTypeEl) {
        carrierTypeEl.innerText = carrier_details.carrier_type || "Carrier 6A/L";
        carrierTypeEl.classList.remove('placeholder-glow');
    }

    const instructionText = document.getElementById('instructionText');
    if (instructionText) {
        instructionText.innerText = "Ready for Inspection";
        instructionText.classList.remove('placeholder-glow');
    }

    const statusBadge = document.getElementById('inspectionStatus');
    const status = carrier_details.carrier_inspection_status || "Pending";

    if (statusBadge) {
        statusBadge.classList.remove('placeholder-glow');
        statusBadge.className = "badge font-monospace";
    }

    if (status === "Completed") {
        document.getElementById('postInspectionActions').classList.remove('d-none');
        document.getElementById('activeInspectionActions').classList.add('d-none');
        document.getElementById('preInspectionActions').classList.add('d-none');

        if (statusBadge) {
            statusBadge.classList.add(carrier_details.acceptance_status === false ? 'badge-rejected' : 'badge-passed');
            statusBadge.innerText = carrier_details.acceptance_status === false ? "Rejected" : "Completed";
        }
    } else if (status === "Failed") {
        document.getElementById('postInspectionActions').classList.add('d-none');
        document.getElementById('activeInspectionActions').classList.add('d-none');
        document.getElementById('preInspectionActions').classList.remove('d-none');

        if (statusBadge) {
            statusBadge.classList.add('badge-rejected');
            statusBadge.innerText = "Failed";
        }
    } else if (status === "Stopped") {
        document.getElementById('postInspectionActions').classList.add('d-none');
        document.getElementById('activeInspectionActions').classList.add('d-none');
        document.getElementById('preInspectionActions').classList.remove('d-none');

        if (statusBadge) {
            statusBadge.classList.add('badge-rejected');
            statusBadge.innerText = "Stopped";
        }
    } else if (status === "Paused") {
        document.getElementById('postInspectionActions').classList.add('d-none');
        document.getElementById('activeInspectionActions').classList.remove('d-none');
        document.getElementById('preInspectionActions').classList.add('d-none');
        document.getElementById('pauseBtn').classList.add('d-none');
        document.getElementById('resumeBtn').classList.remove('d-none');

        if (statusBadge) {
            statusBadge.classList.add('badge-pending');
            statusBadge.innerText = "Paused";
        }
        fetchCurrentState();
    } else if (status === "Inspecting") {
        document.getElementById('postInspectionActions').classList.add('d-none');
        document.getElementById('preInspectionActions').classList.add('d-none');
        document.getElementById('activeInspectionActions').classList.remove('d-none');

        if (statusBadge) {
            statusBadge.classList.add('badge-inspecting');
            statusBadge.innerText = "Inspecting";
        }
        fetchCurrentState();
    } else {
        document.getElementById('postInspectionActions').classList.add('d-none');
        document.getElementById('preInspectionActions').classList.remove('d-none');
        document.getElementById('activeInspectionActions').classList.add('d-none');

        if (statusBadge) {
            statusBadge.classList.add('badge-pending');
            statusBadge.innerText = "Pending";
        }
        fetchCurrentState();
    }

    // Fetch historical logs (which will also connect to log websocket on response)
    if (carrierId) {
        fetchLogs(carrierId);
    }

    setCarrierInspectionDetails(carrier_details.inspection || {});
}

function setCarrierInspectionDetails(data) {
    const parameters = [
        { label: "Sealed Box Check", subtext: "Check whether wire/lead seal is intact", key: "sealed_box", status: data.sealed_box },
        { label: "Damage Box", subtext: "Check for external dents, cracks, or deformations", key: "damage_box", status: data.damage_box !== null && data.damage_box !== undefined ? !data.damage_box : null, isNegative: true },
        { label: "Rusty Box", subtext: "Check for rust or surface corrosion", key: "rusty_box", status: data.rusty_box !== null && data.rusty_box !== undefined ? !data.rusty_box : null, isNegative: true },
        { label: "Incorrect Stenciling on Box", subtext: "Verify OCR stenciling format on carrier", key: "stenciling", status: data.stenciling },
        { label: "Explosive Label Missing", subtext: "Check Hazard Class 1.4S explosive sticker", key: "explosive_label", status: data.explosive_label }
    ];

    const container = document.getElementById("inspectionParameters");
    if (!container) return;
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
    const carrierId = document.getElementById("carrierId").value;

    fetch("/carrier/update_parameter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            carrier_id: parseInt(carrierId),
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
        if (typeof showToast === 'function') {
            showToast(`Parameter ${paramKey.replace('_', ' ')} updated.`, "success");
        }
    })
    .catch(err => {
        console.error("Error updating parameter:", err);
        event.target.checked = !isChecked;
        if (typeof showToast === 'function') {
            showToast("Failed to update parameter.", "danger");
        }
    });
}

function fetchCurrentState() {
    fetch('/carrier/get_current_inspection_state')
        .then(response => response.json())
        .then(data => {
            const instructionText = document.getElementById('instructionText');
            const waitingTime = document.getElementById('waitingTime');

            if (data.status && data.object) {
                if (instructionText) {
                    instructionText.innerText = data.object.instruction || "Ready for Inspection";
                    instructionText.classList.remove('placeholder-glow');
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
            } else {
                if (instructionText) {
                    instructionText.innerText = "Ready for Inspection";
                    instructionText.classList.remove('placeholder-glow');
                }
            }
        })
        .catch(error => {
            console.error('Error fetching current state:', error);
            const instructionText = document.getElementById('instructionText');
            if (instructionText && instructionText.querySelector('.placeholder')) {
                instructionText.innerText = "Ready for Inspection";
                instructionText.classList.remove('placeholder-glow');
            }
        });
}

function startInspection() {
    const carrierId = document.getElementById('carrierId').value;
    const lotId = document.getElementById('lotId').value;
    const carrierType = document.getElementById('carrierType') ? document.getElementById('carrierType').innerText.trim() : "Carrier 6A/L";

    document.getElementById('postInspectionActions').classList.add('d-none');
    document.getElementById('preInspectionActions').classList.add('d-none');
    document.getElementById('activeInspectionActions').classList.remove('d-none');

    const statusBadge = document.getElementById('inspectionStatus');
    if (statusBadge) {
        statusBadge.className = 'badge badge-inspecting font-monospace';
        statusBadge.innerText = "Inspecting";
    }

    fetch('/carrier/start_inspection', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            carrier_id: parseInt(carrierId),
            carrier_type: carrierType,
            lot_id: parseInt(lotId)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status) {
            document.getElementById('pauseBtn').classList.remove('d-none');
            document.getElementById('resumeBtn').classList.add('d-none');
            document.getElementById('postInspectionActions').classList.add('d-none');
            document.getElementById('preInspectionActions').classList.add('d-none');
            document.getElementById('activeInspectionActions').classList.remove('d-none');

            if (typeof showToast === 'function') {
                showToast("Carrier inspection started.", "success");
            }
        } else {
            revertInspectionUI();
            console.error('Error starting inspection:', data.message);
            if (typeof showToast === 'function') {
                showToast(data.message || "Error starting inspection.", "danger");
            }
        }
    })
    .catch(error => {
        console.error('Error starting inspection:', error);
        revertInspectionUI();
        if (typeof showToast === 'function') {
            showToast("Error starting inspection. Please check connection.", "danger");
        }
    });
}

function updateStatus(status) {
    const carrierId = parseInt(document.getElementById('carrierId').value);

    fetch('/carrier/update_status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            carrier_id: carrierId,
            status: status
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status) {
            const newStatus = (data.object && typeof data.object.status === 'string') ? data.object.status : status;
            updateUIForStatus(newStatus);
            if (typeof showToast === 'function') {
                showToast(`Inspection ${newStatus === 'Paused' ? 'paused' : newStatus === 'Inspecting' ? 'resumed' : String(newStatus).toLowerCase()}.`, "success");
            }
        } else {
            if (typeof showToast === 'function') {
                showToast(data.message || "Error updating status.", "danger");
            }
        }
    })
    .catch(error => {
        console.error('Error updating status:', error);
        if (typeof showToast === 'function') {
            showToast("Error updating status. Please check connection.", "danger");
        }
    });
}

function updateUIForStatus(status) {
    const pauseBtn = document.getElementById('pauseBtn');
    const resumeBtn = document.getElementById('resumeBtn');
    const statusBadge = document.getElementById('inspectionStatus');

    if (status === "Paused") {
        if (pauseBtn) pauseBtn.classList.add('d-none');
        if (resumeBtn) resumeBtn.classList.remove('d-none');
        if (statusBadge) {
            statusBadge.innerText = "Paused";
            statusBadge.className = "badge badge-pending font-monospace";
        }
        if (typeof stopCountdown === 'function') {
            stopCountdown();
        }
    } else if (status === "Inspecting") {
        if (resumeBtn) resumeBtn.classList.add('d-none');
        if (pauseBtn) pauseBtn.classList.remove('d-none');
        if (statusBadge) {
            statusBadge.innerText = "Inspecting";
            statusBadge.className = "badge badge-inspecting font-monospace";
        }
        fetchCurrentState();
    } else if (status === "Stopped") {
        document.getElementById('postInspectionActions').classList.add('d-none');
        document.getElementById('activeInspectionActions').classList.add('d-none');
        document.getElementById('preInspectionActions').classList.remove('d-none');

        if (statusBadge) {
            statusBadge.className = "badge badge-rejected font-monospace";
            statusBadge.innerText = "Stopped";
        }
    }
}

function revertInspectionUI() {
    document.getElementById('postInspectionActions').classList.add('d-none');
    document.getElementById('activeInspectionActions').classList.add('d-none');
    document.getElementById('preInspectionActions').classList.remove('d-none');

    const statusBadge = document.getElementById('inspectionStatus');
    if (statusBadge) {
        statusBadge.className = "badge badge-rejected font-monospace";
        statusBadge.innerText = "Stopped";
    }
}

function openEditCarrierNumberModal() {
    const carrierNumberEl = document.getElementById('carrierNumber');
    if (!carrierNumberEl || carrierNumberEl.classList.contains('placeholder-glow') || carrierNumberEl.querySelector('.placeholder')) {
        return;
    }
    const currentVal = carrierNumberEl.innerText.replace(/[^0-9]/g, '');
    document.getElementById('newCarrierNumberInput').value = currentVal || '';
    const modal = new bootstrap.Modal(document.getElementById('editCarrierNumberModal'));
    modal.show();
}

function submitCarrierNumberUpdate() {
    const carrierId = document.getElementById('carrierId').value;
    const lotId = document.getElementById('lotId').value;
    const newNumber = document.getElementById('newCarrierNumberInput').value;

    if (!newNumber || newNumber.trim() === "") {
        if (typeof showToast === 'function') {
            showToast("Please enter a valid carrier number.", "warning");
        }
        return;
    }

    fetch('/carrier/update_carrier_number', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            carrier_id: parseInt(carrierId),
            lot_id: parseInt(lotId),
            new_carrier_number: parseInt(newNumber.trim())
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status) {
            document.getElementById('carrierNumber').innerText = newNumber.trim();
            const modalEl = document.getElementById('editCarrierNumberModal');
            const modalInstance = bootstrap.Modal.getInstance(modalEl);
            if (modalInstance) modalInstance.hide();
            if (typeof showToast === 'function') {
                showToast("Carrier number updated successfully.", "success");
            }
        } else {
            if (typeof showToast === 'function') {
                showToast("Error updating carrier number: " + data.message, "danger");
            }
        }
    })
    .catch(error => {
        console.error('Error updating carrier number:', error);
        if (typeof showToast === 'function') {
            showToast("Failed to update carrier number.", "danger");
        }
    });
}

function moveToNextCarrier() {
    triggerNextCarrierSequence();
}

function triggerNextCarrierSequence() {
    const lotId = document.getElementById('lotId').value;

    fetch(`/lots/increment_carrier_sequence/${lotId}`, {
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
                showToast("All carriers completed! Redirecting...", 'success');
            }
            setTimeout(() => {
                backToSelection();
            }, 2500);
        }
    })
    .catch(error => {
        console.error('Error moving to next carrier:', error);
        window.location.reload();
    });
}

function triggerPreviousCarrierSequence() {
    const lotId = document.getElementById('lotId').value;

    fetch(`/lots/decrement_carrier_sequence/${lotId}`, {
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
                showToast("Error moving to previous carrier: " + (data.message || "Unknown error"), "warning");
            }
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('Error moving to previous carrier:', error);
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

function setCameraErrorSuppressionUI(enabled) {
    window.isCameraErrorSuppressed = Boolean(enabled);
    const sw = document.getElementById("suppressCameraErrorSwitch");
    const label = document.getElementById("suppressCameraErrorLabel");
    const overlay = document.getElementById("suppressedCameraOverlay");

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
