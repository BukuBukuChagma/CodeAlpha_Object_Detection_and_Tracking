import cv2
import logging
from .video_capture import VideoCapture
from .display_utils import FPSCounter, create_side_by_side_display, add_fps_to_frames
from ..detection.detector import YOLODetector

logger = logging.getLogger(__name__)

def process_live_video(detector: YOLODetector):
    """Process live video from webcam."""
    fps_counter = FPSCounter()
    
    with VideoCapture(0) as video:
        logger.info("Video capture started")
        process_video_stream(video, detector, fps_counter)

def process_video_file(detector: YOLODetector, video_path: str):
    """Process video file."""
    fps_counter = FPSCounter()
    
    with VideoCapture(video_path) as video:
        logger.info(f"Processing video: {video_path}")
        process_video_stream(video, detector, fps_counter)

def process_video_stream(video, detector: YOLODetector, fps_counter: FPSCounter):
    """Common video processing loop for both live and file inputs."""
    while True:
        success, frame = video.read_frame()
        if not success:
            break

        detections = detector.detect(frame)
        frame_with_detections = detector.draw_detections(frame, detections)

        fps = fps_counter.update()
        frame_copy, frame_with_detections = add_fps_to_frames(
            frame, frame_with_detections, fps)

        display_frame = create_side_by_side_display(frame_copy, frame_with_detections)
        cv2.imshow('Object Detection', display_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

def process_image(detector: YOLODetector, image_path: str):
    """Process single image."""
    logger.info(f"Processing image: {image_path}")
    
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image: {image_path}")
            
        detections = detector.detect(image)
        image_with_detections = detector.draw_detections(image, detections)
        
        display_frame = create_side_by_side_display(image, image_with_detections)
        cv2.imshow('Object Detection', display_frame)
        cv2.waitKey(0)
        
    except Exception as e:
        logger.error(f"Error processing image: {e}") 