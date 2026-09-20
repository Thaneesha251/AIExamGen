import re
from typing import List, Optional, Tuple, Dict, Any
from backend.app.schemas.syllabus import (
    SyllabusStructure,
    SyllabusUnit,
    SyllabusTopic,
    SyllabusLearningOutcome,
    SourceReference
)
from backend.app.db.models.enums import BloomLevelEnum


class SyllabusParser:
    """
    Deterministic Pattern-Based Syllabus Parser Foundation.
    Extracts Units, Topics, Course Outcomes (COs), and provenance references from raw document text.
    """

    ROMAN_TO_INT = {
        "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
        "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10
    }

    BLOOM_MAP = {
        "remember": BloomLevelEnum.REMEMBER,
        "understand": BloomLevelEnum.UNDERSTAND,
        "apply": BloomLevelEnum.APPLY,
        "analyze": BloomLevelEnum.ANALYZE,
        "evaluate": BloomLevelEnum.EVALUATE,
        "create": BloomLevelEnum.CREATE,
        "k1": BloomLevelEnum.REMEMBER,
        "k2": BloomLevelEnum.UNDERSTAND,
        "k3": BloomLevelEnum.APPLY,
        "k4": BloomLevelEnum.ANALYZE,
        "k5": BloomLevelEnum.EVALUATE,
        "k6": BloomLevelEnum.CREATE,
    }

    def parse(self, raw_text: str, document_name: str = "") -> SyllabusStructure:
        warnings: List[str] = []

        if not raw_text or len(raw_text.strip()) < 30:
            return SyllabusStructure(
                course_title=None,
                units=[],
                learning_outcomes=[],
                warnings=["TEXT_EXTRACTION_UNAVAILABLE: Insufficient text extracted from document."]
            )

        # 1. Parse Course Metadata if available
        course_code, course_title = self._extract_course_header(raw_text)

        # 2. Extract Units & Topics
        units, unit_warnings = self._extract_units(raw_text)
        warnings.extend(unit_warnings)

        # 3. Extract Learning Outcomes / COs
        cos, co_warnings = self._extract_learning_outcomes(raw_text)
        warnings.extend(co_warnings)

        if not units:
            warnings.append("No distinct UNIT sections matched regex patterns. Manual structure review recommended.")
        if not cos:
            warnings.append("No Course Outcomes (CO1..CO5) matched pattern. Manual LO entry recommended.")

        return SyllabusStructure(
            course_title=course_title,
            course_code=course_code,
            units=units,
            learning_outcomes=cos,
            warnings=warnings
        )

    def _extract_course_header(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        code_match = re.search(r'(?:Course Code|Subject Code|Code)\s*[:|-]\s*([A-Z0-9\-]+)', text, re.IGNORECASE)
        title_match = re.search(r'(?:Course Title|Subject Name|Title)\s*[:|-]\s*([^\n\r]+)', text, re.IGNORECASE)

        code = code_match.group(1).strip() if code_match else None
        title = title_match.group(1).strip() if title_match else None
        return code, title

    def _extract_units(self, text: str) -> Tuple[List[SyllabusUnit], List[str]]:
        units: List[SyllabusUnit] = []
        warnings: List[str] = []

        # Regex matching "UNIT 1", "UNIT I:", "Unit 1 -", etc.
        unit_pattern = re.compile(
            r'(?:UNIT|MODULE)\s+([IVXLCDM0-9]+)\s*[:\-\u2013\u2014]?\s*([^\n\r]+)?',
            re.IGNORECASE
        )

        matches = list(unit_pattern.finditer(text))
        if not matches:
            return [], warnings

        for idx, match in enumerate(matches):
            raw_num = match.group(1).strip().upper()
            raw_title = match.group(2).strip() if match.group(2) else f"Unit {raw_num}"

            # Convert Roman to Integer if needed
            unit_num = self.ROMAN_TO_INT.get(raw_num)
            if unit_num is None:
                try:
                    unit_num = int(raw_num)
                except ValueError:
                    unit_num = idx + 1

            # Determine text block boundary between current unit and next unit (or CO section)
            start_pos = match.end()
            end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            
            # Truncate end_pos if "COURSE OUTCOMES" block begins
            co_header = re.search(r'(?:COURSE OUTCOMES|LEARNING OUTCOMES)', text[start_pos:end_pos], re.IGNORECASE)
            if co_header:
                end_pos = start_pos + co_header.start()

            unit_body = text[start_pos:end_pos].strip()

            # Extract Topics inside unit body
            topics = self._extract_topics_from_body(unit_body)

            # Determine page hint if present
            page_num = self._detect_page_number(text[:match.start()])

            units.append(
                SyllabusUnit(
                    unit_number=unit_num,
                    title=raw_title,
                    description=unit_body[:200] + ("..." if len(unit_body) > 200 else ""),
                    weightage=20.0,
                    topics=topics,
                    source_reference=SourceReference(
                        page=page_num,
                        section=f"Unit {unit_num}",
                        source_text=match.group(0).strip()
                    )
                )
            )

        return units, warnings

    def _extract_topics_from_body(self, body: str) -> List[SyllabusTopic]:
        topics: List[SyllabusTopic] = []

        # Split body by semicolon, bullet points, or newlines
        raw_items = re.split(r'[;\u2022\u25cf\n\r]+', body)
        for item in raw_items:
            clean = item.strip()
            # Clean leading numbers like "1. ", "a) "
            clean = re.sub(r'^(?:\d+[\.\)]|[a-z][\.\)])\s*', '', clean, flags=re.IGNORECASE).strip()
            
            if len(clean) >= 3 and len(clean) <= 150:
                topics.append(
                    SyllabusTopic(
                        title=clean,
                        keywords=None,
                        source_reference=SourceReference(source_text=clean[:60])
                    )
                )

        # Fallback if no bullet points found: take first few non-empty lines
        if not topics and body.strip():
            first_line = body.strip().split('\n')[0][:100]
            topics.append(SyllabusTopic(title=first_line, source_reference=SourceReference(source_text=first_line)))

        return topics

    def _extract_learning_outcomes(self, text: str) -> Tuple[List[SyllabusLearningOutcome], List[str]]:
        cos: List[SyllabusLearningOutcome] = []
        warnings: List[str] = []

        # Pattern matching "CO1: ...", "CO1 - ...", "Course Outcome 1: ..."
        co_pattern = re.compile(
            r'(?:CO|LO|Course Outcome|Learning Outcome)\s*([0-9]+)\s*[:\-\u2013\u2014]\s*([^\n\r]+)',
            re.IGNORECASE
        )

        for match in co_pattern.finditer(text):
            num = match.group(1).strip()
            desc = match.group(2).strip()

            if len(desc) >= 5:
                # Detect Bloom level if keywords present
                bloom = None
                desc_lower = desc.lower()
                for keyword, level in self.BLOOM_MAP.items():
                    if keyword in desc_lower:
                        bloom = level
                        break

                page_num = self._detect_page_number(text[:match.start()])

                cos.append(
                    SyllabusLearningOutcome(
                        code=f"CO{num}",
                        description=desc,
                        bloom_level=bloom,
                        source_reference=SourceReference(
                            page=page_num,
                            section=f"CO{num}",
                            source_text=match.group(0).strip()
                        )
                    )
                )

        return cos, warnings

    def _detect_page_number(self, preceding_text: str) -> Optional[int]:
        pages = re.findall(r'---\s*PAGE\s*(\d+)\s*---', preceding_text, re.IGNORECASE)
        if pages:
            try:
                return int(pages[-1])
            except ValueError:
                return None
        return None
