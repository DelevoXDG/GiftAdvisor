class GiftDetail {
    constructor()         console.log('GiftDetail initializing...'); // Debug log
        
        // Forms and modals
        this.editGiftForm = document.getElementById('editGiftForm');
        this.editGiftModal = document.getElementById('editGiftModal');
        this.editBsModal = new bootstrap.Modal(this.editGiftModal);
        
        // Buttons
        this.saveGiftBtn = document.getElementById('saveGiftBtn');
        this.processWithAIBtn = document.getElementById('processWithAIBtn');
        
        console.log('Process AI button found:', this.processWithAIBtn); // Debug log
        
        // State
        this.isSubmitting = false;
        this.isProcessing = false;
        
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        console.log('Initializing event listeners...'); // Debug log
        
        if (!this.processWithAIBtn) {
            console.error('Process AI button not found!');
            return;
        }
        
        this.editGiftModal.addEventListener('hidden.bs.modal', () => this.handleModalHidden());
        this.saveGiftBtn.addEventListener('click', (e) => this.handleUpdateGift(e));
        
        // Add direct event listener with debug
        this.processWithAIBtn.addEventListener('click', () => {
            console.log('AI Process button clicked!'); // Debug log
            this.handleAIProcess();
        });
    }

    async handleUpdateGift(e) {
        if (this.isSubmitting) return;
        
        const form = this.editGiftForm;
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
        
        this.isSubmitting = true;
        const formData = this.getFormData();
        const giftId = window.location.pathname.split('/').filter(Boolean).pop();
        
        try {
            const response = await fetch(`/api/gifts/${giftId}/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            if (response.ok) {
                this.editBsModal.hide();
                window.location.reload();
            } else {
                alert(data.error || 'Failed to update gift');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to update gift');
        } finally {
            this.isSubmitting = false;
        }
    }

    async handleAIProcess() {
        console.log('handleAIProcess called'); // Debug log
        
        if (this.isProcessing) {
            console.log('Already processing, returning...'); // Debug log
            return;
        }
        
        this.isProcessing = true;
        this.processWithAIBtn.disabled = true; // Disable button while processing
        
        // Show processing toast
        const toast = bootstrap.Toast.getOrCreateInstance(document.getElementById('processingToast'));
        toast.show();
        
        const giftId = window.location.pathname.split('/').filter(Boolean).pop();
        console.log('Processing gift ID:', giftId); // Debug log
        
        try {
            const response = await fetch(`/api/gifts/${giftId}/process/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });
            
            const data = await response.json();
            console.log('AI Process response:', data); // Debug log
            
            if (response.ok) {
                // Update the form with AI suggestions
                const form = this.editGiftForm;
                
                // Update tags
                if (data.tags) {
                    const tagSelect = form.querySelector('[name="tags"]');
                    Array.from(tagSelect.options).forEach(option => {
                        option.selected = data.tags.includes(option.value);
                    });
                }
                
                // Update recipients
                if (data.recipients) {
                    const recipientSelect = form.querySelector('[name="recipients"]');
                    Array.from(recipientSelect.options).forEach(option => {
                        option.selected = data.recipients.includes(option.value);
                    });
                }
                
                // Show the edit modal with the updates
                this.editBsModal.show();
            } else {
                // Show error message
                const errorToast = bootstrap.Toast.getOrCreateInstance(document.getElementById('errorToast'));
                document.getElementById('errorToastMessage').textContent = data.error || 'Failed to process with AI';
                errorToast.show();
            }
        } catch (error) {
            console.error('AI Process error:', error); // Debug log
            // Show error message
            const errorToast = bootstrap.Toast.getOrCreateInstance(document.getElementById('errorToast'));
            document.getElementById('errorToastMessage').textContent = 'Failed to process with AI';
            errorToast.show();
        } finally {
            this.isProcessing = false;
            this.processWithAIBtn.disabled = false; // Re-enable button
            // Hide processing toast
            const toast = bootstrap.Toast.getOrCreateInstance(document.getElementById('processingToast'));
            toast.hide();
        }
    }

    getFormData() {
        const form = this.editGiftForm;
        const formData = {
            title: form.querySelector('[name="title"]').value,
            price: parseFloat(form.querySelector('[name="price"]').value),
            status: form.querySelector('[name="status"]').value,
            url: form.querySelector('[name="url"]').value,
            image_url: form.querySelector('[name="image_url"]').value,
            description: form.querySelector('[name="description"]').value,
            notes: form.querySelector('[name="notes"]').value,
            tags: Array.from(form.querySelector('[name="tags"]').selectedOptions).map(opt => parseInt(opt.value)),
            recipients: Array.from(form.querySelector('[name="recipients"]').selectedOptions).map(opt => parseInt(opt.value))
        };
        
        return formData;
    }

    handleModalHidden() {
        this.isSubmitting = false;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new GiftDetail();
}); 