from typing import Dict, Any, Optional
import os
from ai.services.ocr.base import BaseOCRProvider, MockOCRProvider, TesseractOCRProvider

class OCRService:
    """Service wrapper for document OCR processing."""
    
    def __init__(self, provider: Optional[BaseOCRProvider] = None):
        if provider:
            self.provider = provider
        else:
            provider_name = os.getenv("OCR_PROVIDER", "mock").lower()
            if provider_name == "tesseract":
                self.provider = TesseractOCRProvider()
            else:
                self.provider = MockOCRProvider()
        
    async def process_answer_sheet(self, image_path: str) -> Dict[str, Any]:
        return await self.provider.extract_text(image_path)

    async def process_image(self, image_path: str) -> Dict[str, Any]:
        return await self.provider.extract_text(image_path)

