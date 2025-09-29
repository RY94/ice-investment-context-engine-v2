# imap_email_ingestion_pipeline/ocr_engine.py
# Multi-engine OCR processor with confidence scoring and fallback
# Supports PaddleOCR, EasyOCR, and Tesseract with intelligent routing
# RELEVANT FILES: attachment_processor.py, entity_extractor.py

import logging
import tempfile
import os
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

# OCR engine imports
try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False
    logging.warning("PaddleOCR not available")

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logging.warning("EasyOCR not available")

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logging.warning("Tesseract not available")

class OCREngine:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize OCR engines
        self.paddle_ocr = None
        self.easy_reader = None
        self.tesseract_available = TESSERACT_AVAILABLE
        
        # Initialize PaddleOCR (primary engine)
        if PADDLE_AVAILABLE:
            try:
                self.paddle_ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang='en',
                    show_log=False,
                    use_gpu=False  # Set to True if GPU available
                )
                self.logger.info("PaddleOCR initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize PaddleOCR: {e}")
                self.paddle_ocr = None
        
        # Initialize EasyOCR (fallback engine)
        if EASYOCR_AVAILABLE:
            try:
                self.easy_reader = easyocr.Reader(['en'])
                self.logger.info("EasyOCR initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize EasyOCR: {e}")
                self.easy_reader = None
        
        # Check if any OCR engine is available
        if not any([self.paddle_ocr, self.easy_reader, self.tesseract_available]):
            self.logger.error("No OCR engines available!")
        
        # OCR confidence thresholds
        self.min_confidence = 0.5
        self.high_confidence = 0.8
        
        # Preprocessing options
        self.preprocess_image = True
        
    def process_image(self, image_path: str, engine: str = 'auto') -> Dict[str, Any]:
        """Process single image with OCR"""
        try:
            if not os.path.exists(image_path):
                return {'error': f'Image not found: {image_path}'}
            
            # Choose OCR engine
            if engine == 'auto':
                engine = self._select_best_engine()
            
            # Preprocess image
            processed_image_path = self._preprocess_image(image_path)
            
            # Perform OCR based on selected engine
            if engine == 'paddle' and self.paddle_ocr:
                result = self._ocr_with_paddle(processed_image_path)
            elif engine == 'easy' and self.easy_reader:
                result = self._ocr_with_easyocr(processed_image_path)
            elif engine == 'tesseract' and self.tesseract_available:
                result = self._ocr_with_tesseract(processed_image_path)
            else:
                # Try engines in order of preference
                result = self._try_all_engines(processed_image_path)
            
            # Clean up preprocessed image if it's different from original
            if processed_image_path != image_path:
                os.unlink(processed_image_path)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing image {image_path}: {e}")
            return {'error': str(e), 'text': '', 'confidence': 0.0}
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Process PDF with OCR by converting pages to images"""
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            all_text = []
            total_confidence = 0.0
            processed_pages = 0
            
            for page_num in range(min(len(doc), 10)):  # Limit to 10 pages
                page = doc[page_num]
                
                # Convert page to image
                mat = fitz.Matrix(2.0, 2.0)  # Scale factor for better quality
                pix = page.get_pixmap(matrix=mat)
                
                # Save as temporary image
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                    pix.save(tmp_file.name)
                    
                    # Process with OCR
                    page_result = self.process_image(tmp_file.name)
                    
                    if not page_result.get('error'):
                        all_text.append(f"=== Page {page_num + 1} ===")
                        all_text.append(page_result.get('text', ''))
                        total_confidence += page_result.get('confidence', 0.0)
                        processed_pages += 1
                    
                    # Clean up temp file
                    os.unlink(tmp_file.name)
            
            doc.close()
            
            avg_confidence = total_confidence / processed_pages if processed_pages > 0 else 0.0
            
            return {
                'text': '\n'.join(all_text),
                'confidence': avg_confidence,
                'pages_processed': processed_pages,
                'method': 'pdf_ocr'
            }
            
        except Exception as e:
            self.logger.error(f"Error processing PDF {pdf_path}: {e}")
            return {'error': str(e), 'text': '', 'confidence': 0.0}
    
    def _select_best_engine(self) -> str:
        """Select the best available OCR engine"""
        if self.paddle_ocr:
            return 'paddle'
        elif self.easy_reader:
            return 'easy'
        elif self.tesseract_available:
            return 'tesseract'
        else:
            return 'none'
    
    def _preprocess_image(self, image_path: str) -> str:
        """Preprocess image to improve OCR accuracy"""
        if not self.preprocess_image:
            return image_path
        
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                return image_path
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply noise reduction
            denoised = cv2.medianBlur(gray, 3)
            
            # Apply adaptive thresholding
            binary = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Apply dilation to thicken text
            kernel = np.ones((1, 1), np.uint8)
            dilated = cv2.dilate(binary, kernel, iterations=1)
            
            # Save preprocessed image
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                cv2.imwrite(tmp_file.name, dilated)
                return tmp_file.name
                
        except Exception as e:
            self.logger.warning(f"Image preprocessing failed: {e}")
            return image_path
    
    def _ocr_with_paddle(self, image_path: str) -> Dict[str, Any]:
        """Perform OCR using PaddleOCR"""
        try:
            result = self.paddle_ocr.ocr(image_path, cls=True)
            
            if not result or not result[0]:
                return {'text': '', 'confidence': 0.0, 'engine': 'paddle'}
            
            # Extract text and confidence scores
            texts = []
            confidences = []
            
            for line in result[0]:
                if len(line) >= 2:
                    text = line[1][0] if line[1] else ''
                    confidence = line[1][1] if len(line[1]) > 1 else 0.0
                    
                    if text.strip():
                        texts.append(text.strip())
                        confidences.append(confidence)
            
            combined_text = '\n'.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return {
                'text': combined_text,
                'confidence': avg_confidence,
                'engine': 'paddle',
                'details': {
                    'lines': len(texts),
                    'raw_result': result[0] if len(str(result)) < 1000 else 'truncated'
                }
            }
            
        except Exception as e:
            self.logger.error(f"PaddleOCR failed: {e}")
            return {'error': str(e), 'text': '', 'confidence': 0.0, 'engine': 'paddle'}
    
    def _ocr_with_easyocr(self, image_path: str) -> Dict[str, Any]:
        """Perform OCR using EasyOCR"""
        try:
            result = self.easy_reader.readtext(image_path)
            
            # Extract text and confidence scores
            texts = []
            confidences = []
            
            for detection in result:
                if len(detection) >= 3:
                    text = detection[1].strip()
                    confidence = detection[2]
                    
                    if text:
                        texts.append(text)
                        confidences.append(confidence)
            
            combined_text = '\n'.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return {
                'text': combined_text,
                'confidence': avg_confidence,
                'engine': 'easyocr',
                'details': {
                    'lines': len(texts),
                    'raw_result': result if len(str(result)) < 1000 else 'truncated'
                }
            }
            
        except Exception as e:
            self.logger.error(f"EasyOCR failed: {e}")
            return {'error': str(e), 'text': '', 'confidence': 0.0, 'engine': 'easyocr'}
    
    def _ocr_with_tesseract(self, image_path: str) -> Dict[str, Any]:
        """Perform OCR using Tesseract"""
        try:
            # Get text and confidence data
            text = pytesseract.image_to_string(Image.open(image_path))
            
            # Get detailed confidence information
            data = pytesseract.image_to_data(
                Image.open(image_path), output_type=pytesseract.Output.DICT
            )
            
            # Calculate average confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
            
            return {
                'text': text.strip(),
                'confidence': avg_confidence,
                'engine': 'tesseract',
                'details': {
                    'words': len([word for word in data['text'] if word.strip()]),
                    'avg_word_confidence': avg_confidence
                }
            }
            
        except Exception as e:
            self.logger.error(f"Tesseract failed: {e}")
            return {'error': str(e), 'text': '', 'confidence': 0.0, 'engine': 'tesseract'}
    
    def _try_all_engines(self, image_path: str) -> Dict[str, Any]:
        """Try all available engines and return the best result"""
        results = []
        
        # Try PaddleOCR first (best accuracy)
        if self.paddle_ocr:
            paddle_result = self._ocr_with_paddle(image_path)
            if not paddle_result.get('error') and paddle_result.get('confidence', 0) > self.min_confidence:
                return paddle_result
            results.append(paddle_result)
        
        # Try EasyOCR second (good speed)
        if self.easy_reader:
            easy_result = self._ocr_with_easyocr(image_path)
            if not easy_result.get('error') and easy_result.get('confidence', 0) > self.min_confidence:
                return easy_result
            results.append(easy_result)
        
        # Try Tesseract last (fallback)
        if self.tesseract_available:
            tesseract_result = self._ocr_with_tesseract(image_path)
            if not tesseract_result.get('error') and tesseract_result.get('confidence', 0) > self.min_confidence:
                return tesseract_result
            results.append(tesseract_result)
        
        # Return best result based on confidence
        if results:
            best_result = max(results, key=lambda x: x.get('confidence', 0))
            best_result['method'] = 'multi_engine_best'
            return best_result
        
        return {'error': 'No OCR engines available', 'text': '', 'confidence': 0.0}
    
    def batch_process_images(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """Process multiple images in batch"""
        results = []
        
        for image_path in image_paths:
            try:
                result = self.process_image(image_path)
                result['image_path'] = image_path
                results.append(result)
            except Exception as e:
                results.append({
                    'image_path': image_path,
                    'error': str(e),
                    'text': '',
                    'confidence': 0.0
                })
        
        return results
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get status of all OCR engines"""
        return {
            'paddle_ocr': {
                'available': self.paddle_ocr is not None,
                'preferred': True,
                'description': 'Primary OCR engine - best accuracy'
            },
            'easyocr': {
                'available': self.easy_reader is not None,
                'preferred': False,
                'description': 'Fallback OCR engine - good speed'
            },
            'tesseract': {
                'available': self.tesseract_available,
                'preferred': False,
                'description': 'Backup OCR engine - most compatible'
            },
            'preprocessing': self.preprocess_image
        }
    
    def optimize_for_financial_documents(self):
        """Optimize OCR settings for financial documents"""
        self.min_confidence = 0.6  # Stricter confidence for financial data
        self.preprocess_image = True
        
        # Configure PaddleOCR for better financial document recognition
        if self.paddle_ocr:
            try:
                # Reinitialize with optimized settings for financial docs
                self.paddle_ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang='en',
                    show_log=False,
                    use_gpu=False,
                    det_algorithm='DB',  # Better for structured documents
                    rec_algorithm='CRNN'  # Better for text recognition
                )
                self.logger.info("OCR optimized for financial documents")
            except Exception as e:
                self.logger.warning(f"Failed to optimize PaddleOCR: {e}")