import cv2
import logging
import numpy as np
from src.utils.video_capture import VideoCapture
from src.detection.detector import YOLODetector

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_side_by_side_display(frame1: np.ndarray, frame2: np.ndarray) -> np.ndarray:
    """Create a side by side display of two frames."""
    return np.hstack((frame1, frame2))

def main():
    # Initialize detector
    try:
        detector = YOLODetector()
    except Exception as e:
        logger.error(f"Failed to initialize detector: {str(e)}")
        return

    with VideoCapture(0) as video:
        logger.info("Video capture started")
        
        while True:
            success, frame = video.read_frame()
            if not success:
                logger.error("Failed to read frame")
                break

            # Run detection
            detections = detector.detect(frame)
            
            # Draw detections
            frame_with_detections = detector.draw_detections(frame, detections)

            # Create side by side display
            # Ensure both frames are the same size
            display_frame = create_side_by_side_display(frame, frame_with_detections)

            # Display both frames
            cv2.imshow('Original vs Detection', display_frame)

            # Add labels to indicate which is which
            height = 30
            width = frame.shape[1]  # width of one frame
            label_frame = np.zeros((height, width * 2, 3), dtype=np.uint8)
            
            # Add "Original" label
            cv2.putText(label_frame, "Original", (width//4, 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Add "Detection" label
            cv2.putText(label_frame, "Detection", (width + width//4, 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Display labels
            cv2.imshow('Labels', label_frame)

            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cv2.destroyAllWindows()
    logger.info("Application terminated")

if __name__ == "__main__":
    main() 