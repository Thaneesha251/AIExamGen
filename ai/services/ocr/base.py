from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import time
import os

class BaseOCRProvider(ABC):
    """Abstract base interface for OCR engines (Tesseract, EasyOCR, PaddleOCR, Mock)."""

    @abstractmethod
    async def extract_text(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text from an image file along with confidence and bounding boxes.
        
        Returns:
            Dict containing:
                - text: str
                - confidence: float (0.0 to 1.0) or None
                - language: str
                - processing_time: float (seconds)
                - bounding_boxes: List[Dict[str, Any]]
                - provider: str
                - metadata: Dict[str, Any]
        """
        pass


class MockOCRProvider(BaseOCRProvider):
    """Deterministic fallback OCR provider for testing and development."""

    def __init__(self, default_text: Optional[str] = None, default_confidence: float = 0.95):
        self.default_text = default_text
        self.default_confidence = default_confidence

    async def extract_text(self, image_path: str) -> Dict[str, Any]:
        start_time = time.time()
        
        # Check if text is provided via mock environment or attribute
        text = self.default_text or "[Mock OCR Extracted Text from answer sheet image]"
        
        return {
            "text": text,
            "confidence": self.default_confidence,
            "language": "eng",
            "processing_time": round(time.time() - start_time, 4),
            "bounding_boxes": [],
            "provider": "MockOCR",
            "metadata": {"image_path": image_path}
        }


class TesseractOCRProvider(BaseOCRProvider):
    """Tesseract OCR Provider using pytesseract and PIL."""

    def __init__(self, lang: str = "eng"):
        self.lang = lang

    async def extract_text(self, image_path: str) -> Dict[str, Any]:
        start_time = time.time()
        try:
            from PIL import Image
            import pytesseract
            
            image = Image.open(image_path)
            data = pytesseract.image_to_data(image, lang=self.lang, output_type=pytesseract.Output.DICT)
            
            text_lines = []
            confidences = []
            boxes = []
            
            for i in range(len(data['text'])):
                word = data['text'][i].strip()
                conf = float(data['conf'][i])
                if word:
                    text_lines.append(word)
                    if conf >= 0:
                        confidences.append(conf / 100.0)
                    boxes.append({
                        "text": word,
                        "left": data['left'][i],
                        "top": data['top'][i],
                        "width": data['width'][i],
                        "height": data['height'][i],
                        "confidence": conf / 100.0 if conf >= 0 else None
                    })

            full_text = pytesseract.image_to_string(image, lang=self.lang).strip()
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.80
            
            return {
                "text": full_text if full_text else " ".join(text_lines),
                "confidence": round(avg_conf, 4),
                "language": self.lang,
                "processing_time": round(time.time() - start_time, 4),
                "bounding_boxes": boxes,
                "provider": "Tesseract",
                "metadata": {"image_path": image_path}
            }
        except Exception as e:
            # Fallback to mock behavior if pytesseract or Tesseract binary is unavailable
            return {
                "text": f"[Tesseract unavailable: {str(e)}]",
                "confidence": 0.50,
                "language": self.lang,
                "processing_time": round(time.time() - start_time, 4),
                "bounding_boxes": [],
                "provider": "TesseractFallback",
                "metadata": {"error": str(e), "image_path": image_path}
            }

