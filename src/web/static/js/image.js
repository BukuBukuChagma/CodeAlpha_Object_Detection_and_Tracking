document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('upload-form');
    const confThreshold = document.getElementById('conf-threshold');
    const confValue = document.getElementById('conf-value');
    const resultsSection = document.getElementById('results-section');
    const errorMessage = document.getElementById('error-message');
    const imageInput = document.getElementById('image-input');
    const submitButton = form.querySelector('button[type="submit"]');
    const previewSection = document.getElementById('preview-section');
    const previewImage = document.getElementById('preview-image');
    const fileLabel = document.querySelector('.file-label');

    // Update confidence threshold value display
    confThreshold.addEventListener('input', function() {
        confValue.textContent = this.value;
    });

    // Handle file selection
    imageInput.addEventListener('change', async function() {
        const file = this.files[0];
        
        // Clean up previous files first
        await cleanupFiles();
        
        if (file) {
            // Show preview
            previewImage.src = URL.createObjectURL(file);
            previewSection.classList.remove('hidden');
            fileLabel.textContent = file.name;
            submitButton.disabled = false;
        } else {
            previewSection.classList.add('hidden');
            fileLabel.textContent = 'Choose Image';
            submitButton.disabled = true;
        }
    });

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData();
        const imageFile = imageInput.files[0];
        
        if (!imageFile) {
            showError('Please select an image file.');
            return;
        }

        // Clear content before processing
        clearContent();

        // Disable form elements during processing
        submitButton.disabled = true;
        imageInput.disabled = true;
        confThreshold.disabled = true;
        submitButton.innerHTML = '<span class="spinner"></span> Processing...';

        try {
            // Clean up previous files before processing
            await cleanupFiles();

            formData.append('image', imageFile);
            formData.append('conf_threshold', confThreshold.value);

            const response = await fetch('/api/v1/detect/image', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error.message);
            }

            displayResults(data.data);
        } catch (error) {
            showError(error.message);
        } finally {
            // Re-enable form elements
            submitButton.disabled = false;
            imageInput.disabled = false;
            confThreshold.disabled = false;
            submitButton.textContent = 'Process Image';
        }
    });

    // Helper function for cleanup
    async function cleanupFiles() {
        try {
            const response = await fetch('/api/v1/cleanup', { method: 'POST' });
            const data = await response.json();
            if (!data.success) {
                console.error('Cleanup failed:', data.error.message);
            }
        } catch (error) {
            console.error('Error during cleanup:', error);
        }
    }

    // Clean up when leaving the page
    window.addEventListener('beforeunload', () => {
        // Send a synchronous cleanup request
        navigator.sendBeacon('/api/v1/cleanup');
    });

    function displayResults(data) {
        // Display images
        document.getElementById('original-image').src = URL.createObjectURL(
            imageInput.files[0]
        );
        document.getElementById('processed-image').src = data.processed_image_url;
        
        // Display detection results
        const detectionResults = document.getElementById('detection-results');
        detectionResults.innerHTML = data.detections.map(det => `
            <div class="detection">
                <strong>${det.class_name}</strong> (Confidence: ${(det.confidence * 100).toFixed(1)}%)
            </div>
        `).join('');

        // Display processing time
        document.getElementById('processing-time').textContent = 
            data.processing_time.toFixed(3);

        // Show results section
        resultsSection.classList.remove('hidden');
        errorMessage.classList.add('hidden');
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
        resultsSection.classList.add('hidden');
    }

    // Reset form and cleanup when selecting new image
    imageInput.addEventListener('click', async function() {
        // Clear previous results
        resultsSection.classList.add('hidden');
        previewSection.classList.add('hidden');
        errorMessage.classList.add('hidden');

        // Reset form elements
        form.reset();
        fileLabel.textContent = 'Choose Image';

        // Clean up server-side files
        try {
            await fetch('/api/v1/cleanup', { method: 'POST' });
        } catch (error) {
            console.error('Error cleaning up:', error);
        }
    });

    // Add this function near other utility functions
    function clearContent() {
        // Clear preview
        previewSection.classList.add('hidden');
        previewImage.src = '';
        
        // Clear results
        resultsSection.classList.add('hidden');
        document.getElementById('original-image').src = '';
        document.getElementById('processed-image').src = '';
        document.getElementById('detection-results').innerHTML = '';
        document.getElementById('processing-time').textContent = '-';
        
        // Reset form elements
        fileLabel.textContent = 'Choose Image';
    }
}); 