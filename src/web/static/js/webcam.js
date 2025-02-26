const DEBUG = true;

document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const startButton = document.getElementById('start-stream');
    const stopButton = document.getElementById('stop-stream');
    const confThreshold = document.getElementById('conf-threshold');
    const confValue = document.getElementById('conf-value');
    const streamContainer = document.getElementById('stream-container');
    const video = document.getElementById('webcam-video');
    const canvas = document.getElementById('output-canvas');
    const fpsCounter = document.getElementById('fps-counter');
    const objectsCounter = document.getElementById('objects-counter');
    const errorMessage = document.getElementById('error-message');
    
    // Initialize socket connection with transport options
    const socket = io('/stream', {
        transports: ['websocket', 'polling'],
        upgrade: true
    });
    let streamId = null;

    // Update confidence threshold display
    confThreshold.addEventListener('input', function() {
        confValue.textContent = this.value;
    });

    // Handle start stream button
    startButton.addEventListener('click', async () => {
        try {
            if (DEBUG) console.log('Starting stream...');
            
            // Create form data (API expects form data, not JSON)
            const formData = new FormData();
            formData.append('conf_threshold', confThreshold.value);
            
            // Request server to start stream
            const response = await fetch('/api/v1/stream/start', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            if (!data.success) {
                throw new Error(data.error?.message || 'Unknown error');
            }

            // Get stream ID from the nested data structure
            streamId = data.data.stream_id;
            
            // Show stream container and stop button
            streamContainer.classList.remove('hidden');
            stopButton.classList.remove('hidden');
            startButton.classList.add('hidden');
            
            if (DEBUG) console.log('Stream started with ID:', streamId);
        } catch (error) {
            showError('Failed to start stream: ' + error.message);
        }
    });

    // Handle stop stream button
    stopButton.addEventListener('click', async () => {
        if (streamId) {
            try {
                if (DEBUG) console.log('Manually stopping stream:', streamId);
                
                // Note the streamId is part of the URL path
                const response = await fetch(`/api/v1/stream/stop/${streamId}`, {
                    method: 'POST'
                });

                const data = await response.json();
                if (!data.success) {
                    throw new Error(data.error?.message || 'Unknown error');
                }

                streamId = null;
                
                // Clear canvas and reset UI
                const ctx = canvas.getContext('2d');
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                streamContainer.classList.add('hidden');
                stopButton.classList.add('hidden');
                startButton.classList.remove('hidden');
                
                fpsCounter.textContent = '0';
                objectsCounter.textContent = '0';
                
                if (DEBUG) console.log('Stream stopped successfully');
                
            } catch (error) {
                showError('Failed to stop stream: ' + error.message);
            }
        }
    });

    // Socket event handlers
    socket.on('connect', () => {
        if (DEBUG) console.log('Connected to server');
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        showError('Connection lost. Please refresh the page.');
    });

    socket.on('frame', (data) => {
        if (DEBUG) console.log('Received frame event:', data);
        // Update FPS counter
        fpsCounter.textContent = data.fps ? data.fps.toFixed(1) : "0";
        
        // Update objects counter
        objectsCounter.textContent = data.detections ? data.detections.length : "0";
        
        // Draw the processed frame
        const img = new Image();
        img.onload = () => {
            // Set canvas dimensions to match image if needed
            if (canvas.width !== img.width || canvas.height !== img.height) {
                canvas.width = img.width;
                canvas.height = img.height;
            }
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
        };
        img.src = data.frame;
        
        console.log("Received frame with dimensions:", img.width, "x", img.height);
    });

    socket.on('error', (error) => {
        showError(error);
    });

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
    }

    // Use both beforeunload and unload for better browser compatibility
    window.addEventListener('beforeunload', () => {
        stopStream();
    });

    window.addEventListener('unload', () => {
        stopStream();
    });

    // Extract stop stream logic to a function for reuse
    function stopStream() {
        if (streamId) {
            if (DEBUG) console.log('Stopping stream on page leave:', streamId);
            
            try {
                // Use the correct URL format with streamId in the path
                navigator.sendBeacon(`/api/v1/stream/stop/${streamId}`, null);
            } catch (error) {
                console.error('Error stopping stream during page unload:', error);
                
                // Fallback to fetch
                try {
                    fetch(`/api/v1/stream/stop/${streamId}`, {
                        method: 'POST',
                        keepalive: true
                    });
                } catch (fetchError) {
                    console.error('Fetch fallback also failed:', fetchError);
                }
            }
        }
    }
}); 