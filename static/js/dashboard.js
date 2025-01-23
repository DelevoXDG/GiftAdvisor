class Dashboard {
    constructor() {
        // Form elements
        this.addGiftForm = document.getElementById('addGiftForm');
        this.addGiftModal = document.getElementById('addGiftModal');
        this.bsModal = new bootstrap.Modal(this.addGiftModal);
        this.quickAddForm = document.getElementById('quickAddForm');
        this.quickAddInput = this.quickAddForm.querySelector('input[name="url"]');
        this.quickAddButton = this.quickAddForm.querySelector('.search-button');
        
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
        this.currentAIModel = document.body.dataset.aiModel;
        
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
        this.quickAddButton.style.opacity = hasValue ? '1' : '0.5';
        this.quickAddButton.style.cursor = hasValue ? 'pointer' : 'not-allowed';
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
        
        // Show appropriate message based on AI model
        const toast = bootstrap.Toast.getOrCreateInstance(document.getElementById('processingToast'));
        if (this.currentAIModel !== 'none') {
            document.getElementById('processingToastMessage').textContent = "Processing gift idea with AI...";
            toast.show();
        }
        
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
                // Show success message
                const successToast = document.createElement('div');
                successToast.className = 'toast';
                successToast.innerHTML = `
                    <div class="toast-header bg-success text-white">
                        <i class="bi bi-check-circle me-2"></i>
                        <strong class="me-auto">Success</strong>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
                    </div>
                    <div class="toast-body">
                        Gift idea added successfully
                    </div>
                `;
                document.querySelector('.toast-container').appendChild(successToast);
                new bootstrap.Toast(successToast).show();
                
                // Refresh the page after a short delay
                setTimeout(() => window.location.reload(), 1000);
            } else {
                // Show error message
                const errorToast = bootstrap.Toast.getOrCreateInstance(document.getElementById('errorToast'));
                document.getElementById('errorToastMessage').textContent = data.error || 'Failed to add gift idea';
                errorToast.show();
                this.isSubmitting = false;
            }
        } catch (error) {
            console.error('Error:', error);
            // Show error message
            const errorToast = bootstrap.Toast.getOrCreateInstance(document.getElementById('errorToast'));
            document.getElementById('errorToastMessage').textContent = 'Failed to add gift idea';
            errorToast.show();
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
        
        // Show appropriate message based on AI model
        const processingToast = bootstrap.Toast.getOrCreateInstance(document.getElementById('processingToast'));
        if (this.currentAIModel !== 'none') {
            document.getElementById('processingToastMessage').textContent = "Processing gift idea with AI...";
            processingToast.show();
        }
        
        try {
            const response = await fetch('/api/extract-metadata/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({ url: url })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Add the gift
                const giftResponse = await fetch('/api/gifts/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    },
                    body: JSON.stringify(data)
                });
                
                const giftData = await giftResponse.json();
                
                if (giftResponse.ok) {
                    // Show success message
                    const successToast = document.createElement('div');
                    successToast.className = 'toast';
                    successToast.innerHTML = `
                        <div class="toast-header bg-success text-white">
                            <i class="bi bi-check-circle me-2"></i>
                            <strong class="me-auto">Success</strong>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
                        </div>
                        <div class="toast-body">
                            Gift idea added successfully
                        </div>
                    `;
                    document.querySelector('.toast-container').appendChild(successToast);
                    new bootstrap.Toast(successToast).show();
                    
                    // Reset form
                    this.quickAddForm.reset();
                    
                    // Refresh the page after a short delay
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    const errorToast = bootstrap.Toast.getOrCreateInstance(document.getElementById('errorToast'));
                    document.getElementById('errorToastMessage').textContent = giftData.error || 'Failed to add gift';
                    errorToast.show();
                }
            } else {
                const errorToast = bootstrap.Toast.getOrCreateInstance(document.getElementById('errorToast'));
                document.getElementById('errorToastMessage').textContent = data.error || 'Failed to extract metadata';
                errorToast.show();
            }
        } catch (error) {
            console.error('Error:', error);
            const errorToast = bootstrap.Toast.getOrCreateInstance(document.getElementById('errorToast'));
            document.getElementById('errorToastMessage').textContent = 'Failed to process the URL';
            errorToast.show();
        } finally {
            this.isExtracting = false;
            this.quickAddInput.disabled = false;
            this.quickAddButton.disabled = false;
            this.updateQuickAddButtonState();
            processingToast.hide();
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