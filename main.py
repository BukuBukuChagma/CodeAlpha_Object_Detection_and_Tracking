import cv2
import logging
import argparse
from src.detection_and_tracking.detector import YOLODetector
from src.utils.processor import process_live_video, process_video_file, process_image

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Object Detection and Tracking System')
    
    # Input source arguments
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--webcam', action='store_true', help='Use webcam feed')
    group.add_argument('--video', type=str, help='Path to video file')
    group.add_argument('--image', type=str, help='Path to image file')
    
    # Model configuration
    parser.add_argument('--model', type=str, default='yolov8n.pt',
                      choices=['yolov8n.pt', 'yolov8s.pt', 'yolov8m.pt', 'yolov8l.pt', 'yolov8x.pt'],
                      help='YOLO model size to use')
    
    # Tracker configuration
    parser.add_argument('--tracker', type=str, default='bytetrack.yaml',
                      choices=['bytetrack.yaml', 'botsort.yaml'],
                      help='Tracking algorithm to use')
    
    # Detection parameters
    parser.add_argument('--conf', type=float, default=0.5,
                      help='Confidence threshold for detections (0-1)')
    
    # Display parameters
    parser.add_argument('--display-width', type=int, default=640,
                      help='Width of each frame in the display')
    
    args = parser.parse_args()

    try:
        # Initialize detector with specified model and tracker
        detector = YOLODetector(
            model_size=args.model,
            tracker=args.tracker
        )
        
        if args.webcam:
            process_live_video(detector, conf_threshold=args.conf)
        elif args.video:
            process_video_file(detector, args.video, conf_threshold=args.conf)
        elif args.image:
            process_image(detector, args.image, conf_threshold=args.conf)
            
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        cv2.destroyAllWindows()
        logger.info("Application terminated")

if __name__ == "__main__":
    main() 