/**
 * Users JavaScript for MikroTik Monitoring System
 * Handles user management (admin only)
 */

// Initialize API client
const apiClient = new ApiClient();

// Initialize users page components
document.addEventListener('DOMContentLoaded', function() {
    // Load users
    loadUsers();
    
    // Set up event listeners
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Add user form
    document.getElementById('save-user-btn').addEventListener('click', saveUser);
    
    // Edit user form
    document.getElementById('update-user-btn').addEventListener('click', updateUser);
    
    // Delete user button
    document.getElementById('delete-user-btn').addEventListener('click', deleteUser);
    
    // Refresh users button
    const refreshBtn = document.getElementById('refresh-users-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadUsers);
    }
}

// Load users from API
async function loadUsers() {
    // Show loading state
    document.getElementById('users-table').innerHTML = `
        <tr>
            <td colspan="6" class="text-center">
                <span class="spinner-border spinner-border-sm" role="status"></span> Loading users...
            </td>
        </tr>
    `;
    
    // Get users from API
    const users = await apiClient.getUsers();
    
    // Check for error response
    if (users && users.error) {
        console.error('Error loading users:', users.error);
        document.getElementById('users-table').innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-danger">
                    ${users.error}
                    <button class="btn btn-sm btn-primary ms-3" onclick="loadUsers()">
                        <i class="fas fa-sync-alt me-1"></i> Retry
                    </button>
                </td>
            </tr>
        `;
        return;
    }
    
    // Update users table
    updateUsersTable(users);
}

// Update users table
function updateUsersTable(users) {
    const tableBody = document.getElementById('users-table');
    
    if (!users || users.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" class="text-center">No users found</td></tr>';
        return;
    }
    
    let html = '';
    users.forEach(user => {
        // Format role with badge
        let roleBadgeClass = 'secondary';
        if (user.role === 'admin') {
            roleBadgeClass = 'danger';
        } else if (user.role === 'operator') {
            roleBadgeClass = 'warning';
        }
        
        html += `
            <tr data-user-id="${user.id}">
                <td>${user.username}</td>
                <td>${user.email}</td>
                <td><span class="badge bg-${roleBadgeClass}">${user.role}</span></td>
                <td>${formatDateTime(user.created_at)}</td>
                <td>${user.last_login ? formatDateTime(user.last_login) : 'Never'}</td>
                <td>
                    <button type="button" class="btn btn-sm btn-secondary" onclick="showEditUserModal(${user.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    tableBody.innerHTML = html;
}

// Save new user
async function saveUser() {
    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const role = document.getElementById('role').value;
    
    // Validate required fields
    if (!username || !email || !password || !role) {
        showError('Please fill in all required fields');
        return;
    }
    
    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showError('Please enter a valid email address');
        return;
    }
    
    // Disable the save button
    const saveBtn = document.getElementById('save-user-btn');
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Saving...';
    
    // Create user data object
    const userData = {
        username: username,
        email: email,
        password: password,
        role: role
    };
    
    // Create user via API
    const response = await apiClient.createUser(userData);
    
    // Re-enable save button
    saveBtn.disabled = false;
    saveBtn.innerHTML = 'Save User';
    
    // Check for error response
    if (response && response.error) {
        console.error('Error adding user:', response.error);
        showError(response.error || 'Failed to add user');
        return;
    }
    
    // Handle success
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('addUserModal'));
    if (modal) modal.hide();
    
    // Clear form
    document.getElementById('add-user-form').reset();
    
    // Reload users
    loadUsers();
    
    // Show success message
    showSuccess('User added successfully');
}

// Show edit user modal with user data
async function showEditUserModal(userId) {
    // Show loading spinner in modal
    document.getElementById('edit-username').value = '';
    document.getElementById('edit-email').value = '';
    document.getElementById('edit-password').value = '';
    document.getElementById('edit-role').value = 'user';
    
    // Show modal first
    const modal = new bootstrap.Modal(document.getElementById('editUserModal'));
    modal.show();
    
    // Get users from API
    const users = await apiClient.getUsers();
    
    // Check for error response
    if (users && users.error) {
        console.error('Error getting users:', users.error);
        showError(users.error || 'Failed to get user details');
        return;
    }
    
    // Find user by ID
    const user = Array.isArray(users) ? users.find(u => u.id === userId) : null;
    
    if (!user) {
        showError('User not found');
        return;
    }
    
    // Fill form fields
    document.getElementById('edit-user-id').value = user.id;
    document.getElementById('edit-username').value = user.username;
    document.getElementById('edit-email').value = user.email;
    document.getElementById('edit-password').value = ''; // Don't fill password
    document.getElementById('edit-role').value = user.role;
}

// Update user
async function updateUser() {
    const userId = document.getElementById('edit-user-id').value;
    const username = document.getElementById('edit-username').value;
    const email = document.getElementById('edit-email').value;
    const password = document.getElementById('edit-password').value;
    const role = document.getElementById('edit-role').value;
    
    // Validate required fields
    if (!username || !email || !role) {
        showError('Please fill in all required fields');
        return;
    }
    
    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showError('Please enter a valid email address');
        return;
    }
    
    // Disable update button
    const updateBtn = document.getElementById('update-user-btn');
    updateBtn.disabled = true;
    updateBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Updating...';
    
    // Create user data object
    const userData = {
        username: username,
        email: email,
        role: role
    };
    
    // Only include password if it was changed
    if (password) {
        userData.password = password;
    }
    
    // Update user via API
    const response = await apiClient.updateUser(userId, userData);
    
    // Re-enable update button
    updateBtn.disabled = false;
    updateBtn.innerHTML = 'Update User';
    
    // Check for error response
    if (response && response.error) {
        console.error('Error updating user:', response.error);
        showError(response.error || 'Failed to update user');
        return;
    }
    
    // Handle success
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('editUserModal'));
    if (modal) modal.hide();
    
    // Reload users
    loadUsers();
    
    // Show success message
    showSuccess('User updated successfully');
}

// Delete user
async function deleteUser() {
    const userId = document.getElementById('edit-user-id').value;
    const username = document.getElementById('edit-username').value;
    
    // Confirm deletion
    if (!confirm(`Are you sure you want to delete the user "${username}"? This action cannot be undone.`)) {
        return;
    }
    
    // Disable delete button
    const deleteBtn = document.getElementById('delete-user-btn');
    deleteBtn.disabled = true;
    deleteBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Deleting...';
    
    // Delete user via API
    const response = await apiClient.deleteUser(userId);
    
    // Re-enable delete button
    deleteBtn.disabled = false;
    deleteBtn.innerHTML = 'Delete';
    
    // Check for error response
    if (response && response.error) {
        console.error('Error deleting user:', response.error);
        showError(response.error || 'Failed to delete user');
        return;
    }
    
    // Handle success
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('editUserModal'));
    if (modal) modal.hide();
    
    // Reload users
    loadUsers();
    
    // Show success message
    showSuccess('User deleted successfully');
}

// Show error message
function showError(message) {
    const alertHtml = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    const flashContainer = document.querySelector('.flash-messages');
    if (flashContainer) {
        flashContainer.innerHTML += alertHtml;
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            const alerts = document.querySelectorAll('.alert-danger');
            if (alerts.length > 0) {
                const lastAlert = alerts[alerts.length - 1];
                const bsAlert = new bootstrap.Alert(lastAlert);
                bsAlert.close();
            }
        }, 5000);
    }
}

// Show success message
function showSuccess(message) {
    const alertHtml = `
        <div class="alert alert-success alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    const flashContainer = document.querySelector('.flash-messages');
    if (flashContainer) {
        flashContainer.innerHTML += alertHtml;
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            const alerts = document.querySelectorAll('.alert-success');
            if (alerts.length > 0) {
                const lastAlert = alerts[alerts.length - 1];
                const bsAlert = new bootstrap.Alert(lastAlert);
                bsAlert.close();
            }
        }, 5000);
    }
}
