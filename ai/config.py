import os
from pydantic import BaseModel

class AISettings(BaseModel):
    provider: str = os.getenv("AI_PROVIDER", "mock")
    model: str = os.getenv("AI_MODEL", "mock-model")
    api_key: str = os.getenv("AI_API_KEY", "")
    ocr_provider: str = os.getenv("OCR_PROVIDER", "mock")
    tesseract_cmd: str = os.getenv("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")

ai_settings = AISettings()
