"""
Receipt scanning and OCR functionality.
"""
import os
import cv2
import numpy as np
import pytesseract
from PIL import Image
from typing import Tuple, Optional

class ReceiptScanner:
    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize the receipt scanner.
        
        Args:
            tesseract_path: Path to Tesseract executable (optional)
        """
        # Set Tesseract path if provided
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Create data directories if they don't exist
        os.makedirs("data/receipts", exist_ok=True)
        os.makedirs("data/uploads", exist_ok=True)
    
    def scan_image(self, image_path: str) -> str:
        """
        Scan an image and extract text using OCR.
        
        Args:
            image_path: Path to the receipt image
            
        Returns:
            str: Extracted text from the receipt
        """
        # Read the image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image at {image_path}")
        
        # Preprocess the image
        processed_image = self._preprocess_image(image)
        
        # Perform OCR
        text = pytesseract.image_to_string(processed_image)
        
        # Save a copy of the processed image
        filename = os.path.basename(image_path)
        processed_path = os.path.join("data/receipts", f"processed_{filename}")
        cv2.imwrite(processed_path, processed_image)
        
        return text
    
    def scan_from_camera(self, camera_id: int = 0) -> Tuple[str, str]:
        """
        Capture an image from camera and scan it.
        
        Args:
            camera_id: Camera device ID
            
        Returns:
            Tuple[str, str]: Tuple containing (extracted text, saved image path)
        """
        # Initialize camera
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            raise ValueError(f"Could not open camera with ID {camera_id}")
        
        # Capture frame
        ret, frame = cap.read()
        if not ret:
            cap.release()
            raise ValueError("Failed to capture image from camera")
        
        # Save the captured image
        timestamp = int(cv2.getTickCount())
        image_path = os.path.join("data/receipts", f"receipt_{timestamp}.jpg")
        cv2.imwrite(image_path, frame)
        
        # Release the camera
        cap.release()
        
        # Process the image
        text = self.scan_image(image_path)
        
        return text, image_path
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess the image to improve OCR accuracy.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            np.ndarray: Processed image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 21, 10
        )
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
        
        # Dilation and erosion to remove noise
        kernel = np.ones((1, 1), np.uint8)
        dilated = cv2.dilate(denoised, kernel, iterations=1)
        eroded = cv2.erode(dilated, kernel, iterations=1)
        
        return eroded
