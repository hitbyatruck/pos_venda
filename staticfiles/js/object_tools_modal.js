/**
 * Object Tools Modal Helper
 * 
 * Provides functionality for handling modals triggered by object tools
 * in the Django admin or custom admin-like interfaces.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Find all object tools that should trigger modals
    const modalTriggers = document.querySelectorAll('.object-tools a[data-modal]');
    
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get the modal ID from the data attribute
            const modalId = this.getAttribute('data-modal');
            const modal = document.getElementById(modalId);
            
            if (modal) {
                // Initialize and show the modal using Bootstrap
                const bootstrapModal = new bootstrap.Modal(modal);
                bootstrapModal.show();
                
                // Store the trigger data for use in the modal
                if (this.hasAttribute('data-id')) {
                    const itemId = this.getAttribute('data-id');
                    const itemName = this.getAttribute('data-name') || '';
                    
                    // Set data in modal if needed
                    const nameElement = modal.querySelector('.item-name');
                    if (nameElement) {
                        nameElement.textContent = itemName;
                    }
                    
                    // Set up form action if there's a form
                    const form = modal.querySelector('form');
                    if (form && form.hasAttribute('data-action-template')) {
                        const actionTemplate = form.getAttribute('data-action-template');
                        form.action = actionTemplate.replace('{id}', itemId);
                    }
                    
                    // Set up confirmation button actions
                    const confirmBtn = modal.querySelector('.btn-confirm');
                    if (confirmBtn) {
                        confirmBtn.setAttribute('data-id', itemId);
                        confirmBtn.setAttribute('data-name', itemName);
                    }
                }
            } else {
                console.error(`Modal with ID "${modalId}" not found`);
            }
        });
    });
    
    // Handle modal confirmation buttons
    document.querySelectorAll('.modal .btn-confirm').forEach(btn => {
        btn.addEventListener('click', function() {
            const modal = this.closest('.modal');
            const form = modal.querySelector('form');
            
            if (form) {
                form.submit();
            } else {
                // If no form, handle via AJAX
                const id = this.getAttribute('data-id');
                const url = this.getAttribute('data-url');
                
                if (url && id) {
                    // Get CSRF token
                    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                    
                    fetch(url.replace('{id}', id), {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ id: id })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Close the modal
                            bootstrap.Modal.getInstance(modal).hide();
                            
                            // Remove item from the list or redirect
                            if (data.redirect) {
                                window.location.href = data.redirect;
                            } else {
                                const itemRow = document.getElementById(`item-${id}`);
                                if (itemRow) {
                                    itemRow.remove();
                                }
                                
                                // Show success message
                                if (typeof showToast === 'function') {
                                    showToast('success', 'Success', data.message || 'Operation completed successfully');
                                }
                            }
                        } else {
                            // Show error
                            if (typeof showToast === 'function') {
                                showToast('error', 'Error', data.message || 'An error occurred');
                            }
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        if (typeof showToast === 'function') {
                            showToast('error', 'Error', 'An unexpected error occurred');
                        }
                    });
                }
            }
        });
    });
    
    // Helper function for showing toast notifications
    window.showToast = function(type, title, message) {
        // Check if we have a toast container
        let toastContainer = document.getElementById('toast-container');
        
        if (!toastContainer) {
            // Create toast container if it doesn't exist
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        // Create toast element
        const toastId = 'toast-' + Date.now();
        const toastEl = document.createElement('div');
        toastEl.id = toastId;
        toastEl.className = `toast ${type === 'error' ? 'bg-danger text-white' : type === 'success' ? 'bg-success text-white' : 'bg-primary text-white'}`;
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');
        
        toastEl.innerHTML = `
            <div class="toast-header">
                <strong class="me-auto">${title}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        toastContainer.appendChild(toastEl);
        
        // Initialize and show the toast
        const toast = new bootstrap.Toast(toastEl, {
            autohide: true,
            delay: 5000
        });
        toast.show();
        
        // Remove toast after it's hidden
        toastEl.addEventListener('hidden.bs.toast', function() {
            toastEl.remove();
        });
    };
});
