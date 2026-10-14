// When  the Page loads
document.addEventListener('DOMContentLoaded', function () {

});


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

function fetchLogs(boxId) {
    const logContainer = document.getElementById('logContainer');
    if (!logContainer) return;

    logContainer.innerHTML = `
        <div class="d-flex justify-content-center align-items-center h-100 text-muted font-monospace py-3">
            <div class="spinner-border spinner-border-sm text-secondary me-2" role="status"></div>
            <span>Loading logs...</span>
        </div>`;

    fetch(`/box/get_box_logs/${boxId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status) {
                logContainer.innerHTML = "";
                if (!data.object || data.object.length === 0) {
                    logContainer.innerHTML = '<div class="d-flex align-items-center justify-content-center h-100 py-3 text-muted font-monospace"><span class="material-symbols-outlined me-2 fs-5" style="vertical-align: middle;">info</span><span>No logs found.</span></div>';
                } else {
                    data.object.forEach(log => appendLog(log));
                }
                connectLogWebSocket(boxId);
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
function connectLogWebSocket(boxId) {
    if (!boxId) return;
    if (logSocket) {
        logSocket.close();
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const logSocketUrl = `${protocol}//${window.location.host}/ws/box_log/${boxId}`;

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
        setTimeout(() => connectLogWebSocket(boxId), 3000);
    };

    logSocket.onerror = function (error) {
        console.error("Log WebSocket error:", error);
        logSocket.close();
    };
}



// WebSocket Connection
let socket;
const socketUrl = `ws://${window.location.host}/ws/inspection_box`;
let reconnectInterval = 3000; // 3 seconds

function connectWebSocket() {
    socket = new WebSocket(socketUrl);

    socket.onopen = function () {
        console.log("Inspection WebSocket connected");
    };

    socket.onmessage = function (event) {
        onmessage(JSON.parse(event.data))
    };

    socket.onclose = function (event) {
        console.log("Inspection WebSocket connection closed. Reconnecting in " + reconnectInterval / 1000 + " seconds...");
        setTimeout(connectWebSocket, reconnectInterval);
    };

    socket.onerror = function (error) {
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
}

function onmessage(data) {
    console.log("Message from server: ", data);
    if (data.type === "instruction") {
        const instructionEl = document.getElementById('instructionText');
        if (instructionEl) {
            instructionEl.innerText = data.object.text || "Please Wait...";
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
            imgEl.src = `/api/cameras/stream/${data.object.position}`;
        }
    } else if (data.type === "box_update") {
        const boxNm = document.getElementById("boxNumber");
        boxNm.innerHTML = data.object.box_number == null ? "--" : data.object.box_number
        boxNm.classList.remove('placeholder-glow');
        if (data.object.inspection_status === "Completed") {

            // Finalize UI after inspection
            document.getElementById('postInspectionActions').classList.remove('d-none');
            document.getElementById('activeInspectionActions').classList.add('d-none');
            document.getElementById('preInspectionActions').classList.add('d-none');

            // Update Status Badge
            const statusBadge = document.getElementById('inspectionStatus');
            statusBadge.classList.remove('bg-info', 'bg-danger', 'bg-warning', 'bg-secondary');
            statusBadge.classList.add('bg-success');
            statusBadge.innerText = "Completed";

            if (typeof showToast === 'function') {
                showToast("Inspection completed successfully.", "success");
            }

        } else if (data.object.inspection_status === "Failed") {

            document.getElementById('postInspectionActions').classList.add('d-none');
            document.getElementById('activeInspectionActions').classList.add('d-none');
            document.getElementById('preInspectionActions').classList.remove('d-none');

            // Update Status Badge
            const statusBadge = document.getElementById('inspectionStatus');
            statusBadge.classList.remove('bg-info', 'bg-success', 'bg-warning', 'bg-secondary');
            statusBadge.classList.add('bg-danger');
            statusBadge.innerText = "Failed";

            if (typeof showToast === 'function') {
                showToast("Inspection failed.", "error");
            }
        } else if (data.object.inspection_status === "Paused" || data.object.inspection_status === "Stopped" || data.object.inspection_status === "Inspecting") {
            // Call the UI update function if it exists in box_inspection_main.js
            if (typeof updateUIForStatus === 'function') {
                updateUIForStatus(data.object.inspection_status);
            }
        }
    } else if (data.type === "parameter_update" && data.object) {
        const key = data.object.parameter_key;
        const val = data.object.value;
        const checkbox = document.getElementById(`${key}_checkbox`);
        if (checkbox) {
            checkbox.checked = key.includes("interior_rust") ? !val : Boolean(val);
        }
        const badge = document.getElementById(`${key}_status_badge`);
        if (badge) {
            const isPass = checkbox ? checkbox.checked : Boolean(val);
            badge.className = `badge ${isPass ? "badge-passed" : "badge-rejected"} font-monospace mt-1`;
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

