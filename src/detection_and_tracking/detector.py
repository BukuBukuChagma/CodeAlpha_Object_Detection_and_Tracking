from ultralytics import YOLO
import numpy as np
import cv2
import logging
import os
import shutil
from typing import List, Tuple, Dict, Optional, Union
from pathlib import Path

class YOLODetector:
    """
    A class to handle object detection and tracking using YOLOv8.
    """
    def __init__(self, model_size: str = "yolov8n.pt", tracker: str = "bytetrack.yaml"):
        """
        Initialize the YOLO detector.
        
        Args:
            model_size (str): Size of YOLO model to use.
                            Options: yolov8n.pt, yolov8s.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt
                            Default is "yolov8n.pt" (smallest and fastest)
            tracker (str): Tracker configuration file. Options: "bytetrack.yaml", "botsort.yaml"
        """
        self.logger = logging.getLogger(__name__)
        self.tracker = tracker
        
        # Setup weights directory
        self.weights_dir = Path("yolo/weights")
        self.weights_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if model exists in weights directory
        model_path = self.weights_dir / model_size
        if not model_path.exists():
            self.logger.info(f"Model not found in {self.weights_dir}. Downloading...")
            temp_model = YOLO(model_size)
            downloaded_path = Path(model_size)
            if downloaded_path.exists():
                shutil.move(str(downloaded_path), str(model_path))
                self.logger.info(f"Model saved to {model_path}")
            else:
                raise FileNotFoundError(f"Downloaded model not found at {downloaded_path}")
        
        try:
            self.model = YOLO(str(model_path))
            self.logger.info(f"Loaded YOLO model from: {model_path}")
        except Exception as e:
            self.logger.error(f"Error loading YOLO model: {str(e)}")
            raise

    def detect_and_track(self, frame: np.ndarray, conf_threshold: float = 0.5) -> List[Dict]:
        """
        Detect and track objects in a frame using YOLO's built-in tracking.
        
        Args:
            frame (np.ndarray): Input frame
            conf_threshold (float): Confidence threshold for detections
            
        Returns:
            List[Dict]: List of tracked objects with bounding boxes and IDs
        """
        try:
            # Run tracking
            results = self.model.track(
                source=frame, 
                conf=conf_threshold,
                persist=True,  # Persist tracks between frames
                tracker=self.tracker
            )[0]
            
            # Process results
            tracked_objects = []
            if results.boxes is not None and len(results.boxes):
                for box in results.boxes:
                    # Get box coordinates, confidence, class and track ID
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = results.names[class_id]
                    track_id = int(box.id[0]) if box.id is not None else None
                    
                    tracked_objects.append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': confidence,
                        'class_id': class_id,
                        'class_name': class_name,
                        'track_id': track_id
                    })
            
            return tracked_objects
            
        except Exception as e:
            self.logger.error(f"Error during tracking: {str(e)}")
            return []

    def draw_results(self, frame: np.ndarray, results: List[Dict]) -> np.ndarray:
        """Draw detection and tracking results on the frame."""
        draw_frame = frame.copy()
        
        for obj in results:
            bbox = obj['bbox']
            track_id = obj.get('track_id')
            
            # Different colors for tracked vs untracked objects
            color = (0, 0, 255) if track_id is not None else (0, 255, 0)
            
            # Create label with class, confidence and track ID if available
            label_parts = [
                f"{obj['class_name']} {obj['confidence']:.2f}"
            ]
            if track_id is not None:
                label_parts.append(f"ID:{track_id}")
            label = " ".join(label_parts)
            
            # Draw box
            cv2.rectangle(draw_frame, 
                         (bbox[0], bbox[1]), 
                         (bbox[2], bbox[3]), 
                         color, 2)
            
            # Draw label
            cv2.putText(draw_frame, label, 
                       (bbox[0], bbox[1] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                       color, 2)
            
        return draw_frame 