window.addEventListener('DOMContentLoaded', event => {
    const sidebarToggle = document.body.querySelector('#sidebarToggle');
    const backdrop = document.getElementById('sidebar-backdrop');
    const sidebar = document.getElementById('sidebar-wrapper');

    function closeMobileSidebar() {
        if (window.innerWidth < 992) {
            document.body.classList.remove('sb-sidenav-toggled');
            if (backdrop) backdrop.classList.remove('show');
        }
    }

    function toggleSidebar(e) {
        if (e) e.preventDefault();
        const isToggled = document.body.classList.toggle('sb-sidenav-toggled');
        if (backdrop) {
            if (window.innerWidth < 992 && isToggled) {
                backdrop.classList.add('show');
            } else {
                backdrop.classList.remove('show');
            }
        }
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', toggleSidebar);
    }

    if (backdrop) {
        backdrop.addEventListener('click', closeMobileSidebar);
    }

    // Auto-close on small screens when clicking navigation links
    if (sidebar) {
        sidebar.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                closeMobileSidebar();
            });
        });
    }

    // Handle resize
    window.addEventListener('resize', () => {
        if (window.innerWidth >= 992 && backdrop) {
            backdrop.classList.remove('show');
        }
    });
});

