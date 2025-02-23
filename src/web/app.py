from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import logging
import time
from pathlib import Path
import cv2

from .utils import FileHandler
from ..detection_and_tracking.detector import YOLODetector
from .tasks import process_video, celery

app = Flask(__name__, 
           static_folder='static',  # Set static folder
           static_url_path='/static')  # Set URL path for static files
CORS(app)  # Enable CORS for all domains

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
file_handler = FileHandler()
detector = YOLODetector()

# Basic error handler
@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"An error occurred: {str(error)}")
    return jsonify({
        "success": False,
        "error": {
            "code": "internal_error",
            "message": str(error)
        }
    }), 500

# Health check endpoint
@app.route('/api/v1/health', methods=['GET'])
def health_check():
    return jsonify({
        "success": True,
        "data": {
            "status": "healthy"
        }
    })

@app.route('/api/v1/detect/image', methods=['POST'])
def process_image():
    """Process uploaded image and return detections."""
    try:
        # Validate file exists
        if 'image' not in request.files:
            return jsonify({
                "success": False,
                "error": {
                    "code": "missing_file",
                    "message": "No image file provided"
                }
            }), 400
        
        file = request.files['image']
        
        # Validate filename
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": {
                    "code": "invalid_file",
                    "message": "No selected file"
                }
            }), 400
            
        # Validate file type
        if not file_handler.is_allowed_image(file.filename):
            return jsonify({
                "success": False,
                "error": {
                    "code": "invalid_file_type",
                    "message": "File type not supported"
                }
            }), 400
            
        # Get parameters
        conf_threshold = float(request.form.get('conf_threshold', 0.5))
        display_width = int(request.form.get('display_width', 640))
        
        # Save uploaded file
        start_time = time.time()
        file_path, filename = file_handler.save_upload(file, prefix='img')
        
        # Read and process image
        image = cv2.imread(file_path)
        if image is None:
            raise ValueError("Could not read uploaded image")
            
        # Detect objects
        results = detector.detect_and_track(image, conf_threshold)
        
        # Draw results and save
        image_with_results = detector.draw_results(image, results)
        result_url = file_handler.save_result(image_with_results, filename)
        
        processing_time = time.time() - start_time
        
        return jsonify({
            "success": True,
            "data": {
                "detections": results,
                "processed_image_url": result_url,
                "processing_time": processing_time
            }
        })
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "processing_error",
                "message": str(e)
            }
        }), 500

@app.route('/api/v1/detect/video', methods=['POST'])
def process_video_file():
    """Process uploaded video file."""
    try:
        # Validate file exists
        if 'video' not in request.files:
            return jsonify({
                "success": False,
                "error": {
                    "code": "missing_file",
                    "message": "No video file provided"
                }
            }), 400
        
        file = request.files['video']
        
        # Validate filename
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": {
                    "code": "invalid_file",
                    "message": "No selected file"
                }
            }), 400
            
        # Validate file type
        if not file_handler.is_allowed_video(file.filename):
            return jsonify({
                "success": False,
                "error": {
                    "code": "invalid_file_type",
                    "message": "File type not supported"
                }
            }), 400
            
        # Get parameters
        conf_threshold = float(request.form.get('conf_threshold', 0.5))
        display_width = int(request.form.get('display_width', 640))
        save_output = request.form.get('save_output', 'true').lower() == 'true'
        
        # Save uploaded file
        file_path, filename = file_handler.save_upload(file, prefix='video')
        
        # Start processing task
        task = process_video.delay(
            file_path,
            conf_threshold=conf_threshold,
            display_width=display_width,
            save_output=save_output
        )
        
        return jsonify({
            "success": True,
            "data": {
                "task_id": task.id,
                "status": "processing"
            }
        })
        
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "processing_error",
                "message": str(e)
            }
        }), 500

@app.route('/api/v1/detect/video/status/<task_id>', methods=['GET'])
def get_video_status(task_id):
    """Get status of video processing task."""
    try:
        task = process_video.AsyncResult(task_id)
        
        # Get task metadata
        meta = task.backend.get_task_meta(task_id)
        # Check if task exists by looking at metadata
        # If task doesn't exist, meta will have status 'PENDING' and no result
        if meta['status'] == 'PENDING' and not meta.get('result'):
            raise ValueError(f"Task with ID {task_id} not found")
        
        if task.state == 'PENDING':
            response = {
                'status': 'pending',
                'progress': 0
            }
        elif task.state == 'PROGRESS':
            response = {
                'status': 'processing',
                'progress': task.info.get('progress', 0)
            }
        elif task.state == 'SUCCESS':
            response = {
                'status': 'completed',
                'progress': 100,
                'result': task.get()
            }
        else:
            response = {
                'status': 'failed',
                'error': str(task.info)
            }
            
        return jsonify({
            "success": True,
            "data": response
        })
        
    except Exception as e:
        logger.error(f"Error getting video status: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "status_error",
                "message": str(e)
            }
        }), 500

if __name__ == '__main__':
    app.run(debug=True) 