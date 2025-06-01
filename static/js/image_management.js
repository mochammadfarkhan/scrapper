// Image Management JavaScript for Bulk Operations
// Global variables
let selectedImages = new Set();
let availableFolders = [];

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    console.log('Image management initialized');
    
    // Set up event listeners
    setupEventListeners();
    
    // Load available folders
    loadAvailableFolders();
});

// Set up event listeners
function setupEventListeners() {
    // Bulk delete confirmation input
    const bulkDeleteInput = document.getElementById('bulkDeleteConfirmation');
    if (bulkDeleteInput) {
        bulkDeleteInput.addEventListener('input', function() {
            const confirmBtn = document.getElementById('confirmBulkDeleteBtn');
            const errorDiv = document.getElementById('bulkDeleteError');
            
            if (this.value.toUpperCase() === 'DELETE') {
                confirmBtn.disabled = false;
                this.classList.remove('is-invalid');
                errorDiv.style.display = 'none';
            } else {
                confirmBtn.disabled = true;
                if (this.value.length > 0) {
                    this.classList.add('is-invalid');
                    errorDiv.style.display = 'block';
                }
            }
        });
    }
    
    // Create new folder checkbox
    const createNewFolderCheckbox = document.getElementById('createNewFolder');
    if (createNewFolderCheckbox) {
        createNewFolderCheckbox.addEventListener('change', function() {
            const newFolderInput = document.getElementById('newFolderInput');
            const destinationSelect = document.getElementById('destinationFolder');
            
            if (this.checked) {
                newFolderInput.style.display = 'block';
                destinationSelect.disabled = true;
                destinationSelect.value = '';
            } else {
                newFolderInput.style.display = 'none';
                destinationSelect.disabled = false;
                document.getElementById('newFolderName').value = '';
            }
        });
    }
}

// Image Selection Functions
function toggleImageSelection(container) {
    const checkbox = container.querySelector('.image-checkbox');
    if (checkbox) {
        checkbox.checked = !checkbox.checked;
        handleImageSelection(checkbox);
    }
}

function handleImageSelection(checkbox) {
    const filename = checkbox.dataset.filename;
    const relativePath = checkbox.dataset.relativePath;
    const imageCard = checkbox.closest('.image-card');
    const overlay = imageCard.querySelector('.selection-overlay');
    
    if (checkbox.checked) {
        selectedImages.add(relativePath);
        imageCard.classList.add('selected');
        overlay.style.display = 'block';
    } else {
        selectedImages.delete(relativePath);
        imageCard.classList.remove('selected');
        overlay.style.display = 'none';
    }
    
    updateSelectionUI();
}

function selectAllImages() {
    const checkboxes = document.querySelectorAll('.image-checkbox');
    checkboxes.forEach(checkbox => {
        if (!checkbox.checked) {
            checkbox.checked = true;
            handleImageSelection(checkbox);
        }
    });
}

function deselectAllImages() {
    const checkboxes = document.querySelectorAll('.image-checkbox');
    checkboxes.forEach(checkbox => {
        if (checkbox.checked) {
            checkbox.checked = false;
            handleImageSelection(checkbox);
        }
    });
}

function updateSelectionUI() {
    const selectedCount = selectedImages.size;
    const bulkActionsBar = document.getElementById('bulkActionsBar');
    const selectedCountSpan = document.getElementById('selectedCount');
    const moveBtn = document.getElementById('moveImagesBtn');
    const deleteBtn = document.getElementById('deleteImagesBtn');
    
    // Update selected count
    selectedCountSpan.textContent = `${selectedCount} image${selectedCount !== 1 ? 's' : ''} selected`;
    
    // Show/hide bulk actions bar
    if (selectedCount > 0) {
        if (bulkActionsBar.style.display === 'none') {
            bulkActionsBar.style.display = 'block';
            bulkActionsBar.classList.add('bulk-actions-visible');
        }
        moveBtn.disabled = false;
        deleteBtn.disabled = false;
    } else {
        bulkActionsBar.style.display = 'none';
        bulkActionsBar.classList.remove('bulk-actions-visible');
        moveBtn.disabled = true;
        deleteBtn.disabled = true;
    }
}

// Modal Functions
function showMoveModal() {
    if (selectedImages.size === 0) {
        showToast('No images selected', 'warning');
        return;
    }
    
    const moveImageCount = document.getElementById('moveImageCount');
    moveImageCount.textContent = selectedImages.size;
    
    // Reset form
    document.getElementById('destinationFolder').value = '';
    document.getElementById('createNewFolder').checked = false;
    document.getElementById('newFolderName').value = '';
    document.getElementById('newFolderInput').style.display = 'none';
    document.getElementById('destinationFolder').disabled = false;
    
    // Clear validation errors
    clearValidationErrors();
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('moveModal'));
    modal.show();
}

function showDeleteModal() {
    if (selectedImages.size === 0) {
        showToast('No images selected', 'warning');
        return;
    }
    
    const bulkDeleteCount = document.getElementById('bulkDeleteCount');
    bulkDeleteCount.textContent = selectedImages.size;
    
    // Reset form
    document.getElementById('bulkDeleteConfirmation').value = '';
    document.getElementById('confirmBulkDeleteBtn').disabled = true;
    
    // Clear validation errors
    clearValidationErrors();
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('bulkDeleteModal'));
    modal.show();
}

// API Functions
function loadAvailableFolders() {
    fetch(`/api/folders?current=${encodeURIComponent(window.currentClassName)}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                availableFolders = data.folders;
                populateFolderDropdown();
            } else {
                console.error('Failed to load folders:', data.message);
            }
        })
        .catch(error => {
            console.error('Error loading folders:', error);
        });
}

function populateFolderDropdown() {
    const select = document.getElementById('destinationFolder');
    if (!select) return;
    
    // Clear existing options except the first one
    while (select.children.length > 1) {
        select.removeChild(select.lastChild);
    }
    
    // Add folder options
    availableFolders.forEach(folder => {
        const option = document.createElement('option');
        option.value = folder;
        option.textContent = folder;
        select.appendChild(option);
    });
}

function confirmMoveImages() {
    const createNewFolder = document.getElementById('createNewFolder').checked;
    let destinationFolder;
    
    if (createNewFolder) {
        destinationFolder = document.getElementById('newFolderName').value.trim();
        if (!destinationFolder) {
            showValidationError('newFolderName', 'Please enter a folder name');
            return;
        }
        if (!/^[a-zA-Z0-9_\-\s]+$/.test(destinationFolder)) {
            showValidationError('newFolderName', 'Folder name can only contain letters, numbers, spaces, hyphens, and underscores');
            return;
        }
    } else {
        destinationFolder = document.getElementById('destinationFolder').value;
        if (!destinationFolder) {
            showValidationError('destinationFolder', 'Please select a destination folder');
            return;
        }
    }
    
    // Prepare data
    const moveData = {
        images: Array.from(selectedImages),
        destination_folder: destinationFolder,
        source_folder: window.currentClassName,
        create_new: createNewFolder
    };
    
    // Update button state
    const confirmBtn = document.getElementById('confirmMoveBtn');
    confirmBtn.disabled = true;
    confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Moving...';
    
    // Send request
    fetch('/api/move-images', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(moveData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast(`Successfully moved ${data.moved_count} images to ${destinationFolder}`, 'success');
            
            // Remove moved images from the grid
            removeImagesFromGrid(Array.from(selectedImages));
            
            // Clear selection
            selectedImages.clear();
            updateSelectionUI();
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('moveModal'));
            modal.hide();
            
            // Reload folders list
            loadAvailableFolders();
        } else {
            showToast(`Failed to move images: ${data.message}`, 'error');
        }
    })
    .catch(error => {
        console.error('Move request failed:', error);
        showToast('Failed to move images. Please try again.', 'error');
    })
    .finally(() => {
        // Reset button state
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = '<i class="fas fa-folder-open me-1"></i>Move Images';
    });
}

function confirmBulkDelete() {
    const deleteData = {
        images: Array.from(selectedImages),
        folder: window.currentClassName
    };
    
    // Update button state
    const confirmBtn = document.getElementById('confirmBulkDeleteBtn');
    confirmBtn.disabled = true;
    confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Deleting...';
    
    // Send request
    fetch('/api/delete-images', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(deleteData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast(`Successfully deleted ${data.deleted_count} images`, 'success');
            
            // Remove deleted images from the grid
            removeImagesFromGrid(Array.from(selectedImages));
            
            // Clear selection
            selectedImages.clear();
            updateSelectionUI();
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('bulkDeleteModal'));
            modal.hide();
        } else {
            showToast(`Failed to delete images: ${data.message}`, 'error');
        }
    })
    .catch(error => {
        console.error('Delete request failed:', error);
        showToast('Failed to delete images. Please try again.', 'error');
    })
    .finally(() => {
        // Reset button state
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = '<i class="fas fa-trash me-1"></i>Delete Images';
    });
}

// UI Helper Functions
function removeImagesFromGrid(imagePaths) {
    imagePaths.forEach(relativePath => {
        const imageCard = document.querySelector(`[data-relative-path="${relativePath}"]`);
        if (imageCard) {
            const parentCol = imageCard.closest('.col-sm-6, .col-md-4, .col-lg-3');
            if (parentCol) {
                // Add fade out animation
                parentCol.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                parentCol.style.opacity = '0';
                parentCol.style.transform = 'scale(0.8)';
                
                // Remove after animation
                setTimeout(() => {
                    parentCol.remove();
                    updateImageCount();
                }, 300);
            }
        }
    });
}

function updateImageCount() {
    const remainingImages = document.querySelectorAll('.image-card').length;
    const totalCountBadge = document.getElementById('totalImageCount');
    if (totalCountBadge) {
        totalCountBadge.textContent = `${remainingImages} images`;
    }
    
    // If no images left, reload page to show "No Images Found" message
    if (remainingImages === 0) {
        setTimeout(() => {
            location.reload();
        }, 500);
    }
}

function showValidationError(fieldId, message) {
    const field = document.getElementById(fieldId);
    if (field) {
        field.classList.add('is-invalid');
        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
    }
}

function clearValidationErrors() {
    const invalidFields = document.querySelectorAll('.is-invalid');
    invalidFields.forEach(field => {
        field.classList.remove('is-invalid');
    });
    
    const errorDivs = document.querySelectorAll('.invalid-feedback');
    errorDivs.forEach(div => {
        div.style.display = 'none';
    });
}

// Toast notification function (reused from existing code)
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1055';
        document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toastId = 'toast-' + Date.now();
    const bgClass = type === 'success' ? 'bg-success' : type === 'error' ? 'bg-danger' : type === 'warning' ? 'bg-warning' : 'bg-info';
    const iconClass = type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle';

    const toastHtml = `
        <div id="${toastId}" class="toast ${bgClass} text-white" role="alert">
            <div class="toast-header ${bgClass} text-white border-0">
                <i class="fas ${iconClass} me-2"></i>
                <strong class="me-auto">Notification</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHtml);

    // Show the toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 5000
    });
    toast.show();

    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function () {
        this.remove();
    });
}
