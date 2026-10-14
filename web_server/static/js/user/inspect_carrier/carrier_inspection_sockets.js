// ==========================================
// Carrier Inspection Sockets & Log Streaming
// ==========================================

function fetchLogs(carrierId) {
    const logContainer = document.getElementById('logContainer');
    if (!logContainer) return;

    logContainer.innerHTML = `
        <div class="d-flex justify-content-center align-items-center h-100 text-muted font-monospace py-3">
            <div class="spinner-border spinner-border-sm text-secondary me-2" role="status"></div>
            <span>Loading logs...</span>
        </div>`;

    fetch(`/carrier/get_carrier_logs/${carrierId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status) {
                logContainer.innerHTML = "";
                if (!data.object || data.object.length === 0) {
                    logContainer.innerHTML = '<div class="d-flex align-items-center justify-content-center h-100 py-3 text-muted font-monospace"><span class="material-symbols-outlined me-2 fs-5" style="vertical-align: middle;">info</span><span>No logs found.</span></div>';
                } else {
                    data.object.forEach(log => appendLog(log));
                }
                connectLogWebSocket(carrierId);
            }
        })
        .catch(error => {
            console.error('Error fetching logs:', error);
            logContainer.innerHTML = '<div class="d-flex align-items-center justify-content-center h-100 py-3 text-muted font-monospace"><span class="material-symbols-outlined me-2 fs-5 text-danger" style="vertical-align: middle;">error</span><span>Failed to load logs.</span></div>';
        });
}

function formatLogTime(dateTimeStr) {
    if (!dateTimeStr) return new Date().toLocaleTimeString();
    try {
        const d = new Date(dateTimeStr);
        if (isNaN(d.getTime())) return dateTimeStr;
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
    } catch {
        return dateTimeStr;
    }
}

function appendLog(log) {
    const logContainer = document.getElementById('logContainer');
    if (!logContainer) return;

    // Remove empty placeholder
    const placeholder = logContainer.querySelector('.text-muted');
    if (placeholder) {
        placeholder.remove();
    }

    const logEntry = document.createElement('div');
    logEntry.className = "log-entry font-monospace";
    const timeStr = formatLogTime(log.date_time);
    logEntry.innerHTML = `
        <span class="log-timestamp">[${timeStr}]</span> 
        <span class="log-sep fw-bold"> : </span> 
        <span class="log-desc">${log.description}</span>
    `;
    logContainer.appendChild(logEntry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

let logSocket = null;
function connectLogWebSocket(carrierId) {
    if (!carrierId) return;

    if (logSocket) {
        try { logSocket.close(); } catch (e) {}
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const logSocketUrl = `${protocol}//${window.location.host}/ws/carrier_log/${carrierId}`;

    logSocket = new WebSocket(logSocketUrl);

    logSocket.onopen = function () {
        console.log("Carrier Log WebSocket connected");
    };

    logSocket.onmessage = function (event) {
        try {
            const data = JSON.parse(event.data);
            const logContainer = document.getElementById('logContainer');
            if (logContainer && logContainer.querySelector('.text-muted')) {
                logContainer.innerHTML = "";
            }
            if (data && data.description) {
                appendLog(data);
            }
        } catch (e) {
            console.error("Log WS parse error:", e);
        }
    };

    logSocket.onclose = function () {
        console.log("Carrier Log WebSocket closed. Reconnecting...");
        setTimeout(() => connectLogWebSocket(carrierId), 3000);
    };

    logSocket.onerror = function (error) {
        console.error("Carrier Log WebSocket error:", error);
        try { logSocket.close(); } catch (e) {}
    };
}

let inspectionSocket = null;
const reconnectInterval = 3000;

function connectInspectionWebSocket() {
    if (inspectionSocket) {
        try { inspectionSocket.close(); } catch (e) {}
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/inspection_carrier`;

    inspectionSocket = new WebSocket(wsUrl);

    inspectionSocket.onopen = function () {
        console.log("Carrier Inspection WebSocket connected");
    };

    inspectionSocket.onmessage = function (event) {
        try {
            const data = JSON.parse(event.data);
            onInspectionSocketMessage(data);
        } catch (e) {
            console.error("Carrier Inspection WS parse error:", e);
        }
    };

    inspectionSocket.onclose = function () {
        console.log("Carrier Inspection WebSocket connection closed. Reconnecting in " + reconnectInterval / 1000 + " seconds...");
        setTimeout(connectInspectionWebSocket, reconnectInterval);
    };

    inspectionSocket.onerror = function (error) {
        console.error("Carrier Inspection WebSocket error:", error);
        try { inspectionSocket.close(); } catch (e) {}
    };
}

let countdownInterval = null;
function startCountdown(duration) {
    if (countdownInterval) {
        clearInterval(countdownInterval);
    }
    let timer = duration;
    const waitingEl = document.getElementById('waitingTime');
    if (waitingEl) {
        waitingEl.innerText = timer > 0 ? timer + "s" : "";
    }

    countdownInterval = setInterval(function () {
        const el = document.getElementById('waitingTime');
        if (--timer < 0) {
            clearInterval(countdownInterval);
            if (el) el.innerText = "";
            return;
        }
        if (el) el.innerText = timer + "s";
    }, 1000);
}

function stopCountdown() {
    if (countdownInterval) {
        clearInterval(countdownInterval);
        countdownInterval = null;
    }
}

function onInspectionSocketMessage(data) {
    console.log("Carrier Inspection Socket message:", data);
    if (!data || !data.type) return;

    if (data.type === "instruction") {
        const instructionEl = document.getElementById('instructionText');
        if (instructionEl) {
            instructionEl.innerText = data.object.text || "Please Wait...";
            instructionEl.classList.remove('placeholder-glow');
        }
        if (data.object.wait_time !== undefined) {
            startCountdown(data.object.wait_time);
        }
    } else if (data.type === "recording_status") {
        const indicator = document.getElementById('recordingIndicator');
        if (indicator) {
            if (data.object.status) {
                indicator.classList.remove('d-none');
            } else {
                indicator.classList.add('d-none');
            }
        }
    } else if (data.type === "camera_position" && data.object) {
        const titleEl = document.getElementById('cameraViewTitle');
        if (titleEl) {
            titleEl.innerText = data.object.position;
        }
        const imgEl = document.getElementById('cameraViewImage');
        if (imgEl) {
            imgEl.src = `/api/cameras/stream/${data.object.position}?t=${Date.now()}`;
        }
    } else if (data.type === "carrier_update") {
        const carrierNm = document.getElementById("carrierNumber");
        if (carrierNm && data.object.carrier_number !== undefined) {
            carrierNm.innerText = data.object.carrier_number == null ? "--" : data.object.carrier_number;
            carrierNm.classList.remove('placeholder-glow');
        }

        const statusBadge = document.getElementById('inspectionStatus');
        const status = data.object.carrier_inspection_status || data.object.inspection_status;

        if (status === "Completed") {
            document.getElementById('postInspectionActions').classList.remove('d-none');
            document.getElementById('activeInspectionActions').classList.add('d-none');
            document.getElementById('preInspectionActions').classList.add('d-none');

            if (statusBadge) {
                statusBadge.className = `badge font-monospace ${data.object.acceptance_status === false ? 'badge-rejected' : 'badge-passed'}`;
                statusBadge.innerText = data.object.acceptance_status === false ? "Rejected" : "Completed";
            }

            if (typeof showToast === 'function') {
                showToast("Carrier inspection completed.", "success");
            }
        } else if (status === "Failed") {
            document.getElementById('postInspectionActions').classList.add('d-none');
            document.getElementById('activeInspectionActions').classList.add('d-none');
            document.getElementById('preInspectionActions').classList.remove('d-none');

            if (statusBadge) {
                statusBadge.className = 'badge badge-rejected font-monospace';
                statusBadge.innerText = "Failed";
            }

            if (typeof showToast === 'function') {
                showToast("Carrier inspection failed.", "danger");
            }
        } else if (status === "Paused" || status === "Stopped" || status === "Inspecting") {
            if (typeof updateUIForStatus === 'function') {
                updateUIForStatus(status);
            }
        } else if (status === "button_pressed") {
            if (data.object.message === "start") {
                document.getElementById('startInspectionBtn')?.click();
            } else if (data.object.message === "resume") {
                document.getElementById('resumeBtn')?.click();
            } else if (data.object.message === "pause") {
                document.getElementById('pauseBtn')?.click();
            } else if (data.object.message === "stop") {
                document.getElementById('stopBtn')?.click();
            }
        }
    } else if (data.type === "parameter_update" && data.object) {
        const key = data.object.parameter_key;
        const val = data.object.value;
        const checkbox = document.getElementById(`${key}_checkbox`);
        if (checkbox) {
            checkbox.checked = (key.includes("damage") || key.includes("rusty")) ? !val : Boolean(val);
        }
        const badge = document.getElementById(`${key}_status_badge`);
        if (badge) {
            const isPass = checkbox ? checkbox.checked : Boolean(val);
            badge.className = `badge ${isPass ? "badge-passed" : "badge-rejected"} font-monospace mt-1`;
            badge.innerText = isPass ? "PASSED" : "REJECTED";
        }
    } else if (data.type === "inspection_update" && data.object) {
        const updateData = data.object;
        Object.keys(updateData).forEach(key => {
            const checkbox = document.getElementById(`${key}_checkbox`);
            if (checkbox) {
                checkbox.checked = (key.includes("damage") || key.includes("rusty")) ? !updateData[key] : updateData[key] === true;
            }
            const badge = document.getElementById(`${key}_status_badge`);
            if (badge) {
                const isPass = checkbox ? checkbox.checked : updateData[key] === true;
                badge.className = `badge ${isPass ? "badge-passed" : "badge-rejected"} font-monospace mt-1`;
                badge.innerText = isPass ? "PASSED" : "REJECTED";
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', function () {
    connectInspectionWebSocket();
});
