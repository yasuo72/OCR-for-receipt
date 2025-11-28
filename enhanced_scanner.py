"""
Enhanced Receipt Scanner with Advanced OCR and AI-powered text extraction.
Supports multiple OCR engines, advanced preprocessing, and intelligent parsing.
"""
import os
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import re
from typing import Dict, List, Any, Tuple, Optional, Union
import logging
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OCRResult:
    """Container for OCR results with confidence scores."""
    text: str
    confidence: float
    method: str
    bounding_boxes: List[Tuple[int, int, int, int]] = None

@dataclass
class ExtractedData:
    """Container for extracted receipt data."""
    merchant: str = None
    date: str = None
    total: float = None
    subtotal: float = None
    tax: float = None
    items: List[Dict[str, Any]] = None
    payment_method: str = None
    receipt_number: str = None
    confidence_score: float = 0.0
    raw_text: str = ""

class EnhancedReceiptScanner:
    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize the enhanced receipt scanner with multiple OCR engines.
        
        Args:
            tesseract_path: Path to Tesseract executable (optional)
        """
        # Set Tesseract path if provided
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Initialize EasyOCR reader (supports multiple languages) if available
        try:
            import easyocr
            self.easyocr_reader = easyocr.Reader(['en', 'hi'], gpu=False)
            self.easyocr_available = True
            logger.info("EasyOCR initialized successfully")
        except Exception as e:
            logger.warning(f"EasyOCR not available: {e}")
            self.easyocr_available = False
        
        # Create data directories
        os.makedirs("data/receipts", exist_ok=True)
        os.makedirs("data/uploads", exist_ok=True)
        os.makedirs("data/processed", exist_ok=True)
        
        # Tesseract configurations for different scenarios
        self.tesseract_configs = {
            'default': r'--oem 3 --psm 6 -c preserve_interword_spaces=1',
            'single_column': r'--oem 3 --psm 4 -c preserve_interword_spaces=1',
            'sparse_text': r'--oem 3 --psm 8 -c preserve_interword_spaces=1',
            'single_word': r'--oem 3 --psm 8',
            'digits_only': r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789.,',
            'receipt_optimized': r'--oem 3 --psm 6 -c preserve_interword_spaces=1 -c tessedit_create_hocr=1'
        }

    def scan_receipt(self, image_path: str, save_processed: bool = True, fast_mode: bool = False) -> ExtractedData:
        """
        Enhanced receipt scanning with multiple OCR engines and intelligent parsing.
        
        Args:
            image_path: Path to the receipt image
            save_processed: Whether to save processed images for debugging
            
        Returns:
            ExtractedData: Structured receipt data
        """
        logger.info(f"Starting enhanced scan of: {image_path}")
        
        # Read and validate image with EXIF-aware orientation handling
        try:
            pil_image = Image.open(image_path)
            pil_image = ImageOps.exif_transpose(pil_image)
            image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        except Exception as e:
            logger.warning(f"PIL/EXIF load failed, falling back to cv2.imread: {e}")
            image = cv2.imread(image_path)
        
        if image is None:
            raise ValueError(f"Could not read image at {image_path}")
        
        # Light central cropping to reduce background noise while keeping full receipt
        try:
            h, w = image.shape[:2]
            if h > 0 and w > 0:
                top = int(0.05 * h)
                bottom = int(0.95 * h)
                left = int(0.10 * w)
                right = int(0.90 * w)
                image = image[top:bottom, left:right]
        except Exception as e:
            logger.warning(f"Image cropping failed, using original image: {e}")
        
        # Apply preprocessing
        if fast_mode:
            # In fast mode, compute a small set of high-value variants
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            processed_images = {
                'standard': self._standard_preprocessing(gray),
                'adaptive': self._adaptive_preprocessing(gray),
            }
            # Also try perspective-corrected versions to better isolate the receipt region
            perspective = self._perspective_correction(gray)
            if perspective is not None:
                processed_images['perspective_standard'] = self._standard_preprocessing(perspective)
                processed_images['perspective_adaptive'] = self._adaptive_preprocessing(perspective)
        else:
            # Full advanced preprocessing for maximum robustness
            processed_images = self._advanced_preprocessing(image)
        
        # Extract text using multiple OCR engines
        ocr_results = []
        
        # Use Tesseract with different configurations
        config_items = self.tesseract_configs.items()
        if fast_mode:
            # In fast mode, use only the most relevant receipt-optimized config
            preferred_configs = ['receipt_optimized']
            config_items = [
                (name, self.tesseract_configs[name])
                for name in preferred_configs
                if name in self.tesseract_configs
            ]
        
        for config_name, config in config_items:
            for proc_name, proc_image in processed_images.items():
                try:
                    text = pytesseract.image_to_string(proc_image, config=config)
                    # Use Tesseract's detailed confidence calculation even in fast mode;
                    # fast mode is already limited in configs/preprocessing, so this stays performant.
                    confidence = self._calculate_tesseract_confidence(proc_image, config)
                    ocr_results.append(OCRResult(
                        text=text,
                        confidence=confidence,
                        method=f"tesseract_{config_name}_{proc_name}"
                    ))
                except Exception as e:
                    logger.warning(f"Tesseract {config_name} failed on {proc_name}: {e}")
        
        # Use EasyOCR if available
        if self.easyocr_available:
            try:
                if fast_mode:
                    # In fast mode, run EasyOCR once on a representative variant (prefer standard)
                    if 'standard' in processed_images:
                        proc_name = 'standard'
                        proc_image = processed_images['standard']
                    else:
                        # Fallback to the first available variant
                        proc_name, proc_image = next(iter(processed_images.items()))
                    results = self.easyocr_reader.readtext(proc_image)
                    text = ' '.join([result[1] for result in results])
                    confidence = np.mean([result[2] for result in results]) if results else 0
                    bboxes = [result[0] for result in results]
                    ocr_results.append(OCRResult(
                        text=text,
                        confidence=confidence,
                        method=f"easyocr_fast_{proc_name}",
                        bounding_boxes=bboxes
                    ))
                else:
                    # In full mode, run EasyOCR on all variants
                    for proc_name, proc_image in processed_images.items():
                        results = self.easyocr_reader.readtext(proc_image)
                        text = ' '.join([result[1] for result in results])
                        confidence = np.mean([result[2] for result in results]) if results else 0
                        bboxes = [result[0] for result in results]
                        ocr_results.append(OCRResult(
                            text=text,
                            confidence=confidence,
                            method=f"easyocr_{proc_name}",
                            bounding_boxes=bboxes
                        ))
            except Exception as e:
                logger.warning(f"EasyOCR failed: {e}")
        
        # Save processed images for debugging
        if save_processed:
            self._save_processed_images(processed_images, image_path)
        
        # Select best OCR result
        best_result = max(ocr_results, key=lambda x: x.confidence) if ocr_results else None
        
        if not best_result:
            logger.error("All OCR methods failed")
            return ExtractedData(raw_text="OCR_FAILED")
        
        logger.info(f"Best OCR method: {best_result.method} (confidence: {best_result.confidence:.2f})")
        
        # Extract structured data using enhanced parsing
        extracted_data = self._enhanced_data_extraction(best_result.text, ocr_results)
        extracted_data.raw_text = best_result.text
        extracted_data.confidence_score = best_result.confidence
        
        return extracted_data

    def _advanced_preprocessing(self, image: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Apply multiple advanced preprocessing techniques.
        
        Args:
            image: Input image
            
        Returns:
            Dict of preprocessed images with different techniques
        """
        processed_images = {}
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 1. Standard preprocessing (improved version)
        processed_images['standard'] = self._standard_preprocessing(gray)
        
        # 2. High contrast preprocessing
        processed_images['high_contrast'] = self._high_contrast_preprocessing(gray)
        
        # 3. Denoised preprocessing
        processed_images['denoised'] = self._denoised_preprocessing(gray)
        
        # 4. Sharpened preprocessing
        processed_images['sharpened'] = self._sharpened_preprocessing(gray)
        
        # 5. Perspective corrected (if receipt boundaries detected)
        perspective_corrected = self._perspective_correction(gray)
        if perspective_corrected is not None:
            processed_images['perspective'] = perspective_corrected
        
        # 6. Adaptive preprocessing based on image characteristics
        processed_images['adaptive'] = self._adaptive_preprocessing(gray)
        
        return processed_images

    def _standard_preprocessing(self, gray: np.ndarray) -> np.ndarray:
        """Enhanced standard preprocessing."""
        # Resize if too large
        h, w = gray.shape
        if w > 1200:
            scale = 1200.0 / w
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_LANCZOS4)
        
        # Enhance contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Bilateral filter for noise reduction while preserving edges
        filtered = cv2.bilateralFilter(enhanced, 9, 75, 75)
        
        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Morphological operations to clean up
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return cleaned

    def _high_contrast_preprocessing(self, gray: np.ndarray) -> np.ndarray:
        """High contrast preprocessing for faded receipts."""
        # Histogram equalization
        equalized = cv2.equalizeHist(gray)
        
        # Gamma correction
        gamma = 1.5
        lookup_table = np.array([((i / 255.0) ** (1.0 / gamma)) * 255 for i in np.arange(0, 256)]).astype("uint8")
        gamma_corrected = cv2.LUT(equalized, lookup_table)
        
        # Strong adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gamma_corrected, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, 8
        )
        
        return thresh

    def _denoised_preprocessing(self, gray: np.ndarray) -> np.ndarray:
        """Denoising preprocessing for noisy images."""
        # Non-local means denoising
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Gaussian blur to smooth
        blurred = cv2.GaussianBlur(denoised, (3, 3), 0)
        
        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 9, 2
        )
        
        return thresh

    def _sharpened_preprocessing(self, gray: np.ndarray) -> np.ndarray:
        """Sharpening preprocessing for blurry images."""
        # Unsharp masking
        gaussian = cv2.GaussianBlur(gray, (0, 0), 2.0)
        sharpened = cv2.addWeighted(gray, 1.5, gaussian, -0.5, 0)
        
        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(sharpened)
        
        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return thresh

    def _perspective_correction(self, gray: np.ndarray) -> Optional[np.ndarray]:
        """Detect and correct perspective distortion."""
        # Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Sort contours by area
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
        
        for contour in contours:
            # Approximate contour
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # If we found a 4-point contour, apply perspective transform
            if len(approx) == 4:
                return self._four_point_transform(gray, approx.reshape(4, 2))
        
        return None

    def _adaptive_preprocessing(self, gray: np.ndarray) -> np.ndarray:
        """Adaptive preprocessing based on image characteristics."""
        # Analyze image characteristics
        mean_intensity = np.mean(gray)
        std_intensity = np.std(gray)
        
        # Choose preprocessing based on characteristics
        if mean_intensity < 100:  # Dark image
            # Brighten and enhance contrast
            brightened = cv2.convertScaleAbs(gray, alpha=1.5, beta=30)
            clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(brightened)
        elif std_intensity < 30:  # Low contrast image
            # Enhance contrast significantly
            clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
        else:  # Normal image
            # Standard enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
        
        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return thresh

    def _four_point_transform(self, image: np.ndarray, pts: np.ndarray) -> np.ndarray:
        """Apply perspective transform to get top-down view."""
        # Order points: top-left, top-right, bottom-right, bottom-left
        rect = self._order_points(pts)
        (tl, tr, br, bl) = rect
        
        # Calculate width and height of new image
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        
        # Destination points
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]
        ], dtype="float32")
        
        # Compute perspective transform matrix and apply it
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
        
        return warped

    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """Order points in clockwise order starting from top-left."""
        rect = np.zeros((4, 2), dtype="float32")
        
        # Sum and difference of coordinates
        s = pts.sum(axis=1)
        diff = np.diff(pts, axis=1)
        
        # Top-left has smallest sum, bottom-right has largest sum
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        
        # Top-right has smallest difference, bottom-left has largest difference
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        
        return rect

    def _calculate_tesseract_confidence(self, image: np.ndarray, config: str) -> float:
        """Calculate confidence score for Tesseract OCR."""
        try:
            data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            return np.mean(confidences) / 100.0 if confidences else 0.0
        except:
            return 0.0

    def _save_processed_images(self, processed_images: Dict[str, np.ndarray], original_path: str):
        """Save processed images for debugging."""
        base_name = os.path.splitext(os.path.basename(original_path))[0]
        
        for method, image in processed_images.items():
            save_path = os.path.join("data/processed", f"{base_name}_{method}.jpg")
            cv2.imwrite(save_path, image)

    def _enhanced_data_extraction(self, text: str, ocr_results: List[OCRResult]) -> ExtractedData:
        """
        Enhanced data extraction with intelligent parsing for different receipt formats.
        """
        from enhanced_extractor import EnhancedReceiptExtractor
        
        extractor = EnhancedReceiptExtractor()
        return extractor.extract_data(text, ocr_results)
