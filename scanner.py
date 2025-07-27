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
        
        # Preprocess the image with aggressive cleaning
        processed_image = self._preprocess_image(image)

        # Use a stronger Tesseract configuration for receipts
        tesseract_config = r"--oem 3 --psm 6 -c preserve_interword_spaces=1"
        text = pytesseract.image_to_string(processed_image, config=tesseract_config)
        
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
        # Resize large images to a manageable width while preserving aspect ratio
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        if w > 1000:
            scale = 1000.0 / w
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

        # Attempt to detect and deskew the receipt for a straight top-down view
        deskewed = self._detect_receipt(gray)
        if deskewed is not None:
            gray = deskewed

        # Enhance local contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        # Noise reduction while keeping edges sharp
        gray = cv2.bilateralFilter(gray, 9, 75, 75)

        # Adaptive thresholding for binarisation
        thresh = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY,
            31,
            15,
        )

        # Morphological opening to clean small artefacts
        kernel = np.ones((2, 2), np.uint8)
        processed = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

        return processed

    def _detect_receipt(self, gray: np.ndarray) -> Optional[np.ndarray]:
        """Detect the receipt contour and apply a perspective transform.

        Args:
            gray: Grayscale input image
        Returns:
            Top-down warped image if a 4-point contour is found, otherwise None.
        """
        # Edge detection
        edged = cv2.Canny(gray, 50, 200)
        contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

        for cnt in contours:
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            if len(approx) == 4:
                pts = approx.reshape(4, 2)
                return self._four_point_transform(gray, pts)
        return None

    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """Return points ordered as top-left, top-right, bottom-right, bottom-left."""
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect

    def _four_point_transform(self, image: np.ndarray, pts: np.ndarray) -> np.ndarray:
        """Perform perspective transform given source points."""
        rect = self._order_points(pts)
        (tl, tr, br, bl) = rect
        widthA = np.linalg.norm(br - bl)
        widthB = np.linalg.norm(tr - tl)
        maxWidth = int(max(widthA, widthB))
        heightA = np.linalg.norm(tr - br)
        heightB = np.linalg.norm(tl - bl)
        maxHeight = int(max(heightA, heightB))

        dst = np.array(
            [
                [0, 0],
                [maxWidth - 1, 0],
                [maxWidth - 1, maxHeight - 1],
                [0, maxHeight - 1],
            ],
            dtype="float32",
        )

        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
        return warped
