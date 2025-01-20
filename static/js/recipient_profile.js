class RecipientProfile {
    constructor() {
        // Elements
        this.editForm = document.getElementById('editRecipientForm');
        this.saveButton = document.getElementById('saveRecipientBtn');
        this.editModal = document.getElementById('editRecipientModal');
        this.bsEditModal = new bootstrap.Modal(this.editModal);
        
        this.addGiftModal = document.getElementById('addGiftModal');
        this.bsAddGiftModal = new bootstrap.Modal(this.addGiftModal);
        this.searchInput = document.getElementById('giftSearch');
        this.searchResults = document.getElementById('searchResults');
        
        // View toggle elements
        this.gridViewBtn = document.getElementById('gridViewBtn');
        this.listViewBtn = document.getElementById('listViewBtn');
        this.giftGrid = document.querySelector('.gift-grid');
        this.giftList = document.querySelector('.gift-list');
        
        // State
        this.isSubmitting = false;
        this.searchTimeout = null;
        this.recipientId = window.location.pathname.split('/').filter(Boolean).pop();
        
        this.initializeEventListeners();
        this.restoreLayoutPreference();
    }

    initializeEventListeners() {
        // Edit form events
        this.saveButton.addEventListener('click', () => this.handleSave());
        this.editModal.addEventListener('hidden.bs.modal', () => this.handleModalHidden());
        
        // Search events
        this.searchInput.addEventListener('input', () => this.handleSearch());
        this.addGiftModal.addEventListener('hidden.bs.modal', () => this.handleSearchModalHidden());
        this.addGiftModal.addEventListener('shown.bs.modal', () => this.loadRecentGifts());
        
        // View toggling
        this.gridViewBtn.addEventListener('click', () => this.toggleView('grid'));
        this.listViewBtn.addEventListener('click', () => this.toggleView('list'));
    }

    restoreLayoutPreference() {
        const savedLayout = localStorage.getItem('giftLayoutPreference');
        if (savedLayout) {
            this.toggleView(savedLayout, false);
        }
    }

    async handleSave() {
        if (this.isSubmitting) return;
        
        const formData = new FormData(this.editForm);
        const data = {
            name: formData.get('name'),
            relationship: formData.get('relationship'),
            birth_date: formData.get('birth_date') || null,
            interests: Array.from(this.editForm.querySelector('[name="interests"]').selectedOptions).map(opt => opt.value),
            notes: formData.get('notes')
        };
        
        try {
            this.isSubmitting = true;
            const response = await fetch(`/api/recipients/${this.recipientId}/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                window.location.reload();
            } else {
                const error = await response.json();
                alert(error.error || 'Failed to update recipient');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to update recipient');
        } finally {
            this.isSubmitting = false;
        }
    }

    handleSearch() {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => this.performSearch(), 300);
    }

    async performSearch() {
        const query = this.searchInput.value.trim();
        if (!query) {
            this.loadRecentGifts();
            return;
        }
        
        try {
            const response = await fetch(`/api/gifts/search/?q=${encodeURIComponent(query)}`);
            const gifts = await response.json();
            this.displaySearchResults(gifts);
        } catch (error) {
            console.error('Error:', error);
        }
    }

    async loadRecentGifts() {
        try {
            const response = await fetch('/api/gifts/recent/');
            const gifts = await response.json();
            this.displaySearchResults(gifts);
        } catch (error) {
            console.error('Error:', error);
        }
    }

    displaySearchResults(gifts) {
        this.searchResults.innerHTML = gifts.map(gift => `
            <div class="gift-card gift-search-item" data-gift-id="${gift.id}">
                <div class="empty-img">
                    ${gift.image_url 
                        ? `<img src="${gift.image_url}" alt="${gift.title}" class="gift-image">`
                        : '<i class="bi bi-image-fill" style="font-size: 2rem; opacity: 0.5;"></i>'
                    }
                </div>
                <div class="p-4">
                    <h5 class="fw-bold mb-2">${gift.title}</h5>
                    <p class="text-primary fw-bold mb-3">$${gift.price}</p>
                    <div class="d-flex flex-wrap gap-2">
                        ${gift.tags.map(tag => `
                            <span class="badge bg-primary">${tag.name}</span>
                        `).join('')}
                    </div>
                </div>
            </div>
        `).join('');
        
        // Add click handlers
        this.searchResults.querySelectorAll('.gift-search-item').forEach(item => {
            item.addEventListener('click', () => this.addGiftToRecipient(item.dataset.giftId));
        });
    }

    async addGiftToRecipient(giftId) {
        try {
            const response = await fetch(`/api/recipients/${this.recipientId}/gifts/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({ gift_id: giftId })
            });
            
            if (response.ok) {
                window.location.reload();
            } else {
                const error = await response.json();
                alert(error.error || 'Failed to add gift');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to add gift');
        }
    }

    handleModalHidden() {
        this.editForm.reset();
        this.isSubmitting = false;
    }

    handleSearchModalHidden() {
        this.searchInput.value = '';
        this.searchResults.innerHTML = '';
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
            localStorage.setItem('giftLayoutPreference', type);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new RecipientProfile();
}); 