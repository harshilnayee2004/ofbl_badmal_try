// When  the Page loads
document.addEventListener('DOMContentLoaded', function () {
    connectLotInspectionSocket();
});

// WebSocket Connection
let lotInspectionSocket;
const lotInspectionSocketUrl = `ws://${window.location.host}/ws/inspection_lot`;
let reconnectInterval = 3000; // 3 seconds

function connectLotInspectionSocket() {
    lotInspectionSocket = new WebSocket(lotInspectionSocketUrl);

    lotInspectionSocket.onopen = function () {
        console.log("Inspection WebSocket connected");
    };

    lotInspectionSocket.onmessage = function (event) {
        onmessageLotInspection(JSON.parse(event.data))
    };

    lotInspectionSocket.onclose = function (event) {
        console.log("Inspection WebSocket connection closed. Reconnecting in " + reconnectInterval / 1000 + " seconds...");
        setTimeout(connectLotInspectionSocket, reconnectInterval);
    };

    lotInspectionSocket.onerror = function (error) {
        console.error("Inspection WebSocket error: ", error);
        lotInspectionSocket.close(); // Trigger onclose to reconnect
    };
}

function onmessageLotInspection(data) {
    if (data.type === "new_box") {
        showAvailableBoxes()
    }
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

function fetchLogs(fuzeId) {
    const logContainer = document.getElementById('logContainer');
    if (!logContainer) return;

    logContainer.innerHTML = `
        <div class="d-flex justify-content-center align-items-center h-100 text-muted font-monospace py-3">
            <div class="spinner-border spinner-border-sm text-secondary me-2" role="status"></div>
            <span>Loading logs...</span>
        </div>`;

    fetch(`/fuze/get_fuze_logs/${fuzeId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status) {
                logContainer.innerHTML = "";
                if (!data.object || data.object.length === 0) {
                    logContainer.innerHTML = '<div class="d-flex align-items-center justify-content-center h-100 py-3 text-muted font-monospace"><span class="material-symbols-outlined me-2 fs-5" style="vertical-align: middle;">info</span><span>No logs found.</span></div>';
                } else {
                    data.object.forEach(log => appendLog(log));
                }
                connectLogWebSocket(fuzeId);
            }
        })
        .catch(error => {
            console.error('Error fetching logs:', error);
            logContainer.innerHTML = '<div class="d-flex align-items-center justify-content-center h-100 py-3 text-muted font-monospace"><span class="material-symbols-outlined me-2 fs-5 text-danger" style="vertical-align: middle;">error</span><span>Failed to load logs.</span></div>';
        });
}

function appendLog(log) {
    const logContainer = document.getElementById('logContainer');
    if (!logContainer) return;

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

let logSocket;
function connectLogWebSocket(fuzeId) {
    if (logSocket) {
        logSocket.close();
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const logSocketUrl = `${protocol}//${window.location.host}/ws/fuze_log/${fuzeId}`;

    logSocket = new WebSocket(logSocketUrl);

    logSocket.onopen = function () {
        console.log("Log WebSocket connected");
    };

    logSocket.onmessage = function (event) {
        const log = JSON.parse(event.data);
        // Clear "No logs found" if it's there
        const logContainer = document.getElementById('logContainer');
        if (logContainer && logContainer.querySelector('.text-muted')) {
            logContainer.innerHTML = "";
        }
        appendLog(log);
    };

    logSocket.onclose = function () {
        console.log("Log WebSocket closed. Reconnecting...");
        setTimeout(() => connectLogWebSocket(fuzeId), 3000);
    };

    logSocket.onerror = function (error) {
        console.error("Log WebSocket error:", error);
        logSocket.close();
    };
}


// WebSocket Connection
let inspection_fuze_socket;
const socketUrl = `ws://${window.location.host}/ws/inspection_fuze`;

function connectWebSocket() {
    inspection_fuze_socket = new WebSocket(socketUrl);

    inspection_fuze_socket.onopen = function () {
        console.log("Inspection WebSocket connected");
    };

    inspection_fuze_socket.onmessage = function (event) {
        onmessage(JSON.parse(event.data))
    };

    inspection_fuze_socket.onclose = function (event) {
        console.log("Inspection WebSocket connection closed. Reconnecting in " + reconnectInterval / 1000 + " seconds...");
        setTimeout(connectWebSocket, reconnectInterval);
    };

    inspection_fuze_socket.onerror = function (error) {
        console.error("Inspection WebSocket error: ", error);
        socket.close(); // Trigger onclose to reconnect
    };
}

document.addEventListener('DOMContentLoaded', function () {
    connectWebSocket();
});

let countdownInterval;
function startCountdown(duration) {
    if (countdownInterval) {
        clearInterval(countdownInterval);
    }
    let timer = duration;
    const waitingEl = document.getElementById('waitingTime');
    if (waitingEl) {
        waitingEl.classList.remove('placeholder-glow');
        waitingEl.innerText = timer + "s";
    }

    countdownInterval = setInterval(function () {
        const el = document.getElementById('waitingTime');
        if (--timer < 0) {
            clearInterval(countdownInterval);
            if (el) el.innerText = "0s";
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
    const el = document.getElementById('waitingTime');
    if (el) el.innerText = "0s";
}

function onmessage(data) {
    console.log("Message from server: ", data);
    if (!data || !data.type) return;

    if (data.type === "instruction") {
        const instructionEl = document.getElementById('instructionText');
        if (instructionEl) {
            instructionEl.innerText = data.object.text || "Please Wait...";
            instructionEl.classList.remove('placeholder-glow');
        }
        const waitingEl = document.getElementById('waitingTime');
        if (waitingEl) {
            waitingEl.classList.remove('placeholder-glow');
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
    } else if (data.type === "camera_position") {
        document.getElementById('cameraViewImage').src = `/api/cameras/stream/${data.object.position}`;
        if (window.inspectionOverlay) window.inspectionOverlay.setStream(`/api/cameras/stream/${data.object.position}`);
    } else if (data.type === "fuze_update") {
        if (data.object.inspection_status === "Completed") {
            // Finalize UI after inspection
            document.getElementById('preInspectionActions').classList.add('d-none');
            document.getElementById('activeInspectionActions').classList.add('d-none');
            document.getElementById('postInspectionActions').classList.remove('d-none');
            const statusBadge = document.getElementById('inspectionStatus');

            // Update Badge
            statusBadge.classList.remove('bg-warning', 'bg-info');
            statusBadge.classList.add('bg-success');
            statusBadge.innerText = "Completed";
        } else if (data.object.inspection_status === "Failed") {
            // Finalize UI after inspection
            document.getElementById('preInspectionActions').classList.add('d-none');
            document.getElementById('activeInspectionActions').classList.remove('d-none');
            document.getElementById('postInspectionActions').classList.add('d-none');
            const statusBadge = document.getElementById('inspectionStatus');

            // Update Badge
            statusBadge.classList.remove('bg-info', 'bg-success', 'bg-secondary', 'bg-danger');
            statusBadge.classList.add('bg-danger');
            statusBadge.innerText = "Failed";
        } else if (data.object.inspection_status === "Paused" || data.object.inspection_status === "Stopped" || data.object.inspection_status === "Inspecting") {
            // Call the UI update function if it exists in box_inspection_main.js
            if (typeof updateUIForStatus === 'function') {
                updateUIForStatus(data.object.inspection_status);
            }
        }else if (data.object.inspection_status === "button_pressed") {
            if(data.object.message === "start"){
                document.getElementById('startInspectionBtn').click();
            }else if(data.object.message === "resume"){
                document.getElementById('resumeBtn').click();
            }else if(data.object.message === "pause"){
                document.getElementById('pauseBtn').click();
            }else if(data.object.message === "stop"){
                document.getElementById('stopBtn').click();
            }
        }

    } else if (data.type === "parameter_update" && data.object) {
        const key = data.object.parameter_key;
        const val = data.object.value;
        const checkbox = document.getElementById(`${key}_checkbox`);
        if (checkbox) {
            checkbox.checked = (key.includes("damage") || key.includes("crack") || key.includes("spillage")) ? !val : Boolean(val);
        }
        const badge = document.getElementById(`${key}_status_badge`);
        if (badge) {
            const isPass = checkbox ? checkbox.checked : Boolean(val);
            badge.className = `badge bg-light border ${isPass ? "text-success" : "text-danger"} font-monospace mt-1`;
            badge.innerText = isPass ? "PASSED" : "REJECTED";
        }
    } else if (data.type === "inspection_update") {
        const updateData = data.object;
        Object.keys(updateData).forEach(key => {
            const checkbox = document.getElementById(`${key}_checkbox`);
            if (checkbox) {
                checkbox.checked = updateData[key] === true;
            }
        });
    }
}

