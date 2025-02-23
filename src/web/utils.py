import os
from pathlib import Path
import uuid
from werkzeug.utils import secure_filename
import cv2
import base64
import numpy as np
from typing import Tuple, Optional
import shutil

class FileHandler:
    """Handle file uploads and temporary storage."""
    
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
    
    def __init__(self):
        self.upload_folder = Path(__file__).parent / 'static/uploads'
        self.results_folder = Path(__file__).parent / 'static/results'
        self.upload_folder.mkdir(parents=True, exist_ok=True)
        self.results_folder.mkdir(parents=True, exist_ok=True)
    
    def save_upload(self, file, prefix: str = '') -> Tuple[str, str]:
        """Save uploaded file and return paths."""
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{prefix}_{uuid.uuid4().hex}.{ext}"
        
        upload_path = self.upload_folder / unique_filename
        file.save(str(upload_path))
        
        return str(upload_path), unique_filename
    
    def save_result(self, image: np.ndarray, original_filename: str) -> str:
        """Save processed image and return URL."""
        filename = f"result_{original_filename}"
        result_path = self.results_folder / filename
        cv2.imwrite(str(result_path), image)
        
        return f"/static/results/{filename}"

    @staticmethod
    def is_allowed_image(filename: str) -> bool:
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in FileHandler.ALLOWED_IMAGE_EXTENSIONS 

    @staticmethod
    def is_allowed_video(filename: str) -> bool:
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in FileHandler.ALLOWED_VIDEO_EXTENSIONS

    def save_video_result(self, output_path: str, original_filename: str) -> str:
        """Save processed video and return URL."""
        filename = f"result_{original_filename}"
        result_path = self.results_folder / filename
        
        # Move the processed video to results folder
        shutil.move(output_path, str(result_path))
        
        return f"/static/results/{filename}" 