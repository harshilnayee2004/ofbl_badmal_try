function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;

    // Determine colors based on type
    let bgClass = 'bg-success';
    let icon = 'check_circle';
    if (type === 'danger' || type === 'error') {
        bgClass = 'bg-danger';
        icon = 'error';
    } else if (type === 'warning') {
        bgClass = 'bg-warning';
        icon = 'warning';
    } else if (type === 'info') {
        bgClass = 'bg-info';
        icon = 'info';
    }

    // Create toast element
    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white ${bgClass} border-0 mb-2`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');

    toastEl.innerHTML = `
        <div class="d-flex w-100">
            <div class="toast-body d-flex align-items-center">
                <span class="material-symbols-outlined me-2">${icon}</span>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    toastContainer.appendChild(toastEl);
    const toast = new bootstrap.Toast(toastEl, { autohide: true, delay: 3000 });
    toast.show();

    // Remove element after hide
    toastEl.addEventListener('hidden.bs.toast', () => {
        toastEl.remove();
    });
}
