from flask_socketio import SocketIO, emit
from flask import request
from .config import app  # Import from config instead
import cv2
import base64
import logging
import time
from threading import Thread, Event
from typing import Dict
import numpy as np

from ..detection_and_tracking.detector import YOLODetector
from .utils import FileHandler

logger = logging.getLogger(__name__)
socketio = SocketIO()

class WebcamStream:
    """Handle webcam streaming and processing."""
    
    def __init__(self, stream_id: str, detector: YOLODetector, 
                 conf_threshold: float = 0.5,
                 frame_rate: int = 30):
        self.stream_id = stream_id
        self.detector = detector
        self.conf_threshold = conf_threshold
        self.frame_rate = frame_rate if not app.config['TESTING'] else 2
        self.cap = None
        self.thread = None
        self.stop_event = Event()
        self.latest_detections = []  # Store latest detections
        
    def start(self):
        """Start the streaming thread."""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise ValueError("Could not open webcam")
            
        self.thread = Thread(target=self._stream_thread)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        """Stop the streaming thread."""
        try:
            self.stop_event.set()
            if self.thread:
                self.thread.join(timeout=1)
            if self.cap:
                self.cap.release()
        except Exception as e:
            logger.error(f"Error stopping stream: {e}")
            
    def _stream_thread(self):
        """Thread function for streaming."""
        while not self.stop_event.is_set():
            success, frame = self.cap.read()
            if not success:
                break
                
            # Process frame
            results = self.detector.detect_and_track(frame, self.conf_threshold)
            self.latest_detections = results  # Update latest detections
            processed_frame = self.detector.draw_results(frame, results)
            
            # Convert frame to base64
            _, buffer = cv2.imencode('.jpg', processed_frame)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Emit frame and detections
            socketio.emit('frame', {
                'stream_id': self.stream_id,
                'frame': frame_base64,
                'detections': results,
                'timestamp': time.time()
            }, namespace='/stream')
            
            # Control frame rate
            time.sleep(1/self.frame_rate)

# Store active streams
active_streams: Dict[str, WebcamStream] = {}

@socketio.on_error_default
def default_error_handler(e):
    """Handle all namespaced errors."""
    logger.error(f"SocketIO error: {str(e)}", exc_info=True)
    return False

@socketio.on('connect', namespace='/stream')
def handle_connect():
    """Handle client connection."""
    try:
        logger.info('Client attempting to connect')
        # Log connection details
        sid = request.sid if hasattr(request, 'sid') else 'unknown'
        logger.info(f'Client SID: {sid}')
        
        # Try to emit and verify connection
        emit('connect', {
            'status': 'connected',
            'timestamp': time.time()
        })
        logger.info('Connection response sent')
        return True
        
    except Exception as e:
        logger.error(f"Error in connect handler: {str(e)}", exc_info=True)
        return False

@socketio.on('disconnect', namespace='/stream')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info('Client disconnected')

@socketio.on('get_detections', namespace='/stream')
def handle_get_detections(data):
    """Handle request for current detections."""
    try:
        stream_id = data.get('stream_id')
        if not stream_id or stream_id not in active_streams:
            raise ValueError(f"Invalid stream ID: {stream_id}")
            
        # Get the latest detections from the stream
        stream = active_streams[stream_id]
        
        emit('detections', {
            'stream_id': stream_id,
            'detections': stream.latest_detections if hasattr(stream, 'latest_detections') else [],
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"Error getting detections: {str(e)}")
        emit('error', {
            'code': 'detection_error',
            'message': str(e)
        })

@socketio.on_error_default
def default_error_handler(e):
    """Handle all namespaced errors."""
    logger.error(f"SocketIO error: {str(e)}", exc_info=True)
    return False 