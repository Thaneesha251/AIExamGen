import pytest
from ai.services.ocr.base import MockOCRProvider, TesseractOCRProvider
from ai.services.ocr.ocr_service import OCRService

@pytest.mark.asyncio
async def test_mock_ocr_provider():
    provider = MockOCRProvider(default_text="1. Define Stack\nStack is LIFO", default_confidence=0.92)
    res = await provider.extract_text("dummy_path.png")
    
    assert res["text"] == "1. Define Stack\nStack is LIFO"
    assert res["confidence"] == 0.92
    assert res["provider"] == "MockOCR"
    assert "processing_time" in res


@pytest.mark.asyncio
async def test_tesseract_ocr_fallback():
    provider = TesseractOCRProvider()
    res = await provider.extract_text("non_existent_file.png")
    
    assert "provider" in res
    assert "text" in res
    assert "confidence" in res


@pytest.mark.asyncio
async def test_ocr_service_wrapper():
    service = OCRService(provider=MockOCRProvider("Test Text"))
    res = await service.process_answer_sheet("test.png")
    
    assert res["text"] == "Test Text"
    assert res["provider"] == "MockOCR"
