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
        
        // Elements
        this.searchInput = document.getElementById('recipientSearch');
        this.gridViewBtn = document.getElementById('gridViewBtn');
        this.listViewBtn = document.getElementById('listViewBtn');
        this.giftGrid = document.querySelector('.gift-grid');
        this.giftList = document.querySelector('.gift-list');
        
        // State
        this.searchTimeout = null;
        
        this.initializeEventListeners();
        this.restoreLayoutPreference();
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
        
        // Search
        this.searchInput.addEventListener('input', () => this.handleSearch());
        
        // View toggling
        this.gridViewBtn.addEventListener('click', () => this.toggleView('grid'));
        this.listViewBtn.addEventListener('click', () => this.toggleView('list'));
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

    handleSearch() {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => this.performSearch(), 300);
    }

    performSearch() {
        const query = this.searchInput.value.toLowerCase().trim();
        const recipients = document.querySelectorAll('.gift-grid > a, .gift-list > a');
        
        recipients.forEach(recipient => {
            const name = recipient.querySelector('h5').textContent.toLowerCase();
            const relationship = recipient.querySelector('.badge').textContent.toLowerCase();
            const notes = recipient.querySelector('p.text-muted')?.textContent.toLowerCase() || '';
            const interests = Array.from(recipient.querySelectorAll('.badge.bg-secondary'))
                .map(badge => badge.textContent.toLowerCase());
            
            const matches = name.includes(query) || 
                           relationship.includes(query) || 
                           notes.includes(query) ||
                           interests.some(interest => interest.includes(query));
            
            recipient.style.display = matches ? '' : 'none';
        });
    }

    restoreLayoutPreference() {
        const savedLayout = localStorage.getItem('recipientLayoutPreference');
        if (savedLayout) {
            this.toggleView(savedLayout, false);
        }
    }

    toggleView(type, savePreference = true) {
        if (type === 'grid') {
            this.gridViewBtn.classList.add('active');
            this.listViewBtn.classList.remove('active');
            this.giftGrid.classList.remove('d-none');
            this.giftList.classList.add('d-none');
        } else {
            this.listViewBtn.classList.add('active');
            this.gridViewBtn.classList.remove('active');
            this.giftList.classList.remove('d-none');
            this.giftGrid.classList.add('d-none');
        }
        
        if (savePreference) {
            localStorage.setItem('recipientLayoutPreference', type);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new Recipients();
}); 