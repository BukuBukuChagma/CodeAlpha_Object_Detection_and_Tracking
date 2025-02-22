import cv2
import numpy as np
import time
from typing import Tuple

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

def create_side_by_side_display(frame1: np.ndarray, frame2: np.ndarray, labels: bool = True) -> np.ndarray:
    """Create a side by side display of two frames with optional labels."""
    display = np.hstack((frame1, frame2))
    
    if labels:
        height = 30
        label_strip = np.zeros((height, display.shape[1], 3), dtype=np.uint8)
        display = np.vstack((label_strip, display))
        
        width = frame1.shape[1]
        cv2.putText(display, "Original", (width//4, 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display, "Detection", (width + width//4, 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    return display

def add_fps_to_frames(frame1: np.ndarray, frame2: np.ndarray, fps: float) -> Tuple[np.ndarray, np.ndarray]:
    """Add FPS counter to both frames."""
    frame1_copy = frame1.copy()
    fps_text = f"FPS: {fps:.1f}"
    
    cv2.putText(frame1_copy, fps_text, (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame2, fps_text, (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    return frame1_copy, frame2 