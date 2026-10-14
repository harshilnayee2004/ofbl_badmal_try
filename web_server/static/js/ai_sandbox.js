/**
 * AI Model Visual Testing Sandbox (Image & Video Inspection)
 * Supports live frame-by-frame RF-DETR inference on uploaded videos and images.
 */

// ==========================================
// IMAGE TESTING SANDBOX
// ==========================================
async function runModelTest() {
    const fileInput = document.getElementById('testImageInput');
    const modelSelect = document.getElementById('testModelSelect');
    const runBtn = document.getElementById('runTestBtn');
    const spinner = document.getElementById('testSpinner');

    if (!fileInput.files || fileInput.files.length === 0) {
        alert('Please select an image file first.');
        return;
    }

    const file = fileInput.files[0];
    const modelKey = modelSelect.value;

    runBtn.disabled = true;
    spinner.classList.remove('d-none');

    const formData = new FormData();
    formData.append('image', file);

    const startTime = performance.now();

    try {
        const aiUrl = `/ai_server/inspect/${modelKey}`;
        const res = await fetch(aiUrl, {
            method: 'POST',
            body: formData
        });

        if (!res.ok) {
            throw new Error(`AI Server returned status ${res.status}: ${await res.text()}`);
        }

        const data = await res.json();
        const elapsed = Math.round(performance.now() - startTime);
        const badge = document.getElementById('inferenceTimeBadge');
        if (badge) badge.innerText = `${elapsed} ms`;

        renderTestResults(file, data);

    } catch (err) {
        console.error('Test error:', err);
        alert(`Inspection failed: ${err.message}`);
    } finally {
        runBtn.disabled = false;
        spinner.classList.add('d-none');
    }
}

function renderTestResults(file, data) {
    const placeholder = document.getElementById('canvasPlaceholder');
    const canvas = document.getElementById('testResultCanvas');
    const decisionCard = document.getElementById('decisionCard');
    const decisionText = document.getElementById('decisionText');
    const checklistContainer = document.getElementById('checklistContainer');
    const detectionsList = document.getElementById('detectionsList');
    const detCount = document.getElementById('detCount');

    // Overall Decision
    const isPass = data.overall === 'PASS';
    decisionCard.className = `card border-0 shadow-sm ${isPass ? 'bg-success text-white' : 'bg-danger text-white'}`;
    decisionText.className = 'fw-bold mb-0 text-white';
    decisionText.innerText = isPass ? 'ACCEPTED (PASS)' : 'DEFECT DETECTED (REJECT)';

    // Criteria Checklist
    checklistContainer.innerHTML = '';
    if (data.checks && data.checks.length > 0) {
        data.checks.forEach(c => {
            const pass = c.status === 'PASS';
            const item = document.createElement('div');
            item.className = `d-flex align-items-center justify-content-between p-2 mb-1 rounded ${pass ? 'bg-success-subtle text-success-emphasis' : 'bg-danger-subtle text-danger-emphasis'}`;
            item.innerHTML = `
                <div class="d-flex align-items-center gap-2">
                    <span class="material-symbols-outlined fs-6">${pass ? 'check_circle' : 'cancel'}</span>
                    <span class="small fw-semibold">${c.label || c.id}</span>
                </div>
                <span class="badge ${pass ? 'bg-success' : 'bg-danger'}">${c.status}</span>
            `;
            checklistContainer.appendChild(item);
        });
    } else {
        checklistContainer.innerHTML = '<div class="text-muted small text-center py-3">No specific checks returned</div>';
    }

    // Extract detections
    let rawDets = [];
    if (data.messages) {
        const detMsg = data.messages.find(m => m.type === 'detections');
        if (detMsg && detMsg.detections) {
            rawDets = detMsg.detections.filter(d => d.box !== null);
        }
    }

    detCount.innerText = rawDets.length;
    detectionsList.innerHTML = '';
    if (rawDets.length === 0) {
        detectionsList.innerHTML = '<div class="text-muted small text-center py-3">No bounding boxes detected</div>';
    } else {
        rawDets.forEach(d => {
            const pass = d.status === 'PASS';
            const row = document.createElement('div');
            row.className = 'd-flex align-items-center justify-content-between p-1 border-bottom small';
            row.innerHTML = `
                <span class="font-monospace fw-bold ${pass ? 'text-success' : 'text-danger'}">${d.class_name}</span>
                <span class="badge bg-light text-dark border">${Math.round(d.score * 100)}%</span>
            `;
            detectionsList.appendChild(row);
        });
    }

    // Render Canvas
    const img = new Image();
    img.onload = () => {
        placeholder.classList.add('d-none');
        canvas.classList.remove('d-none');

        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);

        rawDets.forEach(d => {
            const [x1, y1, x2, y2] = d.box;
            const isGood = d.status === 'PASS';
            const color = isGood ? '#00e676' : '#ff1744';

            ctx.strokeStyle = color;
            ctx.lineWidth = Math.max(3, Math.round(canvas.width / 400));
            ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

            const label = `${d.class_name} ${(d.score * 100).toFixed(1)}%`;
            ctx.font = `bold ${Math.max(14, Math.round(canvas.width / 60))}px sans-serif`;
            const textWidth = ctx.measureText(label).width;
            const textHeight = Math.max(16, Math.round(canvas.width / 55));

            ctx.fillStyle = color;
            ctx.fillRect(x1, Math.max(0, y1 - textHeight - 6), textWidth + 12, textHeight + 6);

            ctx.fillStyle = '#000000';
            ctx.fillText(label, x1 + 6, Math.max(textHeight, y1 - 4));
        });
    };
    img.src = URL.createObjectURL(file);
}

// ==========================================
// VIDEO TESTING SANDBOX
// ==========================================
let videoFile = null;
let videoElement = null;
let videoCanvas = null;
let videoCtx = null;
let isVideoPlaying = false;       // kept for UI button state compatibility
let videoLoopId = null;           // unused in step mode, kept for safety
let isProcessingFrame = false;
let lastInferenceTime = 0;
let currentVideoDetections = [];
let videoFrameCount = 0;

// ── Step-by-step mode state ──────────────────────────────────────────────────
let isStepByStepRunning = false;
let stepStopRequested    = false;

/** Resolves after `ms` milliseconds. */
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

/**
 * Seeks the video element to `t` seconds and waits until the frame is ready.
 * Returns a promise that resolves on the `seeked` event.
 */
function seekAndWait(t) {
    return new Promise((resolve) => {
        const onSeeked = () => {
            videoElement.removeEventListener('seeked', onSeeked);
            resolve();
        };
        videoElement.addEventListener('seeked', onSeeked);
        videoElement.currentTime = t;
    });
}

/** Capture the current video frame to a Blob (JPEG). Returns null on failure. */
function captureVideoFrameBlob() {
    return new Promise((resolve) => {
        const w = videoElement.videoWidth  || 1280;
        const h = videoElement.videoHeight || 720;
        const off = document.createElement('canvas');
        off.width = w; off.height = h;
        try {
            off.getContext('2d').drawImage(videoElement, 0, 0, w, h);
        } catch (e) {
            resolve(null); return;           // video not decodable in browser
        }
        off.toBlob(resolve, 'image/jpeg', 0.88);
    });
}

/**
 * Core step-by-step loop.
 * Pauses the video, then walks through it one frame at a time:
 *   seek → capture → AI → show result → pause so officer can read → next
 */
async function runStepByStepLoop() {
    if (!videoElement || !videoFile) return;

    // Guard: if browser cannot decode, go straight to server scan
    if (videoElement.error) { runServerVideoScan(); return; }

    // Wait until metadata is ready
    if (!videoElement.duration) {
        await new Promise(res => { videoElement.addEventListener('loadedmetadata', res, { once: true }); });
    }

    isStepByStepRunning = true;
    stepStopRequested   = false;
    videoElement.pause();

    const fpsSelect   = document.getElementById('videoFpsSelect');
    const stepSec     = 1.0 / (parseInt(fpsSelect?.value) || 1);   // e.g. 1 FPS → 1.0s step
    const modelSelect = document.getElementById('videoModelSelect');
    const modelKey    = modelSelect ? modelSelect.value : 'primer_assembly';

    const duration       = videoElement.duration;
    let   currentTimeSec = 0;
    videoFrameCount      = 0;

    const progressBadge  = document.getElementById('videoProgressBadge');
    const inferenceBadge = document.getElementById('videoInferenceTimeBadge');
    const counter        = document.getElementById('videoFrameCounter');

    const fmt = (s) => {
        const m = Math.floor(s / 60).toString().padStart(2, '0');
        const sc = Math.floor(s % 60).toString().padStart(2, '0');
        return `${m}:${sc}`;
    };

    while (isStepByStepRunning && !stepStopRequested && currentTimeSec <= duration) {

        // ── 1. Seek & wait for frame ─────────────────────────────────
        await seekAndWait(currentTimeSec);
        updateVideoTimeline();
        videoFrameCount++;
        if (counter) counter.innerText = `Frame #${videoFrameCount}`;
        if (progressBadge) progressBadge.innerText = `Analyzing ${fmt(currentTimeSec)} …`;

        // ── 2. Capture frame ─────────────────────────────────────────
        const blob = await captureVideoFrameBlob();
        if (!blob) {
            // Browser cannot decode — fallback to full server scan
            stopVideoProcessing();
            runServerVideoScan();
            return;
        }

        // ── 3. Send to AI and await result ───────────────────────────
        const fd = new FormData();
        fd.append('image', blob, 'frame.jpg');
        const t0 = performance.now();
        try {
            const res = await fetch(`/ai_server/inspect/${modelKey}`, { method: 'POST', body: fd });
            if (res.ok) {
                const data = await res.json();
                const latency = Math.round(performance.now() - t0);
                if (inferenceBadge) inferenceBadge.innerText = `${latency} ms`;

                // ── 4. Render bounding boxes + update side panel ─────
                updateVideoDashboardData(data);
                renderVideoFrame();

                if (progressBadge) {
                    const verdict = data.overall === 'PASS' ? '✓ PASS' : '✗ REJECT';
                    progressBadge.innerText = `${fmt(currentTimeSec)} — ${verdict}`;
                    progressBadge.className = `badge font-monospace ${data.overall === 'PASS' ? 'bg-success' : 'bg-danger'}`;
                }
            }
        } catch (err) {
            console.error('Step-by-step AI error:', err);
        }

        // ── 5. Hold frame so the officer can read it ─────────────────
        await sleep(1500);

        // ── 6. Advance ───────────────────────────────────────────────
        currentTimeSec = Math.round((currentTimeSec + stepSec) * 1000) / 1000;
    }

    // ── Done ─────────────────────────────────────────────────────────
    isStepByStepRunning = false;
    isVideoPlaying      = false;
    if (progressBadge) {
        progressBadge.innerText = 'Scan Complete';
        progressBadge.className = 'badge font-monospace bg-secondary';
    }
    const playText = document.getElementById('playVideoText');
    const playIcon = document.getElementById('playVideoIcon');
    const playBtn  = document.getElementById('playVideoBtn');
    if (playText) playText.innerText = 'Replay';
    if (playIcon) playIcon.innerText = 'replay';
    if (playBtn)  playBtn.classList.replace('btn-warning', 'btn-danger');
}


let videoFrameCount = 0;

function onVideoFileSelected(event) {
    const file = event.target ? (event.target.files ? event.target.files[0] : null) : event;
    if (!file) return;

    videoFile = file;
    videoElement = document.getElementById('hiddenTestVideo');
    videoCanvas = document.getElementById('videoResultCanvas');
    videoCtx = videoCanvas ? videoCanvas.getContext('2d') : null;

    const placeholder = document.getElementById('videoCanvasPlaceholder');
    const playerWrapper = document.getElementById('videoPlayerWrapper');
    const playBtn = document.getElementById('playVideoBtn');
    const scanBtn = document.getElementById('serverScanBtn');
    const errorNotice = document.getElementById('videoErrorNotice');

    if (errorNotice) {
        errorNotice.classList.add('d-none');
        errorNotice.innerHTML = '';
    }

    stopVideoProcessing();
    currentVideoDetections = [];
    videoFrameCount = 0;

    // Immediately enable action buttons
    if (playBtn) playBtn.disabled = false;
    if (scanBtn) scanBtn.disabled = false;

    // Display the video container
    if (placeholder) placeholder.classList.add('d-none');
    if (playerWrapper) playerWrapper.classList.remove('d-none');

    // Attach event listeners before loading source
    videoElement.onloadedmetadata = () => {
        if (videoCanvas) {
            videoCanvas.width = videoElement.videoWidth || 1280;
            videoCanvas.height = videoElement.videoHeight || 720;
        }
        updateVideoTimeline();
    };

    videoElement.onloadeddata = () => {
        renderVideoFrame();
    };

    videoElement.onseeked = () => {
        renderVideoFrame();
    };

    videoElement.ontimeupdate = () => {
        updateVideoTimeline();
    };

    videoElement.onplay = () => {
        if (!isVideoPlaying) {
            startVideoProcessing();
        }
    };

    videoElement.onpause = () => {
        if (isVideoPlaying) {
            pauseVideoProcessing();
        }
    };

    videoElement.onended = () => {
        stopVideoProcessing();
        const playText = document.getElementById('playVideoText');
        const playIcon = document.getElementById('playVideoIcon');
        if (playText) playText.innerText = 'Replay';
        if (playIcon) playIcon.innerText = 'replay';
    };

    videoElement.onerror = () => {
        console.warn("Video element decode warning:", videoElement.error);
        if (errorNotice) {
            errorNotice.classList.remove('d-none');
            errorNotice.innerHTML = `
                <div class="d-flex align-items-center justify-content-between gap-3">
                    <div>
                        <strong class="d-block"><span class="material-symbols-outlined fs-6 align-middle text-warning">warning</span> Browser Playback Notice:</strong>
                        <span class="small">The browser could not decode this specific video format (e.g. raw CCTV/AVI or corrupted MP4 header). You can still run the <strong>Full Server Scan</strong> to analyze all frames directly through the AI engine!</span>
                    </div>
                    <button type="button" class="btn btn-sm btn-danger fw-bold text-nowrap" onclick="runServerVideoScan()">
                        <span class="material-symbols-outlined fs-6 align-middle me-1">manage_search</span> Run Server Scan
                    </button>
                </div>
            `;
        }
    };

    const objectUrl = URL.createObjectURL(file);
    videoElement.src = objectUrl;
    videoElement.load();
}

async function loadSampleVideo(url, name) {
    try {
        const resp = await fetch(url);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const blob = await resp.blob();
        const file = new File([blob], (name || "sample") + ".mp4", { type: "video/mp4" });
        onVideoFileSelected(file);
    } catch (err) {
        console.error("Could not load sample video:", err);
        alert("Failed to load sample video: " + err.message);
    }
}

function toggleVideoProcessing() {
    if (!videoElement) return;
    if (isStepByStepRunning) {
        stopVideoProcessing();
    } else {
        startVideoProcessing();
    }
}

function startVideoProcessing() {
    if (!videoElement) return;

    isVideoPlaying = true;
    const playText = document.getElementById('playVideoText');
    const playIcon = document.getElementById('playVideoIcon');
    const playBtn  = document.getElementById('playVideoBtn');
    if (playText) playText.innerText = 'Stop';
    if (playIcon) playIcon.innerText = 'stop';
    if (playBtn)  playBtn.classList.replace('btn-danger', 'btn-warning');

    // Reset position if at end
    if (videoElement.duration && videoElement.currentTime >= videoElement.duration - 0.1) {
        videoElement.currentTime = 0;
    }

    runStepByStepLoop();   // ← replaces the old requestAnimationFrame loop
}

function pauseVideoProcessing() {
    // In step-by-step mode, "pause" just stops the loop at the next iteration
    stepStopRequested = true;
    isVideoPlaying    = false;
    if (videoLoopId) cancelAnimationFrame(videoLoopId);

    const playText = document.getElementById('playVideoText');
    const playIcon = document.getElementById('playVideoIcon');
    const playBtn  = document.getElementById('playVideoBtn');
    if (playText) playText.innerText = 'Resume';
    if (playIcon) playIcon.innerText = 'play_arrow';
    if (playBtn)  playBtn.classList.replace('btn-warning', 'btn-danger');
}

function stopVideoProcessing() {
    stepStopRequested   = true;
    isStepByStepRunning = false;
    isVideoPlaying      = false;
    if (videoLoopId) cancelAnimationFrame(videoLoopId);

    const playText = document.getElementById('playVideoText');
    const playIcon = document.getElementById('playVideoIcon');
    const playBtn  = document.getElementById('playVideoBtn');
    if (playText) playText.innerText = 'Start Test';
    if (playIcon) playIcon.innerText = 'play_arrow';
    if (playBtn)  playBtn.classList.replace('btn-warning', 'btn-danger');
}

function resetVideoTest() {
    stopVideoProcessing();
    if (videoElement) videoElement.currentTime = 0;
    currentVideoDetections = [];
    videoFrameCount = 0;
    const counter = document.getElementById('videoFrameCounter');
    if (counter) counter.innerText = 'Frame 0';
    renderVideoFrame();
    const progressBadge = document.getElementById('videoProgressBadge');
    if (progressBadge) {
        progressBadge.innerText = '00:00 / 00:00';
        progressBadge.className = 'badge bg-secondary font-monospace';
    }
}

// runVideoRenderLoop kept as no-op for safety (no longer used)
function runVideoRenderLoop() { /* replaced by runStepByStepLoop */ }

function seekVideo(event) {
    if (!videoElement || !videoElement.duration) return;
    const barContainer = document.getElementById('videoProgressBarContainer');
    const rect = barContainer.getBoundingClientRect();
    const pos = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
    videoElement.currentTime = pos * videoElement.duration;
}

function updateVideoTimeline() {
    if (!videoElement || !videoElement.duration) return;
    const cur = videoElement.currentTime;
    const dur = videoElement.duration;
    const pct = (cur / dur) * 100;
    const bar = document.getElementById('videoProgressBar');
    if (bar) bar.style.width = `${pct}%`;
}


function renderVideoFrame() {
    if (!videoElement || !videoCanvas || !videoCtx) return;

    // Clear overlay canvas
    videoCtx.clearRect(0, 0, videoCanvas.width, videoCanvas.height);

    // Draw active bounding boxes on top of video
    if (currentVideoDetections && currentVideoDetections.length > 0) {
        currentVideoDetections.forEach(d => {
            const [x1, y1, x2, y2] = d.box;
            const isGood = d.status === 'PASS';
            const color = isGood ? '#00e676' : '#ff1744';

            videoCtx.strokeStyle = color;
            videoCtx.lineWidth = Math.max(3, Math.round(videoCanvas.width / 400));
            videoCtx.strokeRect(x1, y1, x2 - x1, y2 - y1);

            const label = `${d.class_name} ${(d.score * 100).toFixed(1)}%`;
            videoCtx.font = `bold ${Math.max(14, Math.round(videoCanvas.width / 60))}px sans-serif`;
            const textWidth = videoCtx.measureText(label).width;
            const textHeight = Math.max(16, Math.round(videoCanvas.width / 55));

            videoCtx.fillStyle = color;
            videoCtx.fillRect(x1, Math.max(0, y1 - textHeight - 6), textWidth + 12, textHeight + 6);

            videoCtx.fillStyle = '#000000';
            videoCtx.fillText(label, x1 + 6, Math.max(textHeight, y1 - 4));
        });
    }
}

async function sendCurrentVideoFrameToAI() {
    if (isProcessingFrame || !videoElement) return;
    if (videoElement.readyState < 2) return;

    isProcessingFrame = true;
    lastInferenceTime = performance.now();
    videoFrameCount++;

    const counter = document.getElementById('videoFrameCounter');
    if (counter) counter.innerText = `Frame #${videoFrameCount}`;

    // Offscreen frame capture canvas
    const offCanvas = document.createElement('canvas');
    offCanvas.width = videoElement.videoWidth || 1280;
    offCanvas.height = videoElement.videoHeight || 720;
    const offCtx = offCanvas.getContext('2d');

    try {
        offCtx.drawImage(videoElement, 0, 0, offCanvas.width, offCanvas.height);
    } catch (e) {
        isProcessingFrame = false;
        return;
    }

    offCanvas.toBlob(async (blob) => {
        if (!blob) {
            isProcessingFrame = false;
            return;
        }

        const modelSelect = document.getElementById('videoModelSelect');
        const modelKey = modelSelect ? modelSelect.value : 'primer_assembly';
        const formData = new FormData();
        formData.append('image', blob, 'video_frame.jpg');

        const t0 = performance.now();
        try {
            const aiUrl = `/ai_server/inspect/${modelKey}`;
            const res = await fetch(aiUrl, {
                method: 'POST',
                body: formData
            });

            if (res.ok) {
                const data = await res.json();
                const latency = Math.round(performance.now() - t0);
                const badge = document.getElementById('videoInferenceTimeBadge');
                if (badge) badge.innerText = `${latency} ms`;

                updateVideoDashboardData(data);
                renderVideoFrame();
            }
        } catch (err) {
            console.error('Frame inference error:', err);
        } finally {
            isProcessingFrame = false;
        }
    }, 'image/jpeg', 0.85);
}

function updateVideoDashboardData(data) {
    const decisionCard = document.getElementById('videoDecisionCard');
    const decisionText = document.getElementById('videoDecisionText');
    const checklistContainer = document.getElementById('videoChecklistContainer');
    const detectionsList = document.getElementById('videoDetectionsList');
    const detCount = document.getElementById('videoDetCount');

    // Overall Decision
    const isPass = data.overall === 'PASS';
    if (decisionCard && decisionText) {
        decisionCard.className = `card border-0 shadow-sm ${isPass ? 'bg-success text-white' : 'bg-danger text-white'}`;
        decisionText.className = 'fw-bold mb-0 text-white';
        decisionText.innerText = isPass ? 'ACCEPTED (PASS)' : 'DEFECT DETECTED (REJECT)';
    }

    // Criteria Checklist
    if (checklistContainer) {
        if (data.checks && data.checks.length > 0) {
            checklistContainer.innerHTML = '';
            data.checks.forEach(c => {
                const pass = c.status === 'PASS';
                const item = document.createElement('div');
                item.className = `d-flex align-items-center justify-content-between p-2 mb-1 rounded ${pass ? 'bg-success-subtle text-success-emphasis' : 'bg-danger-subtle text-danger-emphasis'}`;
                item.innerHTML = `
                    <div class="d-flex align-items-center gap-2">
                        <span class="material-symbols-outlined fs-6">${pass ? 'check_circle' : 'cancel'}</span>
                        <span class="small fw-semibold">${c.label || c.id}</span>
                    </div>
                    <span class="badge ${pass ? 'bg-success' : 'bg-danger'}">${c.status}</span>
                `;
                checklistContainer.appendChild(item);
            });
        }
    }

    // Parse Detections
    let rawDets = [];
    if (data.messages) {
        const detMsg = data.messages.find(m => m.type === 'detections');
        if (detMsg && detMsg.detections) {
            rawDets = detMsg.detections.filter(d => d.box !== null);
        }
    }

    currentVideoDetections = rawDets;
    if (detCount) detCount.innerText = rawDets.length;

    if (detectionsList) {
        detectionsList.innerHTML = '';
        if (rawDets.length === 0) {
            detectionsList.innerHTML = '<div class="text-muted small text-center py-2">No detections on current frame</div>';
        } else {
            rawDets.forEach(d => {
                const pass = d.status === 'PASS';
                const row = document.createElement('div');
                row.className = 'd-flex align-items-center justify-content-between p-1 border-bottom small';
                row.innerHTML = `
                    <span class="font-monospace fw-bold ${pass ? 'text-success' : 'text-danger'}">${d.class_name}</span>
                    <span class="badge bg-light text-dark border">${Math.round(d.score * 100)}%</span>
                `;
                detectionsList.appendChild(row);
            });
        }
    }
}

// ==========================================
// SERVER-SIDE FULL VIDEO SCAN (BATCH INSPECT)
// ==========================================
let scanFrameResults = [];     // all sampled frames from last server scan
let currentFrameViewerIdx = 0; // which frame is showing in the viewer

async function runServerVideoScan() {
    if (!videoFile) {
        alert('Please select a video file first.');
        return;
    }

    const modelSelect = document.getElementById('videoModelSelect');
    const modelKey = modelSelect ? modelSelect.value : 'primer_assembly';
    const fpsSelect = document.getElementById('videoFpsSelect');
    const sampleFps = fpsSelect ? fpsSelect.value : '2';

    const scanBtn = document.getElementById('serverScanBtn');
    const reportSection = document.getElementById('serverScanReportSection');

    const originalContent = scanBtn.innerHTML;
    scanBtn.disabled = true;
    scanBtn.innerHTML = '<span class="spinner-border spinner-border-sm text-danger"></span>';

    try {
        const formData = new FormData();
        formData.append('video', videoFile);

        const res = await fetch(`/ai_server/inspect_video/${modelKey}?sample_fps=${sampleFps}`, {
            method: 'POST',
            body: formData
        });

        if (!res.ok) {
            throw new Error(`Server returned ${res.status}: ${await res.text()}`);
        }

        const data = await res.json();
        scanFrameResults = data.sampled_results || [];
        currentFrameViewerIdx = 0;

        // ── Summary bar in the card header ──────────────────────────
        const isPass = data.overall === 'PASS';
        const defectFrames = scanFrameResults.filter(r => r.overall !== 'PASS');
        const summaryBar = document.getElementById('scanSummaryBar');
        if (summaryBar) {
            summaryBar.innerHTML = `
                <span class="badge ${isPass ? 'bg-success' : 'bg-danger'} fs-6 px-3">${data.overall}</span>
                <span class="text-white-50 small">${data.sampled_frames_count || 0} frames scanned</span>
                <span class="${defectFrames.length > 0 ? 'text-danger' : 'text-success'} small fw-bold">${defectFrames.length} defect${defectFrames.length !== 1 ? 's' : ''}</span>
                <span class="text-white-50 small">${data.total_frames_in_video || '?'} total video frames</span>
            `;
        }

        // ── Defect count badge in the frame list header ──────────────
        const defectBadge = document.getElementById('defectBadgeCount');
        if (defectBadge) defectBadge.textContent = `${defectFrames.length} defect${defectFrames.length !== 1 ? 's' : ''}`;

        // ── Build the scrollable frame list ─────────────────────────
        const listContainer = document.getElementById('frameListContainer');
        if (listContainer) {
            listContainer.innerHTML = '';
            scanFrameResults.forEach((fr, idx) => {
                const isDefect = fr.overall !== 'PASS';
                // collect defect class names for labels
                let defectLabels = '';
                if (isDefect && fr.messages) {
                    const detMsg = fr.messages.find(m => m.type === 'detections');
                    if (detMsg && detMsg.detections) {
                        const badDets = detMsg.detections.filter(d => d.status === 'DEFECT' && d.box !== null);
                        if (badDets.length > 0) {
                            defectLabels = badDets.map(d => `<span class="badge bg-danger-subtle text-danger-emphasis border border-danger-subtle me-1">${d.class_name}</span>`).join('');
                        }
                    }
                }
                const row = document.createElement('div');
                row.className = `d-flex align-items-start gap-2 px-3 py-2 border-bottom frame-list-row ${isDefect ? 'bg-danger-subtle' : ''}`;
                row.style.cursor = 'pointer';
                row.id = `frameRow_${idx}`;
                row.innerHTML = `
                    <div class="d-flex flex-column flex-grow-1 min-w-0">
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="font-monospace small fw-bold">${fr.timestamp}s</span>
                            <span class="badge ${isDefect ? 'bg-danger' : 'bg-success'} ms-2">${isDefect ? 'REJECT' : 'PASS'}</span>
                        </div>
                        <div class="small text-muted">Frame #${fr.frame_index}</div>
                        ${defectLabels ? `<div class="mt-1">${defectLabels}</div>` : ''}
                    </div>
                    <span class="material-symbols-outlined fs-5 text-secondary align-self-center">chevron_right</span>
                `;
                row.addEventListener('click', () => jumpToFrame(idx));
                listContainer.appendChild(row);
            });
        }

        // ── Show the section ─────────────────────────────────────────
        reportSection.classList.remove('d-none');
        reportSection.scrollIntoView({ behavior: 'smooth' });

        // ── Auto-jump to first defect frame (or frame 0) ────────────
        const firstDefectIdx = scanFrameResults.findIndex(r => r.overall !== 'PASS');
        jumpToFrame(firstDefectIdx >= 0 ? firstDefectIdx : 0);

    } catch (err) {
        console.error('Server scan failed:', err);
        alert(`Server video scan failed: ${err.message}`);
    } finally {
        scanBtn.disabled = false;
        scanBtn.innerHTML = originalContent;
    }
}

/**
 * Render one sampled frame into the frame viewer canvas.
 * Draws the base64 JPEG image first, then overlays bounding boxes.
 */
function jumpToFrame(idx) {
    if (!scanFrameResults || scanFrameResults.length === 0) return;
    idx = Math.max(0, Math.min(scanFrameResults.length - 1, idx));
    currentFrameViewerIdx = idx;

    // Highlight active row in list
    document.querySelectorAll('.frame-list-row').forEach(r => r.classList.remove('table-active', 'border-primary'));
    const activeRow = document.getElementById(`frameRow_${idx}`);
    if (activeRow) {
        activeRow.classList.add('table-active', 'border-primary');
        activeRow.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }

    // Update nav counter
    const navCounter = document.getElementById('frameNavCounter');
    if (navCounter) navCounter.textContent = `${idx + 1} / ${scanFrameResults.length}`;

    const fr = scanFrameResults[idx];
    const isDefect = fr.overall !== 'PASS';

    // Meta bar
    const metaEl = document.getElementById('frameViewerMeta');
    if (metaEl) metaEl.textContent = `t=${fr.timestamp}s  ·  Frame #${fr.frame_index}  ·  ${fr.frame_w}×${fr.frame_h}`;

    // Verdict badge
    const verdictEl = document.getElementById('frameViewerVerdict');
    if (verdictEl) {
        verdictEl.textContent = isDefect ? 'REJECT' : 'PASS';
        verdictEl.className = `badge fs-6 px-3 ${isDefect ? 'bg-danger' : 'bg-success'}`;
    }

    // Checklist strip below canvas
    const checklistDiv = document.getElementById('frameViewerChecklist');
    const checklistBody = document.getElementById('frameViewerChecklistBody');
    if (checklistBody && fr.checks && fr.checks.length > 0) {
        checklistBody.innerHTML = fr.checks.map(c => {
            const pass = c.status === 'PASS';
            return `<span class="badge ${pass ? 'bg-success-subtle text-success-emphasis border border-success-subtle' : 'bg-danger-subtle text-danger-emphasis border border-danger-subtle'} px-2 py-1">
                        ${pass ? '✓' : '✗'} ${c.label}
                    </span>`;
        }).join('');
        if (checklistDiv) checklistDiv.style.display = '';
    } else {
        if (checklistDiv) checklistDiv.style.display = 'none';
    }

    // Draw frame image + boxes on canvas
    renderFrameInViewer(fr);
}

function navigateFrame(delta) {
    jumpToFrame(currentFrameViewerIdx + delta);
}

/**
 * Draw the base64 frame image onto the canvas, then draw bounding boxes on top.
 * Box coords from the AI server are in original frame_w×frame_h pixels.
 * We scale them to canvas display size.
 */
function renderFrameInViewer(fr) {
    const canvas = document.getElementById('frameViewerCanvas');
    const placeholder = document.getElementById('frameViewerPlaceholder');

    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    if (!fr.frame_image) {
        // No image returned — show placeholder message
        canvas.style.display = 'none';
        if (placeholder) placeholder.style.display = '';
        return;
    }

    if (placeholder) placeholder.style.display = 'none';
    canvas.style.display = 'block';

    const img = new Image();
    img.onload = () => {
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        ctx.drawImage(img, 0, 0);

        // Extract detections
        let dets = [];
        if (fr.messages) {
            const detMsg = fr.messages.find(m => m.type === 'detections');
            if (detMsg && detMsg.detections) {
                dets = detMsg.detections.filter(d => d.box !== null);
            }
        }

        // Scale factor: original frame vs thumbnail (server already downscaled)
        // The thumbnail was resized to max 960px wide; coords are still in original fr.frame_w/fr.frame_h
        const scaleX = canvas.width / (fr.frame_w || canvas.width);
        const scaleY = canvas.height / (fr.frame_h || canvas.height);

        dets.forEach(d => {
            const [x1, y1, x2, y2] = d.box;
            const sx1 = x1 * scaleX, sy1 = y1 * scaleY;
            const sx2 = x2 * scaleX, sy2 = y2 * scaleY;

            const isGood = d.status === 'PASS';
            const color = isGood ? '#00e676' : '#ff1744';
            const lw = Math.max(2, Math.round(canvas.width / 400));

            ctx.strokeStyle = color;
            ctx.lineWidth = lw;
            ctx.strokeRect(sx1, sy1, sx2 - sx1, sy2 - sy1);

            const label = `${d.class_name} ${(d.score * 100).toFixed(1)}%`;
            const fontSize = Math.max(13, Math.round(canvas.width / 70));
            ctx.font = `bold ${fontSize}px sans-serif`;
            const tw = ctx.measureText(label).width;
            const th = fontSize + 4;

            ctx.fillStyle = color;
            ctx.fillRect(sx1, Math.max(0, sy1 - th - 4), tw + 10, th + 4);
            ctx.fillStyle = '#000';
            ctx.fillText(label, sx1 + 5, Math.max(th, sy1 - 2));
        });
    };
    img.onerror = () => {
        canvas.style.display = 'none';
        if (placeholder) {
            placeholder.style.display = '';
            placeholder.innerHTML = '<span class="material-symbols-outlined fs-1 d-block mb-2 text-danger">broken_image</span><span class="small text-danger">Could not load frame image</span>';
        }
    };
    img.src = 'data:image/jpeg;base64,' + fr.frame_image;
}


// ==========================================
// DRAG & DROP AND INITIALIZATION
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    // Setup video modal close cleanup
    const videoModalEl = document.getElementById('videoTestModal');
    if (videoModalEl) {
        videoModalEl.addEventListener('hidden.bs.modal', () => {
            stopVideoProcessing();
        });
    }

    // Drag and Drop for Image
    const imgPlaceholder = document.getElementById('canvasPlaceholder');
    const imgInput = document.getElementById('testImageInput');
    if (imgPlaceholder && imgInput) {
        imgPlaceholder.addEventListener('dragover', (e) => {
            e.preventDefault();
            imgPlaceholder.classList.add('bg-secondary', 'bg-opacity-25');
        });
        imgPlaceholder.addEventListener('dragleave', () => {
            imgPlaceholder.classList.remove('bg-secondary', 'bg-opacity-25');
        });
        imgPlaceholder.addEventListener('drop', (e) => {
            e.preventDefault();
            imgPlaceholder.classList.remove('bg-secondary', 'bg-opacity-25');
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                imgInput.files = e.dataTransfer.files;
                runModelTest();
            }
        });
    }

    // Drag and Drop for Video
    const videoPlaceholder = document.getElementById('videoCanvasPlaceholder');
    const videoInput = document.getElementById('videoFileInput');
    if (videoPlaceholder && videoInput) {
        videoPlaceholder.addEventListener('dragover', (e) => {
            e.preventDefault();
            videoPlaceholder.classList.add('bg-secondary', 'bg-opacity-25');
        });
        videoPlaceholder.addEventListener('dragleave', () => {
            videoPlaceholder.classList.remove('bg-secondary', 'bg-opacity-25');
        });
        videoPlaceholder.addEventListener('drop', (e) => {
            e.preventDefault();
            videoPlaceholder.classList.remove('bg-secondary', 'bg-opacity-25');
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                videoInput.files = e.dataTransfer.files;
                onVideoFileSelected(e.dataTransfer.files[0]);
            }
        });
    }
});
