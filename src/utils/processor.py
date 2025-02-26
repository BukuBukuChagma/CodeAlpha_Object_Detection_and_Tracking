import cv2
import logging
from .video_capture import VideoCapture
from .display_utils import FPSCounter, create_side_by_side_display, add_fps_to_frames
from ..detection_and_tracking.detector import YOLODetector

logger = logging.getLogger(__name__)

def process_live_video(detector: YOLODetector, conf_threshold: float = 0.5, 
                      display_width: int = 640, camera_id: int = 1):
    """
    Process live video from webcam.
    
    Args:
        detector: YOLODetector instance
        conf_threshold: Confidence threshold for detections
        display_width: Width of each frame in the display
    """
    fps_counter = FPSCounter()
    
    with VideoCapture(camera_id) as video:
        logger.info("Video capture started")
        process_video_stream(video, detector, fps_counter, conf_threshold, display_width)

def process_video_file(detector: YOLODetector, video_path: str, conf_threshold: float = 0.5,
                      display_width: int = 640):
    """
    Process video file.
    
    Args:
        detector: YOLODetector instance
        video_path: Path to video file
        conf_threshold: Confidence threshold for detections
        display_width: Width of each frame in the display
    """
    fps_counter = FPSCounter()
    
    with VideoCapture(video_path) as video:
        logger.info(f"Processing video: {video_path}")
        process_video_stream(video, detector, fps_counter, conf_threshold, display_width)

def process_video_stream(video, detector: YOLODetector, fps_counter: FPSCounter, 
                        conf_threshold: float = 0.5, display_width: int = 640):
    """
    Common video processing loop for both live and file inputs.
    
    Args:
        video: VideoCapture instance
        detector: YOLODetector instance
        fps_counter: FPSCounter instance
        conf_threshold: Confidence threshold for detections
        display_width: Width of each frame in the display
    """
    while True:
        success, frame = video.read_frame()
        if not success:
            break

        # Get detections and tracks
        results = detector.detect_and_track(frame, conf_threshold)
        
        # Draw results
        frame_with_results = detector.draw_results(frame, results)

        fps = fps_counter.update()
        frame_copy, frame_with_results = add_fps_to_frames(
            frame, frame_with_results, fps)

        display_frame = create_side_by_side_display(
            frame_copy, 
            frame_with_results,
            target_width=display_width
        )
        cv2.imshow('Object Detection & Tracking', display_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

def process_image(detector: YOLODetector, image_path: str, conf_threshold: float = 0.5,
                 display_width: int = 640):
    """
    Process single image.
    
    Args:
        detector: YOLODetector instance
        image_path: Path to image file
        conf_threshold: Confidence threshold for detections
        display_width: Width of each frame in the display
    """
    logger.info(f"Processing image: {image_path}")
    
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image: {image_path}")
            
        results = detector.detect_and_track(image, conf_threshold)
        image_with_results = detector.draw_results(image, results)
        
        display_frame = create_side_by_side_display(
            image, 
            image_with_results,
            target_width=display_width
        )
        cv2.imshow('Object Detection & Tracking', display_frame)
        cv2.waitKey(0)
        
    except Exception as e:
        logger.error(f"Error processing image: {e}") 