class GiftDetail {
    constructor() {
        // Forms and modals
        this.editGiftForm = document.getElementById('editGiftForm');
        this.editGiftModal = document.getElementById('editGiftModal');
        this.editBsModal = new bootstrap.Modal(this.editGiftModal);
        
        // Buttons
        this.saveGiftBtn = document.getElementById('saveGiftBtn');
        
        // State
        this.isSubmitting = false;
        
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        this.editGiftModal.addEventListener('hidden.bs.modal', () => this.handleModalHidden());
        this.saveGiftBtn.addEventListener('click', (e) => this.handleUpdateGift(e));
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