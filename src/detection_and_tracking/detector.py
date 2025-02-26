from ultralytics import YOLO
import numpy as np
import cv2
import logging
import os
import shutil
from typing import List, Tuple, Dict, Optional, Union
from pathlib import Path
from collections import deque

class TrajectoryManager:
    """Manages object trajectories with fading effect."""
    def __init__(self, max_points: int = 30, fade_steps: int = 10):
        self.trajectories = {}  # track_id -> deque of points
        self.max_points = max_points
        self.fade_steps = fade_steps
    
    def update(self, track_id: int, center_point: tuple):
        """Update trajectory for a tracked object."""
        if track_id not in self.trajectories:
            self.trajectories[track_id] = deque(maxlen=self.max_points)
        self.trajectories[track_id].append(center_point)
    
    def draw_trajectories(self, frame: np.ndarray, active_track_ids: set):
        """Draw trajectories with fading effect."""
        # Remove trajectories of objects that are no longer tracked
        current_ids = set(self.trajectories.keys())
        for track_id in current_ids - active_track_ids:
            del self.trajectories[track_id]
        
        # Draw active trajectories
        for track_id in active_track_ids:
            if track_id not in self.trajectories:
                continue
                
            points = list(self.trajectories[track_id])
            if len(points) < 2:
                continue
            
            # Draw lines with fading effect
            for i in range(len(points) - 1):
                # Calculate alpha based on point age
                alpha = (i + 1) / len(points)  # Newer points are more opaque
                color = (0, 0, 255)  # Red color for trajectory
                
                # Draw line segment with calculated alpha
                cv2.line(frame,
                        (int(points[i][0]), int(points[i][1])),
                        (int(points[i+1][0]), int(points[i+1][1])),
                        color,
                        thickness=2,
                        lineType=cv2.LINE_AA)

class YOLODetector:
    """
    A class to handle object detection and tracking using YOLOv8.
    """
    def __init__(self, model_size: str = "yolov8n.pt", tracker: str = "bytetrack.yaml", 
                 trajectory_length: int = 30, fade_steps: int = 10, 
                 conf_threshold: float = 0.5, display_width: int = 640):
        """
        Initialize the YOLO detector.
        
        Args:
            model_size (str): Size of YOLO model to use.
                            Options: yolov8n.pt, yolov8s.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt
                            Default is "yolov8n.pt" (smallest and fastest)
            tracker (str): Tracker configuration file. Options: "bytetrack.yaml", "botsort.yaml"
            trajectory_length (int): Maximum number of points in trajectory
            fade_steps (int): Number of steps for trajectory fade effect
            conf_threshold (float): Confidence threshold for detections
            display_width (int): Width of the display window
        """
        self.logger = logging.getLogger(__name__)
        self.model_name = model_size
        self.tracker = tracker
        self.conf_threshold = conf_threshold
        self.display_width = display_width
        
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

        # Initialize trajectory manager with specified parameters
        self.trajectory_manager = TrajectoryManager(
            max_points=trajectory_length,
            fade_steps=fade_steps
        )

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
                tracker=self.tracker,
                verbose = False
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
        """Draw detection and tracking results with trajectories on the frame."""
        draw_frame = frame.copy()
        
        # Keep track of active track IDs
        active_track_ids = set()
        
        for obj in results:
            bbox = obj['bbox']
            track_id = obj.get('track_id')
            
            if track_id is not None:
                active_track_ids.add(track_id)
                # Calculate center point of bbox
                center_x = (bbox[0] + bbox[2]) // 2
                center_y = (bbox[1] + bbox[3]) // 2
                # Update trajectory
                self.trajectory_manager.update(track_id, (center_x, center_y))
            
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
        
        # Draw trajectories
        self.trajectory_manager.draw_trajectories(draw_frame, active_track_ids)
            
        return draw_frame 