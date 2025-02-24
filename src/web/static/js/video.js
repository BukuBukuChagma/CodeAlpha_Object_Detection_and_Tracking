document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('upload-form');
    const confThreshold = document.getElementById('conf-threshold');
    const confValue = document.getElementById('conf-value');
    const videoInput = document.getElementById('video-input');
    const submitButton = form.querySelector('button[type="submit"]');
    const previewSection = document.getElementById('preview-section');
    const previewVideo = document.getElementById('preview-video');
    const videoInfo = document.querySelector('.video-info');
    const fileLabel = document.querySelector('.file-label');
    const progressSection = document.getElementById('progress-section');
    const progressFill = document.querySelector('.progress-fill');
    const progressValue = document.getElementById('progress-value');
    const statusText = document.getElementById('status-text');
    const resultsSection = document.getElementById('results-section');
    const errorMessage = document.getElementById('error-message');

    // Add this at the top level of the DOMContentLoaded callback
    let pollInterval = null;  // Store interval ID
    let isProcessingComplete = false;  // Track processing status

    // Update confidence threshold value display
    confThreshold.addEventListener('input', function() {
        confValue.textContent = this.value;
    });

    // Handle file selection
    videoInput.addEventListener('change', async function() {
        const file = this.files[0];
        
        // Clean up previous files
        await cleanupFiles();
        
        if (file) {
            // Show preview
            previewVideo.src = URL.createObjectURL(file);
            previewSection.classList.remove('hidden');
            fileLabel.textContent = file.name;
            submitButton.disabled = false;

            // Show video info
            const duration = await getVideoDuration(previewVideo);
            const size = formatFileSize(file.size);
            videoInfo.textContent = `Duration: ${formatDuration(duration)} | Size: ${size}`;
        } else {
            previewSection.classList.add('hidden');
            fileLabel.textContent = 'Choose Video';
            submitButton.disabled = true;
            videoInfo.textContent = '';
        }
    });

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Reset processing status
        isProcessingComplete = false;
        if (pollInterval) {
            clearInterval(pollInterval);
        }

        const formData = new FormData();
        const videoFile = videoInput.files[0];
        
        if (!videoFile) {
            showError('Please select a video file.');
            return;
        }

        // Clear content before processing
        clearContent();

        // Disable form elements during processing
        submitButton.disabled = true;
        videoInput.disabled = true;
        confThreshold.disabled = true;
        submitButton.innerHTML = '<span class="spinner"></span> Starting...';

        try {
            // Clean up previous files
            await cleanupFiles();

            formData.append('video', videoFile);
            formData.append('conf_threshold', confThreshold.value);
            formData.append('save_output', 'true');

            // Start processing
            const response = await fetch('/api/v1/detect/video', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (!data.success) {
                throw new Error(data.error.message);
            }

            // Show progress section
            progressSection.classList.remove('hidden');
            resultsSection.classList.add('hidden');
            errorMessage.classList.add('hidden');

            // Poll for progress
            const taskId = data.data.task_id;
            await pollProgress(taskId);

        } catch (error) {
            showError(error.message);
        } finally {
            // Re-enable form elements
            submitButton.disabled = false;
            videoInput.disabled = false;
            confThreshold.disabled = false;
            submitButton.textContent = 'Process Video';
        }
    });

    async function pollProgress(taskId) {
        // Clear any existing interval
        if (pollInterval) {
            clearInterval(pollInterval);
        }
        
        isProcessingComplete = false;
        
        pollInterval = setInterval(async () => {
            // Don't make new requests if processing is complete
            if (isProcessingComplete) {
                clearInterval(pollInterval);
                return;
            }

            try {
                const response = await fetch(`/api/v1/detect/video/status/${taskId}`);
                const data = await response.json();

                if (!data.success) {
                    throw new Error(data.error.message);
                }

                const status = data.data;
                updateProgress(status);

                if (status.status === 'completed') {
                    isProcessingComplete = true;
                    clearInterval(pollInterval);
                    displayResults(status.result);
                } else if (status.status === 'failed') {
                    isProcessingComplete = true;
                    clearInterval(pollInterval);
                    throw new Error(status.error || 'Processing failed');
                }
            } catch (error) {
                isProcessingComplete = true;
                clearInterval(pollInterval);
                showError(error.message);
            }
        }, 2000);

        // Clean up interval when leaving page
        window.addEventListener('beforeunload', () => {
            if (pollInterval) {
                clearInterval(pollInterval);
            }
        });
    }

    function updateProgress(status) {
        const progress = status.progress || 0;
        progressFill.style.width = `${progress}%`;
        progressValue.textContent = Math.round(progress);
        
        if (status.status === 'processing') {
            statusText.textContent = 'Processing video...';
        } else if (status.status === 'completed') {
            statusText.textContent = 'Processing complete!';
        }
    }

    function displayResults(result) {
        // Set processing complete flag first
        isProcessingComplete = true;
        if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }

        // Update processing info
        document.getElementById('processing-time').textContent = 
            result.processing_time.toFixed(2);
        document.getElementById('frames-processed').textContent = 
            result.frames_processed;
        
        // Setup download link
        const downloadLink = document.getElementById('download-link');
        downloadLink.href = result.output_video_url;
        downloadLink.download = `processed_${videoInput.files[0].name}`;

        // Show results section
        resultsSection.classList.remove('hidden');
        progressSection.classList.add('hidden');
        errorMessage.classList.add('hidden');
    }

    // Helper functions
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

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
        progressSection.classList.add('hidden');
        resultsSection.classList.add('hidden');
    }

    function getVideoDuration(video) {
        return new Promise((resolve) => {
            video.onloadedmetadata = () => resolve(video.duration);
        });
    }

    function formatDuration(seconds) {
        return new Date(seconds * 1000).toISOString().substr(11, 8);
    }

    function formatFileSize(bytes) {
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 Byte';
        const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
        return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
    }

    // Clean up when leaving the page
    window.addEventListener('beforeunload', () => {
        navigator.sendBeacon('/api/v1/cleanup');
    });

    // Add this function near other utility functions
    function clearContent() {
        // Clear preview
        previewSection.classList.add('hidden');
        previewVideo.src = '';
        videoInfo.textContent = '';
        
        // Clear results
        resultsSection.classList.add('hidden');
        document.getElementById('processing-time').textContent = '-';
        document.getElementById('frames-processed').textContent = '-';
        
        // Reset progress
        progressSection.classList.add('hidden');
        progressFill.style.width = '0%';
        progressValue.textContent = '0';
        statusText.textContent = 'Initializing...';
        
        // Reset form elements
        fileLabel.textContent = 'Choose Video';
    }
}); 