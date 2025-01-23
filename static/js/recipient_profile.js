class RecipientProfile {
    constructor() {
        // Form elements
        this.editForm = document.getElementById('editRecipientForm');
        this.editModal = document.getElementById('editRecipientModal');
        this.bsModal = new bootstrap.Modal(this.editModal);
        this.searchInput = document.getElementById('giftSearch');
        this.searchResults = document.getElementById('searchResults');
        this.filterForm = document.getElementById('filterForm');
        
        // View toggle elements
        this.gridViewBtn = document.getElementById('gridViewBtn');
        this.listViewBtn = document.getElementById('listViewBtn');
        this.giftGrid = document.getElementById('giftGrid');
        this.giftList = document.getElementById('giftList');
        
        // State
        this.recipientId = window.location.pathname.split('/').filter(Boolean).pop();
        this.isSubmitting = false;
        this.searchTimeout = null;
        
        // Interests elements
        this.interestInput = document.getElementById('interestInput');
        this.addInterestBtn = document.getElementById('addInterestBtn');
        this.selectedInterests = document.getElementById('selectedInterests');
        this.interestsInput = document.getElementById('interestsInput');
        
        // Initialize interests
        this.interests = new Set(
            Array.from(this.selectedInterests.querySelectorAll('.badge'))
                .map(badge => badge.textContent.trim())
        );
        
        this.initializeEventListeners();
        this.restoreLayoutPreference();
    }

    initializeEventListeners() {
        // Modal events
        this.editModal.addEventListener('hidden.bs.modal', () => this.handleModalHidden());
        
        // Search events
        this.searchInput.addEventListener('input', (e) => this.handleSearch(e));
        
        // Filter form
        this.filterForm.querySelectorAll('select').forEach(select => {
            select.addEventListener('change', () => this.filterForm.submit());
        });
        
        // Add event listeners for interests
        if (this.interestInput) {
            this.interestInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.addInterest();
                }
            });
        }
        
        if (this.addInterestBtn) {
            this.addInterestBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.addInterest();
            });
        }
    }

    restoreLayoutPreference() {
        const savedLayout = localStorage.getItem('giftLayoutPreference');
        if (savedLayout) {
            this.toggleView(savedLayout, false);
        }
    }

    handleSearch(e) {
        clearTimeout(this.searchTimeout);
        const query = e.target.value.trim();
        
        this.searchTimeout = setTimeout(async () => {
            if (query.length < 2) {
                this.searchResults.innerHTML = '';
                return;
            }
            
            try {
                const response = await fetch(`/api/gifts/search/?q=${encodeURIComponent(query)}`);
                const gifts = await response.json();
                
                this.renderSearchResults(gifts);
            } catch (error) {
                console.error('Error searching gifts:', error);
            }
        }, 300);
    }

    renderSearchResults(gifts) {
        if (!gifts.length) {
            this.searchResults.innerHTML = `
                <div class="text-center py-5">
                    <i class="bi bi-search mb-4" style="font-size: 3rem; opacity: 0.5;"></i>
                    <h4 class="fw-bold" style="font-size: 1.25rem;">No gifts found</h4>
                    <p class="text-muted" style="font-size: 0.95rem;">Try a different search term.</p>
                </div>
            `;
            return;
        }
        
        this.searchResults.innerHTML = gifts.map(gift => `
            <div class="gift-card clickable" onclick="recipientProfile.addGiftToRecipient(${gift.id})">
                <div class="empty-img">
                    ${gift.image_url ? `<img src="${gift.image_url}" alt="${gift.title}" class="gift-image">` : '<i class="bi bi-image-fill" style="font-size: 2rem; opacity: 0.5;"></i>'}
                </div>
                <div class="p-4">
                    <h5 class="fw-bold mb-2" style="font-size: 1.1rem;">${gift.title}</h5>
                    ${gift.price ? `<p class="text-primary fw-bold mb-3" style="font-size: 0.95rem;">$${gift.price}</p>` : ''}
                    <div class="d-flex flex-wrap gap-2">
                        ${gift.tags.map(tag => `<span class="badge bg-primary" style="font-size: 0.8rem;">${tag.name}</span>`).join('')}
                    </div>
                </div>
            </div>
        `).join('');
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

    handleModalHidden() {
        this.editForm.reset();
        this.isSubmitting = false;
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

    addInterest() {
        const interest = this.interestInput.value.trim();
        if (!interest) return;
        
        if (!this.interests.has(interest)) {
            this.interests.add(interest);
            
            const badge = document.createElement('span');
            badge.className = 'badge bg-primary d-flex align-items-center gap-1';
            badge.innerHTML = `
                ${interest}
                <button type="button" class="btn-close btn-close-white btn-sm" 
                        onclick="recipientProfile.removeInterest(null, '${interest}')"
                        style="font-size: 0.5rem;"></button>
            `;
            
            this.selectedInterests.appendChild(badge);
            this.updateInterestsInput();
        }
        
        this.interestInput.value = '';
    }
    
    removeInterest(id, name) {
        this.interests.delete(name);
        const badge = Array.from(this.selectedInterests.children)
            .find(el => el.textContent.trim() === name);
        if (badge) {
            badge.remove();
            this.updateInterestsInput();
        }
    }
    
    updateInterestsInput() {
        this.interestsInput.value = Array.from(this.interests).join(',');
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
}

// Initialize when DOM is loaded
let recipientProfile;
document.addEventListener('DOMContentLoaded', () => {
    recipientProfile = new RecipientProfile();
}); 