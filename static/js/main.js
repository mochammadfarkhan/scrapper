// Main JavaScript for Image Scraper Application

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Image lazy loading fallback
    const images = document.querySelectorAll('img[loading="lazy"]');
    images.forEach(function(img) {
        img.addEventListener('error', function() {
            this.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkltYWdlIG5vdCBmb3VuZDwvdGV4dD48L3N2Zz4=';
            this.alt = 'Image not found';
        });
    });

    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add loading state to buttons
    const submitButtons = document.querySelectorAll('button[type="submit"]');
    submitButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const form = this.closest('form');
            if (form && form.checkValidity()) {
                this.disabled = true;
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
                
                // Re-enable button after 30 seconds as fallback
                setTimeout(() => {
                    this.disabled = false;
                    this.innerHTML = originalText;
                }, 30000);
            }
        });
    });

    // Image grid masonry-like effect
    const imageGrid = document.getElementById('imageGrid');
    if (imageGrid) {
        const images = imageGrid.querySelectorAll('img');
        let loadedImages = 0;
        
        images.forEach(function(img) {
            if (img.complete) {
                loadedImages++;
            } else {
                img.addEventListener('load', function() {
                    loadedImages++;
                    if (loadedImages === images.length) {
                        // All images loaded, apply any final styling
                        imageGrid.classList.add('loaded');
                    }
                });
            }
        });
        
        if (loadedImages === images.length) {
            imageGrid.classList.add('loaded');
        }
    }

    // Search functionality for dashboard
    const searchInput = document.getElementById('classSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const classCards = document.querySelectorAll('.class-card');
            
            classCards.forEach(function(card) {
                const className = card.querySelector('.card-title').textContent.toLowerCase();
                if (className.includes(searchTerm)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + / to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            const searchInput = document.getElementById('classSearch') || document.getElementById('keywords');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(function(modal) {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            });
        }
    });

    // Progress bar animation
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(function(bar) {
        const width = bar.style.width;
        bar.style.width = '0%';
        setTimeout(function() {
            bar.style.width = width;
        }, 100);
    });

    // Copy to clipboard functionality
    function copyToClipboard(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(function() {
                showToast('Copied to clipboard!', 'success');
            });
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            showToast('Copied to clipboard!', 'success');
        }
    }

    // Toast notification system
    function showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer') || createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove toast element after it's hidden
        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    }

    function createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
        return container;
    }

    // Make functions globally available
    window.copyToClipboard = copyToClipboard;
    window.showToast = showToast;
});
