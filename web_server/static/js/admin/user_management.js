let dataTable;
const userModal = new bootstrap.Modal(document.getElementById('userModal'));
const deleteConfirmModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));

document.addEventListener('DOMContentLoaded', function () {
    fetchUsers();
});

// Fetch all users and populate table
async function fetchUsers() {
    try {
        const response = await fetch('/manage-users/');
        if (!response.ok) {
            throw new Error('Failed to fetch users');
        }
        const data = await response.json();

        if (data.status) {
            populateUserTable(data.object);
        } else {
            alert(data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error fetching users');
    }
}

function populateUserTable(users) {
    // Destroy existing DataTable if exists
    if (dataTable) {
        dataTable.destroy();
    }

    const tbody = document.querySelector('#usersTable tbody');
    tbody.innerHTML = '';

    users.forEach(user => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${user.id}</td>
            <td>${user.email}</td>
            <td><span class="badge bg-${user.role === 'admin' ? 'danger' : 'primary'}">${user.role}</span></td>
            <td><span class="badge bg-${user.status ? 'success' : 'secondary'}">${user.status ? 'Active' : 'Inactive'}</span></td>
            <td>${user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary me-1" onclick="openEditModal(${user.id})">
                    <span class="material-symbols-outlined" style="font-size: 16px;">edit</span>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="openDeleteModal(${user.id})">
                    <span class="material-symbols-outlined" style="font-size: 16px;">delete</span>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });

    // Initialize DataTable
    dataTable = $('#usersTable').DataTable({
        "pageLength": 10,
        "lengthChange": false, // Disable changing page length if you strictly want 10
        "dom": '<"d-flex justify-content-between"f>t<"d-flex justify-content-between"ip>', // Clean layout
        "language": {
            "search": "Search:",
            "paginate": {
                "next": "Next",
                "previous": "Previous"
            }
        }
    });
}

function resetUserForm() {
    document.getElementById('userForm').reset();
    document.getElementById('userId').value = '';
    document.getElementById('userModalLabel').textContent = 'Add New User';

    // Password handling for Create
    document.getElementById('passwordHelpText').style.display = 'none';
    document.getElementById('userPassword').setAttribute('required', 'required');
}

async function openEditModal(userId) {
    try {
        const response = await fetch(`/manage-users/${userId}`);
        const data = await response.json();

        if (data.status) {
            const user = data.object;
            document.getElementById('userId').value = user.id;
            document.getElementById('userEmail').value = user.email;
            document.getElementById('userRole').value = user.role;
            document.getElementById('userStatus').checked = user.status;

            document.getElementById('userModalLabel').textContent = 'Edit User';

            // Password handling for Edit
            document.getElementById('passwordHelpText').style.display = 'inline';
            document.getElementById('userPassword').removeAttribute('required');
            document.getElementById('userPassword').value = ''; // Clear for security/optionality

            userModal.show();
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

async function saveUser() {
    const userId = document.getElementById('userId').value;
    const email = document.getElementById('userEmail').value;
    const role = document.getElementById('userRole').value;
    const status = document.getElementById('userStatus').checked;
    const password = document.getElementById('userPassword').value;

    // Simple validation
    if (!email) {
        alert("Email is required");
        return;
    }

    const payload = {
        email: email,
        role: role,
        status: status
    };

    let url = '/manage-users/';
    let method = 'POST';

    if (userId) {
        // Update Mode
        url = `/manage-users/${userId}`;
        method = 'PUT';
        // Add password only if provided
        if (password) {
            payload.password = password;
        }
    } else {
        // Create Mode
        if (!password) {
            alert("Password is required for new users");
            return;
        }
        payload.password = password;
    }

    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (data.status || response.ok) {
            userModal.hide();
            fetchUsers();
        } else {
            alert(data.message || data.detail || 'Operation failed');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred');
    }
}

function openDeleteModal(userId) {
    document.getElementById('deleteUserId').value = userId;
    deleteConfirmModal.show();
}

async function confirmDeleteUser() {
    const userId = document.getElementById('deleteUserId').value;

    try {
        const response = await fetch(`/manage-users/${userId}`, {
            method: 'DELETE'
        });
        const data = await response.json();

        if (data.status || response.ok) {
            deleteConfirmModal.hide();
            fetchUsers();
        } else {
            alert(data.message || 'Failed to delete user');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}
