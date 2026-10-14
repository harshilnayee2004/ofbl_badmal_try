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
let isVideoPlaying = false;
let videoLoopId = null;
let isProcessingFrame = false;
let lastInferenceTime = 0;
let currentVideoDetections = [];
let videoFrameCount = 0;

function onVideoFileSelected(event) {
    const file = event.target ? (event.target.files ? event.target.files[0] : null) : event;
    if (!file) return;

    videoFile = file;
    videoElement = document.getElementById('hiddenTestVideo');
    videoCanvas = document.getElementById('videoResultCanvas');
    videoCtx = videoCanvas.getContext('2d');

    const placeholder = document.getElementById('videoCanvasPlaceholder');
    const playBtn = document.getElementById('playVideoBtn');
    const scanBtn = document.getElementById('serverScanBtn');

    stopVideoProcessing();
    currentVideoDetections = [];
    videoFrameCount = 0;

    const objectUrl = URL.createObjectURL(file);
    videoElement.src = objectUrl;

    videoElement.onloadedmetadata = () => {
        placeholder.classList.add('d-none');
        videoCanvas.classList.remove('d-none');
        videoCanvas.width = videoElement.videoWidth || 1280;
        videoCanvas.height = videoElement.videoHeight || 720;

        videoElement.currentTime = 0;
        updateVideoTimeline();
        if (playBtn) playBtn.disabled = false;
        if (scanBtn) scanBtn.disabled = false;
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

    videoElement.onended = () => {
        stopVideoProcessing();
        const playText = document.getElementById('playVideoText');
        const playIcon = document.getElementById('playVideoIcon');
        if (playText) playText.innerText = 'Replay';
        if (playIcon) playIcon.innerText = 'replay';
    };
}

function toggleVideoProcessing() {
    if (!videoElement) return;

    if (isVideoPlaying) {
        pauseVideoProcessing();
    } else {
        startVideoProcessing();
    }
}

function startVideoProcessing() {
    if (!videoElement) return;

    videoElement.play().then(() => {
        isVideoPlaying = true;
        const playText = document.getElementById('playVideoText');
        const playIcon = document.getElementById('playVideoIcon');
        const playBtn = document.getElementById('playVideoBtn');

        if (playText) playText.innerText = 'Pause';
        if (playIcon) playIcon.innerText = 'pause';
        if (playBtn) playBtn.classList.replace('btn-danger', 'btn-warning');

        runVideoRenderLoop();
    }).catch(err => {
        console.error('Video play error:', err);
    });
}

function pauseVideoProcessing() {
    if (!videoElement) return;

    videoElement.pause();
    isVideoPlaying = false;
    if (videoLoopId) cancelAnimationFrame(videoLoopId);

    const playText = document.getElementById('playVideoText');
    const playIcon = document.getElementById('playVideoIcon');
    const playBtn = document.getElementById('playVideoBtn');

    if (playText) playText.innerText = 'Resume';
    if (playIcon) playIcon.innerText = 'play_arrow';
    if (playBtn) playBtn.classList.replace('btn-warning', 'btn-danger');
}

function stopVideoProcessing() {
    if (!videoElement) return;

    pauseVideoProcessing();
    const playText = document.getElementById('playVideoText');
    const playIcon = document.getElementById('playVideoIcon');
    const playBtn = document.getElementById('playVideoBtn');

    if (playText) playText.innerText = 'Start Test';
    if (playIcon) playIcon.innerText = 'play_arrow';
    if (playBtn) playBtn.classList.replace('btn-warning', 'btn-danger');
}

function resetVideoTest() {
    if (!videoElement) return;
    videoElement.currentTime = 0;
    currentVideoDetections = [];
    videoFrameCount = 0;
    const counter = document.getElementById('videoFrameCounter');
    if (counter) counter.innerText = 'Frame 0';
    renderVideoFrame();
}

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

    const formatTime = (secs) => {
        const m = Math.floor(secs / 60).toString().padStart(2, '0');
        const s = Math.floor(secs % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    };
    const badge = document.getElementById('videoProgressBadge');
    if (badge) badge.innerText = `${formatTime(cur)} / ${formatTime(dur)}`;
}

function runVideoRenderLoop() {
    if (!isVideoPlaying) return;

    renderVideoFrame();

    const now = performance.now();
    const fpsSelect = document.getElementById('videoFpsSelect');
    const targetFps = fpsSelect ? parseInt(fpsSelect.value) || 3 : 3;
    const minInterval = 1000 / targetFps;

    if (!isProcessingFrame && (now - lastInferenceTime >= minInterval)) {
        sendCurrentVideoFrameToAI();
    }

    videoLoopId = requestAnimationFrame(runVideoRenderLoop);
}

function renderVideoFrame() {
    if (!videoElement || !videoCanvas || !videoCtx) return;

    try {
        videoCtx.drawImage(videoElement, 0, 0, videoCanvas.width, videoCanvas.height);
    } catch (e) {
        // Video might not be ready yet
        return;
    }

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
    if (isProcessingFrame || !videoCanvas) return;
    isProcessingFrame = true;
    lastInferenceTime = performance.now();
    videoFrameCount++;

    const counter = document.getElementById('videoFrameCounter');
    if (counter) counter.innerText = `Frame #${videoFrameCount}`;

    videoCanvas.toBlob(async (blob) => {
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
    const reportBody = document.getElementById('serverScanReportBody');

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
        reportSection.classList.remove('d-none');

        const isPass = data.overall === 'PASS';
        let defectItems = '';
        const defectFrames = (data.sampled_results || []).filter(r => r.overall !== 'PASS');

        if (defectFrames.length > 0) {
            defectItems = defectFrames.map(f => `
                <div class="list-group-item list-group-item-action d-flex justify-content-between align-items-center py-2" style="cursor: pointer;" onclick="if(videoElement){videoElement.currentTime=${f.timestamp};}">
                    <div>
                        <span class="badge bg-danger me-2">Defect at ${f.timestamp}s</span>
                        <span class="small text-muted">Frame #${f.frame_index}</span>
                    </div>
                    <span class="badge bg-dark border">Click to Jump</span>
                </div>
            `).join('');
        } else {
            defectItems = '<div class="text-success small p-2"><span class="material-symbols-outlined fs-6 align-middle me-1">check_circle</span>All sampled frames passed criteria!</div>';
        }

        reportBody.innerHTML = `
            <div class="row g-3">
                <div class="col-md-3 text-center">
                    <span class="text-muted small fw-bold text-uppercase d-block mb-1">Batch Verdict</span>
                    <span class="badge fs-5 px-3 py-2 ${isPass ? 'bg-success' : 'bg-danger'}">${data.overall}</span>
                </div>
                <div class="col-md-3 text-center">
                    <span class="text-muted small fw-bold text-uppercase d-block mb-1">Total Video Frames</span>
                    <h5 class="fw-bold font-monospace mb-0">${data.total_frames_in_video || 'N/A'}</h5>
                </div>
                <div class="col-md-3 text-center">
                    <span class="text-muted small fw-bold text-uppercase d-block mb-1">Sampled Frames</span>
                    <h5 class="fw-bold font-monospace mb-0">${data.sampled_frames_count || 0}</h5>
                </div>
                <div class="col-md-3 text-center">
                    <span class="text-muted small fw-bold text-uppercase d-block mb-1">Defect Frames</span>
                    <h5 class="fw-bold font-monospace mb-0 text-${defectFrames.length > 0 ? 'danger' : 'success'}">${defectFrames.length}</h5>
                </div>
            </div>
            <hr class="my-3">
            <h6 class="small fw-bold text-uppercase text-muted mb-2">Defect Timeline Navigation</h6>
            <div class="list-group list-group-flush border rounded overflow-auto" style="max-height: 160px;">
                ${defectItems}
            </div>
        `;

        reportSection.scrollIntoView({ behavior: 'smooth' });

    } catch (err) {
        console.error('Server scan failed:', err);
        alert(`Server video scan failed: ${err.message}`);
    } finally {
        scanBtn.disabled = false;
        scanBtn.innerHTML = originalContent;
    }
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
