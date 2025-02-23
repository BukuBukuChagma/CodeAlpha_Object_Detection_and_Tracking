from celery import Celery
import cv2
import os
from pathlib import Path
import time
from typing import Dict
import logging

from ..detection_and_tracking.detector import YOLODetector
from .utils import FileHandler

# Configure Celery
celery = Celery('tasks', broker='redis://localhost:6379/0')
celery.conf.update(
    result_backend='redis://localhost:6379/0',  # Redis stores task results
    task_track_started=True
)

logger = logging.getLogger(__name__)

@celery.task(bind=True)
def process_video(self, file_path: str, conf_threshold: float = 0.5,
                 display_width: int = 640, save_output: bool = True) -> Dict:
    """Process video file in background."""
    cap = None
    out = None
    try:
        detector = YOLODetector()
        file_handler = FileHandler()
        
        # Open video
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            raise ValueError("Could not open video file")
            
        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Create output video writer if needed
        output_path = None
        if save_output:
            output_path = str(Path(file_path).parent / f"output_{Path(file_path).name}")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        start_time = time.time()
        
        while True:
            success, frame = cap.read()
            if not success:
                break
                
            # Process frame
            results = detector.detect_and_track(frame, conf_threshold)
            processed_frame = detector.draw_results(frame, results)
            
            # Save frame if output is requested
            if out is not None:
                out.write(processed_frame)
            
            # Update progress
            frame_count += 1
            progress = (frame_count / total_frames) * 100
            self.update_state(
                state='PROGRESS',
                meta={'progress': progress}
            )
        
        # Clean up
        cap.release()
        if out is not None:
            out.write(processed_frame)
            out.release()
        
        processing_time = time.time() - start_time
        
        # Save result video if output was created
        result_url = None
        if output_path:
            result_url = file_handler.save_video_result(
                output_path,
                Path(file_path).name
            )
        
        return {
            'status': 'completed',
            'processing_time': processing_time,
            'frames_processed': frame_count,
            'output_video_url': result_url
        }
        
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        raise
    finally:
        # Ensure resources are released
        if cap is not None:
            cap.release()
        if out is not None:
            out.release()
        cv2.destroyAllWindows() 