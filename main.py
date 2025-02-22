import cv2
import logging
import argparse
from src.detection.detector import YOLODetector
from src.utils.processor import process_live_video, process_video_file, process_image

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Object Detection System')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--webcam', action='store_true', help='Use webcam feed')
    group.add_argument('--video', type=str, help='Path to video file')
    group.add_argument('--image', type=str, help='Path to image file')
    
    args = parser.parse_args()

    try:
        detector = YOLODetector()
        
        if args.webcam:
            process_live_video(detector)
        elif args.video:
            process_video_file(detector, args.video)
        elif args.image:
            process_image(detector, args.image)
            
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        cv2.destroyAllWindows()
        logger.info("Application terminated")

if __name__ == "__main__":
    main() 