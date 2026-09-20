from typing import Optional, Dict, Any
from ai.services.syllabus_parser import SyllabusParser
from backend.app.schemas.syllabus import SyllabusStructure


class SyllabusAnalysisAgent:
    """
    AI Agent responsible for Syllabus Analysis, Unit/Topic extraction, and Course Outcome structuring.
    Integrates deterministic baseline parsing in Phase 4 and prepares pluggable LLM provider for Phase 5.
    """

    def __init__(self, use_llm_fallback: bool = False):
        self.parser = SyllabusParser()
        self.use_llm_fallback = use_llm_fallback

    def analyze_syllabus(self, raw_text: str, document_name: str = "") -> SyllabusStructure:
        """
        Processes raw extracted text and converts it into a standardized SyllabusStructure contract.
        """
        # Baseline Phase 4 deterministic pattern parsing
        structure = self.parser.parse(raw_text, document_name=document_name)
        
        # Note for Phase 5: LLM refinement pipeline can be invoked here if enabled
        return structure
