import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import os
import cv2
import numpy as np
from PyPDF2 import PdfReader
import pdf2image
from typing import Tuple, Optional
import io

class ImprovedDocumentProcessor:


    """Extract text from documents using advanced OCR techniques"""
    
    def __init__(self, tesseract_path: Optional[str] = None):
        # Set Tesseract path
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # OCR configuration for better accuracy
        self.ocr_config = {
            'standard': '--oem 3 --psm 6',  # Assume uniform block of text
            'sparse': '--oem 3 --psm 11',   # Sparse text
            'single_column': '--oem 3 --psm 4',  # Single column
        }
    
    def preprocess_image_advanced(self, image: Image.Image) -> Image.Image:
        """Advanced image preprocessing for better OCR accuracy"""
        try:
            # Convert PIL to OpenCV format
            img_array = np.array(image)
            
            # Convert to grayscale if needed
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Resize if too small (upscale for better OCR)
            height, width = gray.shape
            if height < 1000 or width < 1000:
                scale = max(1000 / height, 1000 / width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # Resize if too large
            height, width = gray.shape
            if height > 3000 or width > 3000:
                scale = min(3000 / height, 3000 / width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # Noise removal
            denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            
            # Adaptive thresholding (works better than simple threshold)
            binary = cv2.adaptiveThreshold(
                denoised, 255, 
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 
                11, 2
            )
            
            # Deskew (rotate to correct angle)
            binary = self.deskew_image(binary)
            
            # Morphological operations to improve text
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
            processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # Convert back to PIL
            pil_image = Image.fromarray(processed)
            
            return pil_image
            
        except Exception as e:
            print(f"Advanced preprocessing failed: {e}, using basic preprocessing")
            return self.preprocess_image_basic(image)
    
    def deskew_image(self, image: np.ndarray) -> np.ndarray:
        """Detect and correct skew in document images"""
        try:
            # Detect edges
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            
            # Detect lines using HoughLines
            lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
            
            if lines is not None and len(lines) > 0:
                # Calculate dominant angle
                angles = []
                for line in lines[:10]:  # Use top 10 lines
                    rho, theta = line[0]
                    angle = (theta * 180 / np.pi) - 90
                    angles.append(angle)
                
                # Get median angle
                median_angle = np.median(angles)
                
                # Only rotate if angle is significant (> 0.5 degrees)
                if abs(median_angle) > 0.5:
                    # Rotate image
                    (h, w) = image.shape
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                    rotated = cv2.warpAffine(
                        image, M, (w, h),
                        flags=cv2.INTER_CUBIC,
                        borderMode=cv2.BORDER_REPLICATE
                    )
                    return rotated
            
            return image
            
        except Exception as e:
            print(f"Deskew failed: {e}")
            return image
    
    def preprocess_image_basic(self, image: Image.Image) -> Image.Image:
        """Basic image preprocessing as fallback"""
        try:
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large
            max_size = 2500
            if image.width > max_size or image.height > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Convert to grayscale
            image = image.convert('L')
            
            # Increase contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Sharpen
            image = image.filter(ImageFilter.SHARPEN)
            
            # Adjust brightness if too dark or too bright
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.2)
            
            return image
            
        except Exception as e:
            print(f"Basic preprocessing failed: {e}")
            return image
    
    def extract_text_from_image(self, image_path: str, use_advanced: bool = True) -> Tuple[Optional[str], Optional[str]]:
        """Extract text from image using OCR with preprocessing"""
        try:
            # Open image
            image = Image.open(image_path)
            
            # Preprocess
            if use_advanced:
                try:
                    processed_image = self.preprocess_image_advanced(image)
                except Exception as e:
                    print(f"Advanced preprocessing failed, using basic: {e}")
                    processed_image = self.preprocess_image_basic(image)
            else:
                processed_image = self.preprocess_image_basic(image)
            
            # Try multiple OCR configurations and pick best result
            results = []
            
            for config_name, config in self.ocr_config.items():
                try:
                    text = pytesseract.image_to_string(processed_image, lang='eng', config=config)
                    quality = self.get_text_quality_score(text)
                    results.append({
                        'text': text,
                        'quality': quality,
                        'config': config_name
                    })
                except Exception as e:
                    print(f"OCR with config {config_name} failed: {e}")
                    continue
            
            if not results:
                return None, "All OCR attempts failed"
            
            # Pick best result
            best_result = max(results, key=lambda x: x['quality'])
            
            print(f"✅ Best OCR config: {best_result['config']} (quality: {best_result['quality']:.1f}%)")
            
            return best_result['text'].strip(), None
            
        except Exception as e:
            return None, f"Error extracting text from image: {str(e)}"
    
    def extract_text_from_pdf(self, pdf_path: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract text from PDF (handles both text and scanned PDFs)"""
        try:
            text = ""
            
            # First, try text extraction (for text-based PDFs)
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            # If text extracted, return it
            if text.strip() and self.get_text_quality_score(text) > 30:
                return text.strip(), None
            
            # If no text or poor quality, treat as scanned PDF
            print("PDF appears to be scanned, using OCR...")
            return self.extract_text_from_scanned_pdf(pdf_path)
            
        except Exception as e:
            return None, f"Error extracting text from PDF: {str(e)}"
    
    def extract_text_from_scanned_pdf(self, pdf_path: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract text from scanned PDF using OCR"""
        try:
            # Convert PDF pages to images
            images = pdf2image.convert_from_path(pdf_path, dpi=300)
            
            all_text = []
            
            for i, image in enumerate(images):
                print(f"Processing page {i+1}/{len(images)}...")
                
                # Preprocess image
                processed_image = self.preprocess_image_advanced(image)
                
                # Extract text
                page_text = pytesseract.image_to_string(
                    processed_image, 
                    lang='eng',
                    config=self.ocr_config['standard']
                )
                
                if page_text.strip():
                    all_text.append(f"--- Page {i+1} ---\n{page_text}")
            
            combined_text = "\n\n".join(all_text)
            
            if combined_text.strip():
                return combined_text.strip(), None
            else:
                return None, "No text could be extracted from scanned PDF"
            
        except Exception as e:
            return None, f"Error processing scanned PDF: {str(e)}"
    
    def process_document(self, file_path: str, file_extension: str) -> Tuple[Optional[str], Optional[str]]:
        """Main function to process any document type"""
        
        file_extension = file_extension.lower().replace('.', '')
        
        # Determine file type and extract text
        if file_extension == 'pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_extension in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp']:
            return self.extract_text_from_image(file_path)
        else:
            return None, f"Unsupported file type: {file_extension}"
    
    def get_text_quality_score(self, text: str) -> float:
        """Estimate OCR quality based on text characteristics"""
        if not text:
            return 0
        
        # Count readable words (alpha characters)
        words = text.split()
        if not words:
            return 0
        
        readable_words = [w for w in words if any(c.isalpha() for c in w)]
        
        # Calculate base quality
        base_quality = (len(readable_words) / len(words)) * 100
        
        # Penalize if too many special characters
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        special_ratio = special_chars / len(text) if text else 0
        
        if special_ratio > 0.3:
            base_quality *= 0.7
        
        # Bonus for common words
        common_words = ['the', 'and', 'to', 'of', 'a', 'in', 'is', 'for', 'on', 'with']
        common_count = sum(1 for word in words if word.lower() in common_words)
        
        if common_count > 0:
            base_quality += min(common_count * 2, 10)
        
        return min(round(base_quality, 2), 100)
    
    def extract_with_fallback(self, file_path: str, file_extension: str) -> Tuple[Optional[str], Optional[str], dict]:
        """Extract text with multiple fallback strategies and return metadata"""
        
        metadata = {
            'method_used': None,
            'quality_score': 0,
            'preprocessing': None,
            'pages_processed': 0
        }
        
        # Primary extraction
        text, error = self.process_document(file_path, file_extension)
        
        if text:
            metadata['quality_score'] = self.get_text_quality_score(text)
            metadata['method_used'] = 'primary'
            
            # If quality is poor and it's an image, try different preprocessing
            if metadata['quality_score'] < 50 and file_extension in ['png', 'jpg', 'jpeg']:
                print(f"Quality low ({metadata['quality_score']:.1f}%), trying basic preprocessing...")
                text_fallback, _ = self.extract_text_from_image(file_path, use_advanced=False)
                
                if text_fallback:
                    quality_fallback = self.get_text_quality_score(text_fallback)
                    if quality_fallback > metadata['quality_score']:
                        text = text_fallback
                        metadata['quality_score'] = quality_fallback
                        metadata['method_used'] = 'fallback'
                        metadata['preprocessing'] = 'basic'
        
        return text, error, metadata

DocumentProcessor = ImprovedDocumentProcessor
