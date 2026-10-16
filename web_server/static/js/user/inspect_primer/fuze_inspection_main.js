// When the Page loads
document.addEventListener('DOMContentLoaded', function () {
    loadLot();
});

function backToSelection() {
    localStorage.removeItem("fuze_inspection_lot_id");
    window.location.href = "/user/inspect_fuze";
}

// Load Lots
function loadLot() {

    const lotId = document.getElementById('lotId').value;
    console.log("Current Lot ID:", lotId);
    localStorage.setItem("fuze_inspection_lot_id", lotId);

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
    let lot_details = data.object || {};
    const lotNumberEl = document.getElementById('lotNumber');
    if (lotNumberEl) {
        lotNumberEl.innerText = lot_details.lot_number || "--";
    }
    getFuzeDetails(lot_details.lot_id || lot_details.id);
}

function getFuzeDetails(lotId) {
    fetch(`/fuze/get_fuze_current_details/${lotId}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        },
    })
        .then(response => response.json())
        .then(data => {
            if (data.status && data.object) {
                setFuzeDetails(data);
            } else {
                console.error('Error fetching fuze details:', data.message);
                setPrimer1ALInspectionDetails({});
                clearFuzePlaceholders();
            }
        })
        .catch(error => {
            console.error('Error loading inspection:', error);
            setPrimer1ALInspectionDetails({});
            clearFuzePlaceholders();
        });
}

function clearFuzePlaceholders() {
    const fields = ['fuzeType', 'fuzeSequence', 'instructionText', 'waitingTime'];
    fields.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.classList.remove('placeholder-glow');
            if (id === 'instructionText') {
                el.innerText = 'Ready for Inspection';
            } else if (id === 'waitingTime') {
                el.innerText = '0s';
            } else if (id === 'fuzeType') {
                el.innerText = 'Primer Electric 1A/L';
            } else if (id === 'fuzeSequence') {
                el.innerText = '1';
            }
        }
    });
}

function fetchCurrentState() {
    fetch('/fuze/get_current_inspection_state')
        .then(response => response.json())
        .then(data => {
            const instructionText = document.getElementById('instructionText');
            const waitingTime = document.getElementById('waitingTime');

            if (data.status && data.object) {
                if (instructionText) {
                    instructionText.innerText = data.object.instruction || "Ready for Inspection";
                    instructionText.classList.remove('placeholder-glow');
                }

                if (waitingTime) {
                    waitingTime.classList.remove('placeholder-glow');
                    const wt = data.object.wait_time !== undefined ? data.object.wait_time : 0;
                    waitingTime.innerText = wt + "s";
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
                if (waitingTime) {
                    waitingTime.classList.remove('placeholder-glow');
                    waitingTime.innerText = "0s";
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
            const waitingTime = document.getElementById('waitingTime');
            if (waitingTime) {
                waitingTime.innerText = "0s";
                waitingTime.classList.remove('placeholder-glow');
            }
        });
}

// Set Fuze Details
function setFuzeDetails(data) {
    let fuze_details = data.object || {};
    const fuzeId = fuze_details.fuze_id || "";

    document.getElementById('fuzeId').value = fuzeId;

    const fuzeSequenceEl = document.getElementById('fuzeSequence');
    if (fuzeSequenceEl) {
        fuzeSequenceEl.innerText = fuze_details.fuze_sequence || "1";
        fuzeSequenceEl.classList.remove('placeholder-glow');
    }

    const fuzeTypeEl = document.getElementById('fuzeType');
    if (fuzeTypeEl) {
        fuzeTypeEl.innerText = fuze_details.fuze_type || "Primer Electric 1A/L";
        fuzeTypeEl.classList.remove('placeholder-glow');
    }

    const inspectionStatusEl = document.getElementById('inspectionStatus');
    if (inspectionStatusEl) {
        inspectionStatusEl.innerText = fuze_details.fuze_inspection_status || "Pending";
        inspectionStatusEl.classList.remove('placeholder-glow');
    }

    const instructionText = document.getElementById('instructionText');
    if (instructionText) {
        instructionText.innerText = "Ready for Inspection";
        instructionText.classList.remove('placeholder-glow');
    }

    const waitingTime = document.getElementById('waitingTime');
    if (waitingTime) {
        waitingTime.innerText = "0s";
        waitingTime.classList.remove('placeholder-glow');
    }

    // Update Recording Status
    const indicator = document.getElementById('recordingIndicator');
    if (indicator && fuze_details.recording_status !== undefined) {
        if (fuze_details.recording_status) {
            indicator.classList.remove('d-none');
        } else {
            indicator.classList.add('d-none');
        }
    }

    if (fuzeId) {
        fetchLogs(fuzeId);
    }

    if (fuze_details.fuze_inspection_status == "Completed") {
        // Finalize UI after inspection
        document.getElementById('preInspectionActions').classList.add('d-none');
        document.getElementById('activeInspectionActions').classList.add('d-none');
        document.getElementById('postInspectionActions').classList.remove('d-none');
        const statusBadge = document.getElementById('inspectionStatus');

        // Update Badge
        statusBadge.classList.remove('bg-warning', 'bg-info');
        statusBadge.classList.add('bg-success');
        statusBadge.innerText = "Completed";
    } else if (fuze_details.fuze_inspection_status == "Inspecting") {
        // Finalize UI after inspection
        document.getElementById('preInspectionActions').classList.add('d-none');
        document.getElementById('activeInspectionActions').classList.remove('d-none');
        document.getElementById('postInspectionActions').classList.add('d-none');
        const statusBadge = document.getElementById('inspectionStatus');

        // Update Badge
        statusBadge.classList.remove('bg-info', 'bg-success', 'bg-secondary', 'bg-danger');
        statusBadge.classList.add('bg-warning');
        statusBadge.innerText = "Inspecting";
        fetchCurrentState();
    } else if (fuze_details.fuze_inspection_status == "Stopped") {
        // Finalize UI after inspection
        document.getElementById('preInspectionActions').classList.remove('d-none');
        document.getElementById('activeInspectionActions').classList.add('d-none');
        document.getElementById('postInspectionActions').classList.add('d-none');
        const statusBadge = document.getElementById('inspectionStatus');

        // Update Badge
        statusBadge.classList.remove('bg-info', 'bg-success', 'bg-secondary', 'bg-danger');
        statusBadge.classList.add('bg-danger');
        statusBadge.innerText = "Stopped";
    } else if (fuze_details.fuze_inspection_status == "Failed") {
        // Finalize UI after inspection
        document.getElementById('preInspectionActions').classList.remove('d-none');
        document.getElementById('activeInspectionActions').classList.add('d-none');
        document.getElementById('postInspectionActions').classList.add('d-none');
        const statusBadge = document.getElementById('inspectionStatus');

        // Update Badge
        statusBadge.classList.remove('bg-info', 'bg-success', 'bg-secondary', 'bg-danger');
        statusBadge.classList.add('bg-danger');
        statusBadge.innerText = "Failed";
    }
    else if (fuze_details.fuze_inspection_status == "Paused") {
        document.getElementById('preInspectionActions').classList.add('d-none');
        document.getElementById('activeInspectionActions').classList.remove('d-none');
        document.getElementById('postInspectionActions').classList.add('d-none');

        // Update Status Badge
        const statusBadge = document.getElementById('inspectionStatus');
        statusBadge.classList.remove('bg-info', 'bg-success', 'bg-warning', 'bg-danger');
        statusBadge.classList.add('bg-secondary');
        statusBadge.innerText = "Paused";

        document.getElementById('pauseBtn').classList.add('d-none');
        document.getElementById('resumeBtn').classList.remove('d-none');
        fetchCurrentState();
    } else {
        document.getElementById('preInspectionActions').classList.remove('d-none');
        document.getElementById('activeInspectionActions').classList.add('d-none');
        document.getElementById('postInspectionActions').classList.add('d-none');

        // Update Status Badge
        const statusBadge = document.getElementById('inspectionStatus');
        statusBadge.classList.remove('bg-info', 'bg-secondary', 'bg-success', 'bg-warning', 'bg-danger');
        statusBadge.classList.add('bg-primary');
        statusBadge.innerText = "Pending";
        fetchCurrentState();
    }

    setPrimer1ALInspectionDetails(fuze_details.inspection || {});
}

function setPrimer1ALInspectionDetails(data) {
    const parameters = [
        { label: "Improper Cleanliness Appearance", subtext: "Check the cleanliness of the primer", key: "cleanliness_appearance", status: data.cleanliness_appearance },
        { label: "Incorrect LOT NUMBER", subtext: "Check whether the lot number is present or not", key: "lot_number_match", status: data.lot_number_match },
        { label: "Crack/Damage on Magazine", subtext: "Check for damage and cracks on the primer", key: "magazine_crack_damage", status: data.magazine_crack_damage !== null && data.magazine_crack_damage !== undefined ? !data.magazine_crack_damage : null, isNegative: true },
        { label: "Paper Liner Damage", subtext: "Check whether the paper is present or not and check for spillage of gun powder", key: "paper_liner_damage_spillage", status: data.paper_liner_damage_spillage !== null && data.paper_liner_damage_spillage !== undefined ? !data.paper_liner_damage_spillage : null, isNegative: true },
        { label: "Absence/Damage of Rubber Ring", subtext: "Check for absence, damage, or incorrect assembly of the rubber ring", key: "rubber_ring_assembly", status: data.rubber_ring_assembly },
        { label: "Improper Assembly of Magazine to Primer Body", subtext: "Check for improper assembly of the magazine to the primer body", key: "magazine_assembly", status: data.magazine_assembly }
    ];

    renderParameters(parameters);
}

function renderParameters(parameters) {
    const container = document.getElementById("inspectionParameters");
    container.innerHTML = "";

    parameters.forEach(param => {
        const isChecked = param.status === true;
        const badgeColor = param.status === true ? "text-success" : (param.status === false ? "text-danger" : "text-muted");
        const statusText = param.status === true ? "PASSED" : (param.status === false ? "REJECTED" : "PENDING");
        const subtextHtml = param.subtext ? `<small class="text-muted d-block font-monospace" style="font-size: 0.75rem;">${param.subtext}</small>` : '';

        const item = `
            <div class="col-12 col-sm-6">
                <div class="p-2 border rounded bg-white shadow-sm d-flex justify-content-between align-items-center param-card h-100 gap-2">
                    <div class="flex-grow-1" style="min-width: 0;">
                        <span class="fw-bold small d-block text-truncate" title="${param.label}">${param.label}</span>
                        ${subtextHtml}
                        <span class="badge bg-light border ${badgeColor} font-monospace mt-1" style="font-size: 0.7rem;" id="${param.key}_status_badge">${statusText}</span>
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
    const fuzeId = document.getElementById("fuzeId").value;

    fetch("/fuze/update_parameter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            fuze_id: parseInt(fuzeId),
            parameter_key: paramKey,
            value: dbValue
        })
    })
    .then(res => res.json())
    .then(data => {
        const badge = document.getElementById(`${paramKey}_status_badge`);
        if (badge) {
            badge.className = `badge bg-light border ${isChecked ? "text-success" : "text-danger"} font-monospace mt-1`;
            badge.innerText = isChecked ? "PASSED (MANUAL)" : "REJECTED (MANUAL)";
        }
    })
    .catch(err => console.error("Error updating fuze parameter:", err));
}

function startInspection() {
    fetch(`/fuze/start_inspection`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            fuze_id: Number(document.getElementById('fuzeId').value),
            fuze_type: document.getElementById('fuzeType').innerText,
            lot_id: Number(document.getElementById('lotId').value),
        })
    })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            if (data.status) {
                // Finalize UI after inspection
                document.getElementById('preInspectionActions').classList.add('d-none');
                document.getElementById('activeInspectionActions').classList.remove('d-none');
                document.getElementById('postInspectionActions').classList.add('d-none');
                const statusBadge = document.getElementById('inspectionStatus');

                // Update Badge
                statusBadge.classList.remove('bg-info', 'bg-success', 'bg-secondary', 'bg-danger');
                statusBadge.classList.add('bg-warning');
                statusBadge.innerText = "Inspecting";

                // Reset buttons state
                document.getElementById('pauseBtn').classList.remove('d-none');
                document.getElementById('resumeBtn').classList.add('d-none');

            } else {
                revertInspectionUI();
                console.error('Error starting inspection:', data.message);
                alert("Error starting inspection: " + data.message);
            }
        })
        .catch(error => {
            console.error('Error starting inspection:', error);
            revertInspectionUI();
        });
}

function updateStatus(status) {
    const fuzeId = Number(document.getElementById('fuzeId').value);

    fetch(`/fuze/update_status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            fuze_id: fuzeId,
            status: status
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status) {
                const newStatus = (data.object && typeof data.object.status === 'string') ? data.object.status : status;
                console.log(`Status updated to ${newStatus}`);
                updateUIForStatus(newStatus);
            } else {
                alert("Error updating status: " + data.message);
            }
        })
        .catch(error => console.error('Error updating status:', error));
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
    } else if (status === "Inspecting") {
        resumeBtn.classList.add('d-none');
        pauseBtn.classList.remove('d-none');
        statusBadge.classList.replace('bg-secondary', 'bg-warning');
        statusBadge.innerText = "Inspecting";
    } else if (status === "Stopped") {
        document.getElementById('activeInspectionActions').classList.add('d-none');
        document.getElementById('preInspectionActions').classList.remove('d-none');
        revertInspectionUI();
        statusBadge.innerText = "Stopped";
        statusBadge.classList.remove('bg-warning', 'bg-secondary');
        statusBadge.classList.add('bg-danger');
    }
}

function revertInspectionUI() {
    const startBtn = document.getElementById('startInspectionBtn');
    const spinner = startBtn.querySelector('.spinner-border');
    const btnText = startBtn.querySelector('.btn-text');

    startBtn.disabled = false;
    spinner.classList.add('d-none');
    btnText.textContent = "Start Inspection";
}

function moveToNextFuze() {
    const lotId = Number(document.getElementById('lotId').value);
    triggerNextFuzeSequence(lotId);
}

function triggerPreviousFuzeSequence() {
    const lotId = document.getElementById('lotId').value;

    fetch(`/lots/decrement_fuze_sequence/${lotId}`, {
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
                alert("Error moving to previous primer: " + data.message);
                window.location.reload();
            }
        })
        .catch(error => {
            console.error('Error moving to previous primer:', error);
            alert("Error moving to previous primer. Please check your connection.");
            window.location.reload();
        });
}

function triggerNextFuzeSequence(lotId) {
    fetch(`/lots/increment_fuze_sequence/${lotId}`, {
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
                    showToast("All primers completed! Redirecting...", 'success');
                } else {
                    alert("All primers completed! Redirecting...");
                }

                setTimeout(() => {
                    backToSelection();
                }, 3000);
            }
        })
        .catch(error => {
            console.error('Error moving to next primer:', error);
            alert("Error moving to next primer. Please check your connection.");
            window.location.reload();
        });
}

function loadBoxesForSelection() {
    const lotId = document.getElementById('lotId').value;
    const boxSearchResults = document.getElementById('boxSearchResults');
    boxSearchResults.innerHTML = '<div class="text-center text-muted p-3"><div class="spinner-border spinner-border-sm text-primary" role="status"></div> Loading boxes...</div>';

    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('boxSelectionModal'));
    modal.show();

    fetch(`/lots/get_box_for_fuze_reference/${lotId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status && data.object && data.object.length > 0) {
                boxSearchResults.innerHTML = '';
                data.object.forEach(box => {
                    const btn = document.createElement('button');
                    btn.type = 'button';
                    btn.className = 'list-group-item list-group-item-action border-0 mb-2 rounded shadow-sm d-flex justify-content-between align-items-center';
                    btn.innerHTML = `
                        <div>
                            <span class="fw-bold text-primary">Box No: ${box.box_number}</span>
                            <br>
                            <small class="text-muted">Type: ${box.box_type}</small>
                        </div>
                        <span class="material-symbols-outlined text-muted fs-5">chevron_right</span>
                    `;
                    btn.onclick = () => selectBoxForFuze(box.id, box.box_number);
                    boxSearchResults.appendChild(btn);
                });
            } else {
                boxSearchResults.innerHTML = '<div class="text-center text-muted p-3">No boxes found for this lot.</div>';
            }
        })
        .catch(error => {
            console.error('Error loading boxes:', error);
            boxSearchResults.innerHTML = '<div class="text-center text-danger p-3">Error loading boxes.</div>';
        });
}

function selectBoxForFuze(boxId, boxNumber) {
    const fuzeId = document.getElementById('fuzeId').value;

    // Update UI immediately (optimistic)
    const boxNumberEl = document.getElementById('boxNumber');
    boxNumberEl.innerText = boxNumber;

    // Hide modal
    const modalEl = document.getElementById('boxSelectionModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) {
        modal.hide();
    }

    // Call API to link
    fetch('/fuze/update_box_reference', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            fuze_id: parseInt(fuzeId),
            box_id: parseInt(boxId)
        })
    })
        .then(response => response.json())
        .then(data => {
            if (!data.status) {
                console.error("Failed to update Box ID:", data.message);
                alert("Could not save the selected box.");
                // optionally reload to get correct state
            } else {
                // Optional: trigger reload if you want all states refreshed
                // window.location.reload();
                console.log("Box linked successfully");
            }
        })
        .catch(error => {
            console.error("Error linking box to primer:", error);
        });
}
