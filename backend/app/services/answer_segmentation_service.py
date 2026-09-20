import re
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
try:
    from app.db.models import AnswerPaper, AnswerPage, ExtractedAnswer, QuestionPaperVersion, QuestionPaperItem, ExtractionMethodEnum
except ImportError:
    from backend.app.db.models import AnswerPaper, AnswerPage, ExtractedAnswer, QuestionPaperVersion, QuestionPaperItem, ExtractionMethodEnum


class AnswerSegmentationService:
    """Question paper-aware answer segmentation engine."""

    # Regex patterns for question detection
    QUESTION_PATTERN = re.compile(
        r'(?:^|\n)\s*(?:Question\s*|Q\.?\s*|Qn\.?\s*)?(\d{1,2}\s*[a-z]?|\d{1,2}\s*\.\s*[a-z]?|\d{1,2}\s*\))\s*[:.-]?',
        re.IGNORECASE
    )

    def __init__(self, db: Session):
        self.db = db

    def segment_answers(self, answer_paper: AnswerPaper) -> List[ExtractedAnswer]:
        """Segments page-level OCR text into question-level ExtractedAnswer records."""
        # Delete pre-existing automated OCR extracted answers if retrying to prevent duplicate accumulation
        self.db.query(ExtractedAnswer).filter(
            ExtractedAnswer.answer_paper_id == answer_paper.id,
            ExtractedAnswer.manually_corrected == False
        ).delete()
        self.db.flush()

        # Fetch paper items from linked question paper version if available
        question_items_map = self._get_question_paper_items_map(answer_paper)

        # Collect ordered pages
        pages = sorted(answer_paper.pages, key=lambda p: p.page_number)
        if not pages:
            return []

        extracted_segments: List[Dict[str, Any]] = []
        current_segment: Optional[Dict[str, Any]] = None

        for page in pages:
            page_text = page.ocr_text or ""
            page_conf = page.ocr_confidence or 0.85
            lines = page_text.splitlines()

            for line in lines:
                stripped_line = line.strip()
                if not stripped_line:
                    continue

                match = self.QUESTION_PATTERN.search(stripped_line)
                if match:
                    raw_q_num = match.group(1).strip()
                    clean_q_num = self._clean_question_number(raw_q_num)

                    # If we matched a valid question start
                    if clean_q_num:
                        # Save existing segment
                        if current_segment:
                            extracted_segments.append(current_segment)

                        # Start new segment
                        text_after_num = stripped_line[match.end():].strip()
                        current_segment = {
                            "question_number": clean_q_num,
                            "text_parts": [text_after_num] if text_after_num else [],
                            "page_start": page.page_number,
                            "page_end": page.page_number,
                            "ocr_confidences": [page_conf],
                            "first_page_id": page.id
                        }
                        continue

                # Not a new question header, append to active segment or initialize default unmapped segment
                if current_segment:
                    current_segment["text_parts"].append(stripped_line)
                    current_segment["page_end"] = page.page_number
                    current_segment["ocr_confidences"].append(page_conf)
                else:
                    # Unmapped content before any question header detected
                    current_segment = {
                        "question_number": "Unmapped",
                        "text_parts": [stripped_line],
                        "page_start": page.page_number,
                        "page_end": page.page_number,
                        "ocr_confidences": [page_conf],
                        "first_page_id": page.id
                    }

        if current_segment:
            extracted_segments.append(current_segment)

        # Build ExtractedAnswer ORM instances
        created_records: List[ExtractedAnswer] = []
        for seg in extracted_segments:
            q_num = seg["question_number"]
            full_text = "\n".join(seg["text_parts"]).strip()

            # Cross-reference with question paper version items
            item_id, seg_conf = self._match_question_item(q_num, question_items_map)

            avg_ocr_conf = (
                sum(seg["ocr_confidences"]) / len(seg["ocr_confidences"])
                if seg["ocr_confidences"] else 0.80
            )

            extracted_ans = ExtractedAnswer(
                answer_paper_id=answer_paper.id,
                question_paper_item_id=item_id,
                answer_page_id=seg["first_page_id"],
                question_number=q_num,
                extracted_text=full_text,
                extraction_confidence=round(avg_ocr_conf * seg_conf, 4),
                ocr_confidence=round(avg_ocr_conf, 4),
                segmentation_confidence=round(seg_conf, 4),
                page_start=seg["page_start"],
                page_end=seg["page_end"],
                extraction_method=ExtractionMethodEnum.OCR,
                manually_corrected=False,
                status="SEGMENTED"
            )
            self.db.add(extracted_ans)
            created_records.append(extracted_ans)

        self.db.flush()
        return created_records

    def _clean_question_number(self, raw: str) -> str:
        """Standardizes raw question string e.g., '1.', 'Q1', '1)' -> '1'."""
        cleaned = re.sub(r'[^a-zA-Z0-9]', '', raw).upper()
        if cleaned.startswith("Q") and len(cleaned) > 1 and cleaned[1:].isdigit():
            cleaned = cleaned[1:]
        return cleaned or raw

    def _get_question_paper_items_map(self, answer_paper: AnswerPaper) -> Dict[str, QuestionPaperItem]:
        """Loads paper items keyed by question label / sequence number."""
        items_map: Dict[str, QuestionPaperItem] = {}
        
        # Trace via Examination -> QuestionPaperVersion
        if answer_paper.examination and answer_paper.examination.question_paper_version_id:
            qp_version = self.db.query(QuestionPaperVersion).filter(
                QuestionPaperVersion.id == answer_paper.examination.question_paper_version_id
            ).first()

            if qp_version and qp_version.items:
                for idx, item in enumerate(sorted(qp_version.items, key=lambda x: x.sequence_number), 1):
                    # Key by item number, e.g. "1", "2", "3" or item.item_label
                    items_map[str(idx)] = item
                    if item.item_label:
                        items_map[item.item_label.upper()] = item
                        cleaned_label = re.sub(r'[^a-zA-Z0-9]', '', item.item_label).upper()
                        items_map[cleaned_label] = item

        return items_map

    def _match_question_item(self, q_num: str, items_map: Dict[str, QuestionPaperItem]) -> Tuple[Optional[str], float]:
        """Matches detected question number to QuestionPaperItem and assigns segmentation confidence."""
        if not items_map:
            return None, 0.70

        clean_key = re.sub(r'[^a-zA-Z0-9]', '', q_num).upper()
        if clean_key in items_map:
            return items_map[clean_key].id, 0.95

        if q_num in items_map:
            return items_map[q_num].id, 0.95

        # Fuzzy check or unmapped
        return None, 0.40
