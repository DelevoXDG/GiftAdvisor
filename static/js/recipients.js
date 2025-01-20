class Recipients {
    constructor() {
        // Forms and modals
        this.addRecipientForm = document.getElementById('addRecipientForm');
        this.editRecipientForm = document.getElementById('editRecipientForm');
        this.addRecipientModal = document.getElementById('addRecipientModal');
        this.editRecipientModal = document.getElementById('editRecipientModal');
        this.addBsModal = new bootstrap.Modal(this.addRecipientModal);
        this.editBsModal = new bootstrap.Modal(this.editRecipientModal);
        
        // Buttons
        this.submitRecipientBtn = document.getElementById('submitRecipientBtn');
        this.updateRecipientBtn = document.getElementById('updateRecipientBtn');
        this.deleteRecipientBtn = document.getElementById('deleteRecipientBtn');
        
        // State
        this.isSubmitting = false;
        
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Modal events
        this.addRecipientModal.addEventListener('hidden.bs.modal', () => this.handleModalHidden(this.addRecipientForm));
        this.editRecipientModal.addEventListener('hidden.bs.modal', () => this.handleModalHidden(this.editRecipientForm));
        
        // Form submissions
        this.submitRecipientBtn.addEventListener('click', (e) => this.handleAddRecipient(e));
        this.updateRecipientBtn.addEventListener('click', (e) => this.handleUpdateRecipient(e));
        this.deleteRecipientBtn.addEventListener('click', (e) => this.handleDeleteRecipient(e));
        
        // Edit button clicks
        document.querySelectorAll('[data-recipient-id]').forEach(button => {
            button.addEventListener('click', (e) => this.handleEditClick(e));
        });
    }

    async handleAddRecipient(e) {
        if (this.isSubmitting) return;
        
        const form = this.addRecipientForm;
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
        
        this.isSubmitting = true;
        const formData = this.getFormData(form);
        
        try {
            const response = await fetch('/api/recipients/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            if (response.ok) {
                this.addBsModal.hide();
                window.location.reload();
            } else {
                alert(data.error || 'Failed to add recipient');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to add recipient');
        } finally {
            this.isSubmitting = false;
        }
    }

    async handleUpdateRecipient(e) {
        if (this.isSubmitting) return;
        
        const form = this.editRecipientForm;
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
        
        this.isSubmitting = true;
        const formData = this.getFormData(form);
        const recipientId = form.querySelector('[name="recipient_id"]').value;
        
        try {
            const response = await fetch(`/api/recipients/${recipientId}/`, {
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
                alert(data.error || 'Failed to update recipient');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to update recipient');
        } finally {
            this.isSubmitting = false;
        }
    }

    async handleDeleteRecipient(e) {
        if (!confirm('Are you sure you want to delete this recipient? This action cannot be undone.')) {
            return;
        }
        
        const recipientId = this.editRecipientForm.querySelector('[name="recipient_id"]').value;
        
        try {
            const response = await fetch(`/api/recipients/${recipientId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });
            
            if (response.ok) {
                this.editBsModal.hide();
                window.location.reload();
            } else {
                const data = await response.json();
                alert(data.error || 'Failed to delete recipient');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to delete recipient');
        }
    }

    async handleEditClick(e) {
        const recipientId = e.currentTarget.dataset.recipientId;
        
        try {
            const response = await fetch(`/api/recipients/${recipientId}/`);
            const data = await response.json();
            
            if (response.ok) {
                this.populateEditForm(data);
            } else {
                alert(data.error || 'Failed to fetch recipient details');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to fetch recipient details');
        }
    }

    populateEditForm(data) {
        const form = this.editRecipientForm;
        
        form.querySelector('[name="recipient_id"]').value = data.id;
        form.querySelector('[name="name"]').value = data.name;
        form.querySelector('[name="relationship"]').value = data.relationship;
        form.querySelector('[name="birth_date"]').value = data.birth_date || '';
        form.querySelector('[name="notes"]').value = data.notes || '';
        
        // Handle interests (multiple select)
        const interestsSelect = form.querySelector('[name="interests"]');
        Array.from(interestsSelect.options).forEach(option => {
            option.selected = data.interests.includes(parseInt(option.value));
        });
    }

    getFormData(form) {
        const formData = {
            name: form.querySelector('[name="name"]').value,
            relationship: form.querySelector('[name="relationship"]').value,
            birth_date: form.querySelector('[name="birth_date"]').value || null,
            notes: form.querySelector('[name="notes"]').value,
            interests: Array.from(form.querySelector('[name="interests"]').selectedOptions).map(opt => parseInt(opt.value))
        };
        
        return formData;
    }

    handleModalHidden(form) {
        form.reset();
        this.isSubmitting = false;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new Recipients();
}); 