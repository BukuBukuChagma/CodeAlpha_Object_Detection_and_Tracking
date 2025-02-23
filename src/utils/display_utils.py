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

def resize_with_aspect_ratio(image: np.ndarray, target_width: int = 640) -> np.ndarray:
    """
    Resize image maintaining aspect ratio.
    
    Args:
        image: Input image
        target_width: Desired width
    
    Returns:
        Resized image
    """
    height, width = image.shape[:2]
    
    # Calculate scaling factor based on target width
    scale = target_width / float(width)
    target_height = int(height * scale)
    
    # Resize the image
    resized = cv2.resize(image, (target_width, target_height), 
                        interpolation=cv2.INTER_AREA)
    
    return resized

def create_side_by_side_display(frame1: np.ndarray, frame2: np.ndarray, labels: bool = True, 
                              target_width: int = 640) -> np.ndarray:
    """
    Create a side by side display of two frames with optional labels.
    
    Args:
        frame1: First frame
        frame2: Second frame
        labels: Whether to add labels
        target_width: Width for each frame in the display
    """
    # Get original dimensions
    h1, w1 = frame1.shape[:2]
    h2, w2 = frame2.shape[:2]
    
    # Calculate scaling to maintain aspect ratio
    scale = target_width / float(max(w1, w2))
    new_width = int(target_width)
    new_height = int(max(h1, h2) * scale)
    
    # Resize both frames
    frame1_resized = cv2.resize(frame1, (new_width, new_height), interpolation=cv2.INTER_AREA)
    frame2_resized = cv2.resize(frame2, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    # Create side-by-side display
    display = np.hstack((frame1_resized, frame2_resized))
    
    if labels:
        # Add black strip at the top for labels
        height = 30
        label_strip = np.zeros((height, display.shape[1], 3), dtype=np.uint8)
        display = np.vstack((label_strip, display))
        
        # Add labels
        cv2.putText(display, "Original", (new_width//4, 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display, "Detection", (new_width + new_width//4, 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    return display

def add_fps_to_frames(frame1: np.ndarray, frame2: np.ndarray, fps: float) -> Tuple[np.ndarray, np.ndarray]:
    """Add FPS counter to both frames."""
    frame1_copy = frame1.copy()
    fps_text = f"FPS: {fps:.1f}"
    
    # Calculate text size and position
    font_scale = min(frame1.shape[1], frame2.shape[1]) / 500.0  # Adjust scale based on frame width
    thickness = max(1, int(font_scale * 2))
    
    # Add FPS text to both frames
    cv2.putText(frame1_copy, fps_text, (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 0), thickness)
    cv2.putText(frame2, fps_text, (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 0), thickness)
    
    return frame1_copy, frame2 