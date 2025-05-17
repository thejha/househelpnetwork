/**
 * HouseHelpNetwork Main JavaScript
 */

function searchPincode(pincode) {
    if (pincode.length >= 6) {
        fetch(`/admin/pincodes/search?term=${pincode}`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.results.length > 0) {
                    const result = data.results[0];
                    document.getElementById('state').value = result.state;
                    document.getElementById('city').value = result.city;
                    document.getElementById('society').value = result.society;
                }
            })
            .catch(error => {
                console.error('Error searching pincode:', error);
            });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Add pincode search event listener
    const pincodeInput = document.getElementById('pincode');
    if (pincodeInput) {
        pincodeInput.addEventListener('input', function(e) {
            searchPincode(e.target.value);
        });
    }
    // Flash messages auto-dismiss
    const flashMessages = document.querySelectorAll('.alert-dismissible');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            const closeButton = message.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000); // Dismiss after 5 seconds
    });

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Rating system for reviews
    const ratingInputs = document.querySelectorAll('.rating-input');
    ratingInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            const value = this.value;
            const name = this.getAttribute('name');
            
            // Update the visible stars
            const stars = document.querySelectorAll(`[data-rating="${name}"] .star`);
            stars.forEach(function(star, index) {
                if (index < value) {
                    star.classList.add('active');
                } else {
                    star.classList.remove('active');
                }
            });
        });
    });

    // Task selector for contracts
    const taskSelector = document.getElementById('tasks');
    if (taskSelector) {
        const selectedTasks = new Set();
        
        // Initialize Bootstrap multiselect
        $(taskSelector).multiselect({
            includeSelectAllOption: true,
            nonSelectedText: 'Select Tasks',
            onChange: function(option, checked) {
                const taskId = option.val();
                if (checked) {
                    selectedTasks.add(taskId);
                } else {
                    selectedTasks.delete(taskId);
                }
            }
        });
    }
    
    // Search form type toggle
    const searchTypeSelector = document.getElementById('search_type');
    const searchValueInput = document.getElementById('search_value');
    const searchValueLabel = document.querySelector('label[for="search_value"]');
    
    if (searchTypeSelector && searchValueInput && searchValueLabel) {
        searchTypeSelector.addEventListener('change', function() {
            const searchType = this.value;
            
            if (searchType === 'gov_id') {
                searchValueLabel.textContent = 'Enter Government ID';
                searchValueInput.placeholder = 'Aadhar/Voter ID/Driving License';
            } else if (searchType === 'phone_number') {
                searchValueLabel.textContent = 'Enter Phone Number';
                searchValueInput.placeholder = 'Phone Number';
            }
        });
    }
    
    // Helper profile image preview
    const photoInput = document.getElementById('photo');
    const photoPreview = document.getElementById('photo-preview');
    
    if (photoInput && photoPreview) {
        photoInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    photoPreview.src = e.target.result;
                    photoPreview.style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        });
    }
    
    // Document preview 
    const documentInput = document.getElementById('documents');
    const documentPreviewContainer = document.getElementById('document-previews');
    
    if (documentInput && documentPreviewContainer) {
        documentInput.addEventListener('change', function() {
            documentPreviewContainer.innerHTML = '';
            
            for (let i = 0; i < this.files.length; i++) {
                const file = this.files[i];
                const docPreview = document.createElement('div');
                docPreview.className = 'document-preview';
                
                const docName = document.createElement('span');
                docName.textContent = file.name;
                
                docPreview.appendChild(docName);
                documentPreviewContainer.appendChild(docPreview);
            }
        });
    }
    
    // Review ratings visualization
    const ratingElements = document.querySelectorAll('.rating-display');
    ratingElements.forEach(function(element) {
        const rating = parseFloat(element.getAttribute('data-rating'));
        const maxRating = 5;
        
        for (let i = 1; i <= maxRating; i++) {
            const star = document.createElement('span');
            star.className = i <= rating ? 'star filled' : 'star empty';
            star.innerHTML = '★';
            element.appendChild(star);
        }
        
        const ratingText = document.createElement('span');
        ratingText.className = 'rating-text';
        ratingText.textContent = ` ${rating.toFixed(1)}`;
        element.appendChild(ratingText);
    });
    
    // Initialize datepickers
    const datepickers = document.querySelectorAll('.datepicker');
    datepickers.forEach(function(picker) {
        new Datepicker(picker, {
            format: 'yyyy-mm-dd',
            autohide: true
        });
    });
});

// Helper function to confirm deletion
function confirmDelete(type, name) {
    return confirm(`Are you sure you want to delete ${type}: ${name}?`);
}

// Helper function to toggle sections visibility
function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.classList.toggle('d-none');
    }
}
