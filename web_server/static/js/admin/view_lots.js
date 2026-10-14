let dataTable;

document.addEventListener('DOMContentLoaded', function () {
    fetchLots();
});

// Fetch all lots and populate table
async function fetchLots() {
    try {
        const response = await fetch('/lots/');
        if (!response.ok) {
            throw new Error('Failed to fetch lots');
        }
        const data = await response.json();

        if (data.status) {
            populateLotsTable(data.object);
        } else {
            alert(data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error fetching lots');
    }
}

function populateLotsTable(lots) {
    if (dataTable) {
        dataTable.destroy();
    }

    const tbody = document.querySelector('#lotsTable tbody');
    tbody.innerHTML = '';

    lots.forEach(lot => {
        const tr = document.createElement('tr');

        let statusBadgeClass = 'secondary';
        if (lot.inspection_status === 'Completed') statusBadgeClass = 'success';
        if (lot.inspection_status === 'Inspecting') statusBadgeClass = 'warning';
        if (lot.inspection_status === 'Pending') statusBadgeClass = 'primary';

        tr.innerHTML = `
            <td>${lot.id}</td>
            <td>${lot.lot_number || '-'}</td>
            <td>${lot.fuze_type || '-'}</td>
            <td>${lot.box_type || '-'}</td>
            <td><span class="badge bg-${statusBadgeClass}">${lot.inspection_status}</span></td>
            <td>${lot.created_at ? new Date(lot.created_at).toLocaleString() : '-'}</td>
            <td>${lot.created_by || '-'}</td>
            <td>
                <a href="/admin/manage_lots?lot_id=${lot.id}" class="btn btn-sm btn-outline-primary me-1">
                    View Details
                </a>
            </td>
        `;
        tbody.appendChild(tr);
    });

    dataTable = $('#lotsTable').DataTable({
        "pageLength": 10,
        "lengthChange": true,
        "order": [[5, "desc"]], // Sort by Created At column descending
        "dom": '<"d-flex justify-content-between"f>t<"d-flex justify-content-between"ip>',
        "language": {
            "search": "Search:",
            "paginate": {
                "next": "Next",
                "previous": "Previous"
            }
        }
    });
}
