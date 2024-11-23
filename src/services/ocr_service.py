"""
OCR service implementation using EasyOCR
"""
import easyocr
import torch
import logging

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        self.readers = {}
        self.setup_ocr()
        
    def setup_ocr(self):
        """Initialize OCR readers"""
        try:
            gpu = torch.cuda.is_available()
            device = torch.cuda.get_device_name(0) if gpu else "CPU"
            logger.info(f"Using device: {device} for OCR")
            
            # Initialize readers for different languages
            self.readers = {
                'en_ja': easyocr.Reader(['ja', 'en'], gpu=gpu),
                'en_ko': easyocr.Reader(['ko', 'en'], gpu=gpu),
                'en_ch_sim': easyocr.Reader(['ch_sim', 'en'], gpu=gpu),
                'en_ch_tra': easyocr.Reader(['ch_tra', 'en'], gpu=gpu)
            }
            
        except Exception as e:
            logger.error(f"Error setting up OCR: {str(e)}")
            raise
            
    def get_reader(self, source_lang):
        """Get appropriate reader for the source language"""
        if source_lang == "Japanese":
            return self.readers['en_ja']
        elif source_lang == "Korean":
            return self.readers['en_ko']
        elif source_lang == "Chinese (Simplified)":
            return self.readers['en_ch_sim']
        elif source_lang == "Chinese (Traditional)":
            return self.readers['en_ch_tra']
        else:
            return self.readers['en_ja']  # Default to Japanese reader
            
    def perform_ocr(self, image, source_lang):
        """Perform OCR on the image"""
        try:
            reader = self.get_reader(source_lang)
            result = reader.readtext(image)
            
            if not result:
                return None
                
            # Extract and join text
            text = ' '.join([entry[1] for entry in result])
            return text
            
        except Exception as e:
            logger.error(f"Error performing OCR: {str(e)}")
            raise
