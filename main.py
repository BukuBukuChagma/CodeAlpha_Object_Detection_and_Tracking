import cv2
import logging
import numpy as np
import time
from src.utils.video_capture import VideoCapture
from src.detection.detector import YOLODetector

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_side_by_side_display(frame1: np.ndarray, frame2: np.ndarray, labels: bool = True) -> np.ndarray:
    """Create a side by side display of two frames with optional labels."""
    # Create the side-by-side display
    display = np.hstack((frame1, frame2))
    
    if labels:
        # Add black strip at the top for labels
        height = 30
        label_strip = np.zeros((height, display.shape[1], 3), dtype=np.uint8)
        display = np.vstack((label_strip, display))
        
        # Add labels
        width = frame1.shape[1]
        cv2.putText(display, "Original", (width//4, 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display, "Detection", (width + width//4, 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    return display

class FPSCounter:
    """Simple FPS counter"""
    def __init__(self, avg_frames: int = 30):
        self.avg_frames = avg_frames
        self.times = []
        
    def update(self) -> float:
        self.times.append(time.time())
        if len(self.times) > self.avg_frames:
            self.times.pop(0)
        
        if len(self.times) > 1:
            return len(self.times) / (self.times[-1] - self.times[0])
        return 0.0

def main():
    # Initialize detector
    try:
        detector = YOLODetector()
    except Exception as e:
        logger.error(f"Failed to initialize detector: {str(e)}")
        return

    fps_counter = FPSCounter()
    
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

            # Update and draw FPS
            fps = fps_counter.update()
            fps_text = f"FPS: {fps:.1f}"
            
            # Add FPS to both frames
            frame_copy = frame.copy()
            cv2.putText(frame_copy, fps_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame_with_detections, fps_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Create side by side display with integrated labels
            display_frame = create_side_by_side_display(frame_copy, frame_with_detections)

            # Display the frame
            cv2.imshow('Object Detection', display_frame)

            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cv2.destroyAllWindows()
    logger.info("Application terminated")

if __name__ == "__main__":
    main() 