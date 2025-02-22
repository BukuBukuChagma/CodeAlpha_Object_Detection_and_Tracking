import cv2
import numpy as np
import logging
from typing import Optional, Tuple

class VideoCapture:
    """
    A class to handle video capture operations.
    """
    def __init__(self, source: int = 0):
        """
        Initialize the video capture.
        
        Args:
            source (int): Camera index or video file path. Default is 0 (webcam)
        """
        self.source = source
        self.cap = None
        self.logger = logging.getLogger(__name__)

    def start(self) -> bool:
        """
        Start the video capture.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.cap = cv2.VideoCapture(self.source)
            if not self.cap.isOpened():
                self.logger.error("Failed to open video capture")
                return False
            return True
        except Exception as e:
            self.logger.error(f"Error starting video capture: {str(e)}")
            return False

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read a frame from the video capture.
        
        Returns:
            Tuple[bool, Optional[np.ndarray]]: (success, frame)
        """
        if self.cap is None:
            return False, None
        
        try:
            ret, frame = self.cap.read()
            if not ret:
                self.logger.warning("Failed to read frame")
                return False, None
            return True, frame
        except Exception as e:
            self.logger.error(f"Error reading frame: {str(e)}")
            return False, None

    def release(self):
        """Release the video capture resources."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def __enter__(self):
        """Context manager enter."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release() 