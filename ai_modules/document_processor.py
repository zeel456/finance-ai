import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import os
import cv2
import numpy as np
from PyPDF2 import PdfReader
import pdf2image
from typing import Tuple, Optional
import gc
import sys

class ImprovedDocumentProcessor:
    """Memory-optimized OCR with full accuracy maintained"""
    
    def __init__(self, tesseract_path: Optional[str] = None):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        self.ocr_config = {
            'standard': '--oem 3 --psm 6',
            'sparse': '--oem 3 --psm 11',
            'single_column': '--oem 3 --psm 4',
        }
        
        # Force garbage collection threshold
        gc.set_threshold(700, 10, 10)
    
    def _clean_memory(self):
        """Aggressive memory cleanup"""
        gc.collect()
        
    def preprocess_image_advanced(self, image: Image.Image) -> Image.Image:
        """Advanced preprocessing with memory management"""
        try:
            # Convert to numpy early, close PIL image
            img_array = np.array(image)
            
            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Free original array
            del img_array
            
            # Smart resizing - stay within bounds
            height, width = gray.shape
            
            # Upscale if too small
            if height < 1000 or width < 1000:
                scale = max(1000 / height, 1000 / width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # Downscale if too large (prevents memory overflow)
            height, width = gray.shape
            if height > 2500 or width > 2500:  # Reduced from 3000
                scale = min(2500 / height, 2500 / width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # Noise removal
            denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            del gray
            
            # Adaptive thresholding
            binary = cv2.adaptiveThreshold(
                denoised, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11, 2
            )
            del denoised
            
            # Deskew
            binary = self.deskew_image(binary)
            
            # Morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
            processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            del binary
            
            # Convert back to PIL
            pil_image = Image.fromarray(processed)
            del processed
            
            self._clean_memory()
            
            return pil_image
            
        except Exception as e:
            print(f"Advanced preprocessing failed: {e}, using basic")
            self._clean_memory()
            return self.preprocess_image_basic(image)
    
    def deskew_image(self, image: np.ndarray) -> np.ndarray:
        """Detect and correct skew - same accuracy"""
        try:
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
            
            del edges
            
            if lines is not None and len(lines) > 0:
                angles = []
                for line in lines[:10]:
                    rho, theta = line[0]
                    angle = (theta * 180 / np.pi) - 90
                    angles.append(angle)
                
                median_angle = np.median(angles)
                
                if abs(median_angle) > 0.5:
                    (h, w) = image.shape
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                    rotated = cv2.warpAffine(
                        image, M, (w, h),
                        flags=cv2.INTER_CUBIC,
                        borderMode=cv2.BORDER_REPLICATE
                    )
                    del M
                    return rotated
            
            return image
            
        except Exception as e:
            print(f"Deskew failed: {e}")
            return image
    
    def preprocess_image_basic(self, image: Image.Image) -> Image.Image:
        """Basic preprocessing - same as before"""
        try:
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Limit size for memory
            max_size = 2000
            if image.width > max_size or image.height > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            image = image.convert('L')
            
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            image = image.filter(ImageFilter.SHARPEN)
            
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.2)
            
            return image
            
        except Exception as e:
            print(f"Basic preprocessing failed: {e}")
            return image
    
    def extract_text_from_image(self, image_path: str, use_advanced: bool = True) -> Tuple[Optional[str], Optional[str]]:
        """Extract text - maintains all accuracy features"""
        try:
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
            
            # Close original to free memory
            image.close()
            del image
            
            # Try multiple configs
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
                    
                    # Clean between attempts
                    self._clean_memory()
                    
                except Exception as e:
                    print(f"OCR with config {config_name} failed: {e}")
                    continue
            
            # Clean up processed image
            processed_image.close()
            del processed_image
            self._clean_memory()
            
            if not results:
                return None, "All OCR attempts failed"
            
            best_result = max(results, key=lambda x: x['quality'])
            
            print(f"✅ Best OCR config: {best_result['config']} (quality: {best_result['quality']:.1f}%)")
            
            return best_result['text'].strip(), None
            
        except Exception as e:
            self._clean_memory()
            return None, f"Error extracting text from image: {str(e)}"
    
    def extract_text_from_pdf(self, pdf_path: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract from PDF - same functionality"""
        try:
            text = ""
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    
                    # Clean memory every 5 pages
                    if page_num % 5 == 0:
                        self._clean_memory()
            
            if text.strip() and self.get_text_quality_score(text) > 30:
                return text.strip(), None
            
            print("PDF appears to be scanned, using OCR...")
            return self.extract_text_from_scanned_pdf(pdf_path)
            
        except Exception as e:
            self._clean_memory()
            return None, f"Error extracting text from PDF: {str(e)}"
    
    def extract_text_from_scanned_pdf(self, pdf_path: str) -> Tuple[Optional[str], Optional[str]]:
        """OCR scanned PDF - process page by page to save memory"""
        try:
            # Convert with lower DPI on free tier to save memory
            dpi = 200  # Reduced from 300, still good accuracy
            images = pdf2image.convert_from_path(pdf_path, dpi=dpi)
            
            all_text = []
            
            for i, image in enumerate(images):
                print(f"Processing page {i+1}/{len(images)}...")
                
                # Process image
                processed_image = self.preprocess_image_advanced(image)
                
                # Extract text
                page_text = pytesseract.image_to_string(
                    processed_image,
                    lang='eng',
                    config=self.ocr_config['standard']
                )
                
                if page_text.strip():
                    all_text.append(f"--- Page {i+1} ---\n{page_text}")
                
                # CRITICAL: Clean up immediately after each page
                image.close()
                processed_image.close()
                del image
                del processed_image
                del page_text
                self._clean_memory()
            
            combined_text = "\n\n".join(all_text)
            
            # Final cleanup
            del all_text
            del images
            self._clean_memory()
            
            if combined_text.strip():
                return combined_text.strip(), None
            else:
                return None, "No text could be extracted from scanned PDF"
            
        except Exception as e:
            self._clean_memory()
            return None, f"Error processing scanned PDF: {str(e)}"
    
    def process_document(self, file_path: str, file_extension: str) -> Tuple[Optional[str], Optional[str]]:
        """Main processing function - same as before"""
        file_extension = file_extension.lower().replace('.', '')
        
        if file_extension == 'pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_extension in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp']:
            return self.extract_text_from_image(file_path)
        else:
            return None, f"Unsupported file type: {file_extension}"
    
    def get_text_quality_score(self, text: str) -> float:
        """Same quality scoring as before"""
        if not text:
            return 0
        
        words = text.split()
        if not words:
            return 0
        
        readable_words = [w for w in words if any(c.isalpha() for c in w)]
        base_quality = (len(readable_words) / len(words)) * 100
        
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        special_ratio = special_chars / len(text) if text else 0
        
        if special_ratio > 0.3:
            base_quality *= 0.7
        
        common_words = ['the', 'and', 'to', 'of', 'a', 'in', 'is', 'for', 'on', 'with']
        common_count = sum(1 for word in words if word.lower() in common_words)
        
        if common_count > 0:
            base_quality += min(common_count * 2, 10)
        
        return min(round(base_quality, 2), 100)
    
    def extract_with_fallback(self, file_path: str, file_extension: str) -> Tuple[Optional[str], Optional[str], dict]:
        """Extract with fallback - same as before"""
        metadata = {
            'method_used': None,
            'quality_score': 0,
            'preprocessing': None,
            'pages_processed': 0
        }
        
        text, error = self.process_document(file_path, file_extension)
        
        if text:
            metadata['quality_score'] = self.get_text_quality_score(text)
            metadata['method_used'] = 'primary'
            
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
        
        # Final cleanup
        self._clean_memory()
        
        return text, error, metadata

DocumentProcessor = ImprovedDocumentProcessor