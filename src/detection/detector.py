from ultralytics import YOLO
import numpy as np
import cv2
import logging
import os
import shutil
from typing import List, Tuple, Dict, Optional
from pathlib import Path

class YOLODetector:
    """
    A class to handle object detection using YOLOv8.
    """
    def __init__(self, model_size: str = "yolov8n.pt"):
        """
        Initialize the YOLO detector.
        
        Args:
            model_size (str): Size of YOLO model to use.
                            Options: yolov8n.pt, yolov8s.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt
                            Default is "yolov8n.pt" (smallest and fastest)
        """
        self.logger = logging.getLogger(__name__)
        
        # Setup weights directory
        self.weights_dir = Path("yolo/weights")
        self.weights_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if model exists in weights directory
        model_path = self.weights_dir / model_size
        if not model_path.exists():
            self.logger.info(f"Model not found in {self.weights_dir}. Downloading...")
            # Download model to base directory first
            temp_model = YOLO(model_size)
            # Move the downloaded file to our weights directory
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

    def detect(self, frame: np.ndarray, conf_threshold: float = 0.5) -> List[Dict]:
        """
        Detect objects in a frame.
        
        Args:
            frame (np.ndarray): Input frame
            conf_threshold (float): Confidence threshold for detections
            
        Returns:
            List[Dict]: List of detections, each containing:
                       - bbox (List[float]): [x1, y1, x2, y2]
                       - confidence (float): Detection confidence
                       - class_id (int): Class ID
                       - class_name (str): Class name
        """
        try:
            # Run inference
            results = self.model(frame, conf=conf_threshold)[0]
            
            # Process results
            detections = []
            for box in results.boxes:
                # Get box coordinates, confidence and class
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = results.names[class_id]
                
                detections.append({
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'confidence': confidence,
                    'class_id': class_id,
                    'class_name': class_name
                })
            
            return detections
            
        except Exception as e:
            self.logger.error(f"Error during detection: {str(e)}")
            return []

    def draw_detections(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        Draw detection boxes and labels on the frame.
        
        Args:
            frame (np.ndarray): Input frame
            detections (List[Dict]): List of detections from detect()
            
        Returns:
            np.ndarray: Frame with drawn detections
        """
        draw_frame = frame.copy()
        
        for det in detections:
            bbox = det['bbox']
            label = f"{det['class_name']} {det['confidence']:.2f}"
            
            # Draw box
            cv2.rectangle(draw_frame, 
                         (bbox[0], bbox[1]), 
                         (bbox[2], bbox[3]), 
                         (0, 255, 0), 2)
            
            # Draw label
            cv2.putText(draw_frame, label, 
                       (bbox[0], bbox[1] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                       (0, 255, 0), 2)
            
        return draw_frame 