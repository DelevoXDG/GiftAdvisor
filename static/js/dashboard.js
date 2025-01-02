class Dashboard {
    constructor() {
        // Form elements
        this.addGiftForm = document.getElementById('addGiftForm');
        this.addGiftModal = document.getElementById('addGiftModal');
        this.bsModal = new bootstrap.Modal(this.addGiftModal);
        this.quickAddForm = document.getElementById('quickAddForm');
        this.quickAddInput = this.quickAddForm.querySelector('input[name="url"]');
        this.quickAddButton = this.quickAddForm.querySelector('button[type="submit"]');
        
        // View toggle elements
        this.gridViewBtn = document.getElementById('gridViewBtn');
        this.listViewBtn = document.getElementById('listViewBtn');
        this.giftGrid = document.querySelector('.gift-grid');
        this.giftList = document.querySelector('.gift-list');
        
        // Filter form
        this.filterForm = document.getElementById('filterForm');
        
        // State
        this.isSubmitting = false;
		this.isExtracting = false;
		        this.currentExtraction = null;

        
		this.initializeEventListeners();
		this.restoreLayoutPreference();
        
        // Initial button state
        this.updateQuickAddButtonState();
    }

    initializeEventListeners() {
        // Modal events
        this.addGiftModal.addEventListener('hidden.bs.modal', () => this.handleModalHidden());
        document.getElementById('submitGiftBtn').addEventListener('click', (e) => this.handleGiftSubmit(e));
        
        // Quick add form
		this.quickAddForm.addEventListener('submit', (e) => this.handleQuickAdd(e));
		this.quickAddInput.addEventListener('input', () => this.updateQuickAddButtonState());
        
        // View toggling
        this.gridViewBtn.addEventListener('click', () => this.toggleView('grid'));
        this.listViewBtn.addEventListener('click', () => this.toggleView('list'));
        
        // Filter form
        this.filterForm.querySelectorAll('select').forEach(select => {
            select.addEventListener('change', () => this.filterForm.submit());
        });
	}
	
    updateQuickAddButtonState() {
        const hasValue = this.quickAddInput.value.trim() !== '';
        this.quickAddButton.disabled = !hasValue;
    }

    restoreLayoutPreference() {
        const savedLayout = localStorage.getItem('giftLayoutPreference');
        if (savedLayout) {
            this.toggleView(savedLayout, false);
        }
    }

    async handleGiftSubmit(e) {
        if (this.isSubmitting) return;
        if (!this.addGiftForm.checkValidity()) {
            this.addGiftForm.reportValidity();
            return;
        }
        this.isSubmitting = true;
        
        const formData = {
            title: this.addGiftForm.querySelector('[name="title"]').value,
            description: this.addGiftForm.querySelector('[name="description"]').value,
            price: parseFloat(this.addGiftForm.querySelector('[name="price"]').value),
            url: this.addGiftForm.querySelector('[name="url"]').value,
            image_url: this.addGiftForm.querySelector('[name="image_url"]')?.value || '',
            recipients: Array.from(this.addGiftForm.querySelector('select[multiple]').selectedOptions).map(opt => opt.value),
            tags: Array.from(this.addGiftForm.querySelectorAll('select[multiple]')[1].selectedOptions).map(opt => opt.value)
        };

        try {
            const response = await fetch('/api/gifts/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();
            
            if (response.ok) {
                this.bsModal.hide();
                window.location.reload();
            } else {
                alert(data.error || 'Failed to add gift idea');
                this.isSubmitting = false;
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to add gift idea');
            this.isSubmitting = false;
        }
    }

    async handleQuickAdd(e) {
        e.preventDefault();
		if (this.isExtracting) return;
		
		const url = this.quickAddInput.value.trim();
		if (!url) return;
		
        this.isExtracting = true;
        
        this.quickAddInput.disabled = true;
		this.quickAddButton.disabled = true;
		
		        // Cancel any ongoing extraction
        if (this.currentExtraction) {
            this.currentExtraction.abort();
        }
        
        // Create new AbortController for this extraction
        const controller = new AbortController();
        this.currentExtraction = controller;
      
        
        try {
            const response = await fetch('/api/extract-metadata/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({
                    url: this.quickAddInput.value
				}),
				signal: controller.signal
			});
			
            // Only proceed if this is still the current extraction
            if (this.currentExtraction === controller) {
				const data = await response.json();
				
				if (response.ok) {
					this.addGiftForm.reset();
					
					this.addGiftForm.querySelector('input[name="title"]').value = data.title || '';
					this.addGiftForm.querySelector('textarea[name="description"]').value = data.description || '';
					this.addGiftForm.querySelector('input[name="price"]').value = data.price || '';
					this.addGiftForm.querySelector('input[name="url"]').value = data.url || '';
					this.addGiftForm.querySelector('input[name="image_url"]').value = data.image_url || '';
					
					this.bsModal.show();
					this.quickAddForm.reset();
				} else {
					alert(data.error || 'Failed to extract metadata');
				}
            }
		} catch (error) {
			if (error.name !== 'AbortError') {
				console.error('Error:', error);
				alert('Failed to process the URL');
			}
		} finally {
			if (this.currentExtraction === controller) {
				this.currentExtraction = null;
				this.isExtracting = false;
				this.quickAddInput.disabled = false;
				this.quickAddButton.disabled = false;
				this.updateQuickAddButtonState();
			}
		}
    }

    handleModalHidden() {
        this.addGiftForm.reset();
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
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new Dashboard();
}); 