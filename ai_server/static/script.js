document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('inference-form');
    const imageInput = document.getElementById('image-input');
    const dropZone = document.getElementById('drop-zone');
    const imagePreview = document.getElementById('image-preview');
    const uploadPlaceholder = document.querySelector('.upload-placeholder');
    const promptInput = document.getElementById('prompt-input');
    const runBtn = document.getElementById('run-btn');
    const loader = runBtn.querySelector('.loader');
    const outputDisplay = document.getElementById('output-display');
    const latencyValue = document.getElementById('latency-value');
    const statusValue = document.getElementById('status-value');

    // Handle image upload & preview
    dropZone.addEventListener('click', () => imageInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--primary)';
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = 'var(--border-color)';
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--border-color)';
        if (e.dataTransfer.files.length) {
            imageInput.files = e.dataTransfer.files;
            handleImageSelection(e.dataTransfer.files[0]);
        }
    });

    imageInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleImageSelection(e.target.files[0]);
        }
    });

    function handleImageSelection(file) {
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                imagePreview.src = e.target.result;
                imagePreview.classList.remove('hidden');
                uploadPlaceholder.classList.add('hidden');
            };
            reader.readAsDataURL(file);
        }
    }

    // Handle Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!imageInput.files[0]) {
            alert('Please select an image first.');
            return;
        }

        const formData = new FormData();
        formData.append('image', imageInput.files[0]);
        formData.append('prompt', promptInput.value);

        // UI Updates
        runBtn.disabled = true;
        loader.classList.remove('hidden');
        statusValue.textContent = 'Processing...';
        statusValue.style.color = 'var(--accent-purple)';
        outputDisplay.textContent = 'Awaiting response...';
        latencyValue.textContent = '-- ms';

        const startTime = performance.now();

        try {
            const response = await fetch('/inference', {
                method: 'POST',
                body: formData
            });

            const endTime = performance.now();
            const latency = Math.round(endTime - startTime);
            latencyValue.textContent = `${latency} ms`;

            const result = await response.json();

            if (result.status) {
                statusValue.textContent = 'Success';
                statusValue.style.color = '#10b981'; // Green
                outputDisplay.textContent = JSON.stringify(result.object, null, 2);
            } else {
                throw new Error(result.message || 'Inference failed');
            }
        } catch (error) {
            console.error('Error:', error);
            statusValue.textContent = 'Error';
            statusValue.style.color = '#ef4444'; // Red
            outputDisplay.textContent = `Error: ${error.message}`;
        } finally {
            runBtn.disabled = false;
            loader.classList.add('hidden');
        }
    });
});
