import io
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

try:
    from app.repositories.question_paper_repository import QuestionPaperRepository
    from app.repositories.answer_key_repository import AnswerKeyRepository
    from app.db.models import QuestionPaper, QuestionPaperVersion, AnswerKey, User
except ImportError:
    from backend.app.repositories.question_paper_repository import QuestionPaperRepository
    from backend.app.repositories.answer_key_repository import AnswerKeyRepository
    from backend.app.db.models import QuestionPaper, QuestionPaperVersion, AnswerKey, User

class NumberedCanvas:
    """Two-pass canvas for adding total page numbers in footer."""
    def __init__(self, *args, **kwargs):
        pass

class QuestionPaperExportService:
    def __init__(self, db: Session):
        self.db = db
        self.paper_repo = QuestionPaperRepository(db)
        self.ak_repo = AnswerKeyRepository(db)

    def generate_question_paper_pdf(self, paper_id: str, version_number: Optional[int] = None) -> bytes:
        paper = self.paper_repo.get_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question Paper not found.")

        if version_number:
            ver = self.paper_repo.get_version_by_number(paper_id, version_number)
        else:
            ver = self.paper_repo.get_latest_version(paper_id)

        if not ver:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question Paper Version not found.")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'InstHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            alignment=1, # Center
            textColor=colors.HexColor('#0f172a')
        )
        subtitle_style = ParagraphStyle(
            'InstSubHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=15,
            alignment=1,
            textColor=colors.HexColor('#334155')
        )
        meta_style = ParagraphStyle(
            'MetaText',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor('#1e293b')
        )
        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=15,
            alignment=1,
            textColor=colors.HexColor('#1e3a8a')
        )
        qnum_style = ParagraphStyle(
            'QNum',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor('#0f172a')
        )
        qtext_style = ParagraphStyle(
            'QText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor('#1e293b')
        )
        opt_style = ParagraphStyle(
            'OptText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#334155')
        )

        elements = []

        # Institution Header
        subject_name = paper.subject.name if paper.subject else "EXAMINATION"
        subject_code = paper.subject.code if paper.subject else "EXAM101"

        elements.append(Paragraph("NATIONAL INSTITUTE OF TECHNOLOGY & ACADEMICS", title_style))
        elements.append(Paragraph("DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING", subtitle_style))
        elements.append(Paragraph(f"MODEL EXAMINATION — {paper.title.upper()}", subtitle_style))
        elements.append(Spacer(1, 10))

        meta_data = [
            [
                Paragraph(f"<b>Subject:</b> {subject_name} ({subject_code})", meta_style),
                Paragraph(f"<b>Code:</b> {paper.paper_code}", meta_style)
            ],
            [
                Paragraph(f"<b>Duration:</b> {paper.duration_minutes} Mins", meta_style),
                Paragraph(f"<b>Max Marks:</b> {int(paper.total_marks)}", meta_style)
            ]
        ]
        meta_table = Table(meta_data, colWidths=[360, 180])
        meta_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 2),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 6))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0f172a'), spaceBefore=2, spaceAfter=8))

        # Instructions
        elements.append(Paragraph("<b>GENERAL INSTRUCTIONS:</b>", meta_style))
        elements.append(Paragraph("1. Answer all questions in accordance with section rules.", qtext_style))
        elements.append(Paragraph("2. Figures to the right indicate full marks.", qtext_style))
        elements.append(Paragraph("3. Assume suitable data wherever necessary.", qtext_style))
        elements.append(Spacer(1, 10))

        # Group items by section
        items_by_section = {}
        for item in ver.items:
            sec = item.section or "Section A"
            items_by_section.setdefault(sec, []).append(item)

        for sec_name, items in items_by_section.items():
            sec_marks = sum(i.marks for i in items)
            elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor('#cbd5e1'), spaceBefore=4, spaceAfter=6))
            elements.append(Paragraph(f"{sec_name.upper()} — ({len(items)} Questions × Marks = {int(sec_marks)} Marks)", section_style))
            elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor('#cbd5e1'), spaceBefore=6, spaceAfter=8))

            for item in items:
                q_block = []
                q_text = item.question_text_snapshot
                q_num = item.question_number

                col_num = Paragraph(f"{q_num}.", qnum_style)
                col_text = Paragraph(q_text, qtext_style)
                col_marks = Paragraph(f"[{int(item.marks)}]", qnum_style)

                # MCQ options if available
                if item.options_snapshot and isinstance(item.options_snapshot, dict):
                    opts = item.options_snapshot.get("options", [])
                    if opts:
                        opt_paras = []
                        labels = ["A", "B", "C", "D", "E"]
                        for idx, o in enumerate(opts):
                            lbl = labels[idx] if idx < len(labels) else str(idx+1)
                            opt_paras.append(Paragraph(f"({lbl}) {o}", opt_style))
                        
                        # Layout options in 2 columns
                        opt_rows = []
                        for i in range(0, len(opt_paras), 2):
                            r = [opt_paras[i]]
                            if i + 1 < len(opt_paras):
                                r.append(opt_paras[i+1])
                            else:
                                r.append(Paragraph("", opt_style))
                            opt_rows.append(r)

                        opt_table = Table(opt_rows, colWidths=[240, 240])
                        opt_table.setStyle(TableStyle([
                            ('VALIGN', (0,0), (-1,-1), 'TOP'),
                            ('LEFTPADDING', (0,0), (-1,-1), 0),
                            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                        ]))
                        col_text = [col_text, Spacer(1, 4), opt_table]

                q_table_data = [[col_num, col_text, col_marks]]
                q_table = Table(q_table_data, colWidths=[30, 460, 50])
                q_table.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('TOPPADDING', (0,0), (-1,-1), 4),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                    ('ALIGN', (2,0), (2,0), 'RIGHT'),
                ]))

                q_block.append(q_table)
                elements.append(KeepTogether(q_block))

            elements.append(Spacer(1, 8))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_answer_key_pdf(self, paper_id: str, version_number: Optional[int] = None) -> bytes:
        paper = self.paper_repo.get_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question Paper not found.")

        if version_number:
            ver = self.paper_repo.get_version_by_number(paper_id, version_number)
        else:
            ver = self.paper_repo.get_latest_version(paper_id)

        if not ver:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question Paper Version not found.")

        ak = self.ak_repo.get_latest_answer_key(ver.id)
        if not ak:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer Key not found for this paper version.")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('AKTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=14, leading=18, alignment=1, textColor=colors.HexColor('#0f172a'))
        sub_style = ParagraphStyle('AKSub', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, leading=15, alignment=1, textColor=colors.HexColor('#2563eb'))
        header_style = ParagraphStyle('AKHead', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=14, textColor=colors.HexColor('#0f172a'))
        ans_style = ParagraphStyle('AKAns', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=13.5, textColor=colors.HexColor('#1e293b'))
        tag_style = ParagraphStyle('AKTag', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=9, leading=12, textColor=colors.HexColor('#475569'))

        elements = []

        elements.append(Paragraph("CONFIDENTIAL — FACULTY ANSWER KEY & EVALUATION GUIDANCE", title_style))
        elements.append(Paragraph(f"Paper Code: {paper.paper_code} | Paper Ver: {ver.version_number} | Answer Key Ver: {ak.version_number}", sub_style))
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563eb'), spaceBefore=2, spaceAfter=10))

        ak_item_map = {item.question_paper_item_id: item for item in ak.items}

        for pitem in ver.items:
            q_block = []
            aki = ak_item_map.get(pitem.id)
            q_num = pitem.question_number
            q_text = pitem.question_text_snapshot

            q_block.append(Paragraph(f"<b>Question #{q_num}</b> [{int(pitem.marks)} Marks] — <i>{pitem.section}</i>", header_style))
            q_block.append(Paragraph(f"<b>Question:</b> {q_text}", ans_style))
            q_block.append(Spacer(1, 4))

            if aki:
                q_block.append(Paragraph(f"<b>Model Answer:</b><br/>{aki.model_answer}", ans_style))
                q_block.append(Spacer(1, 3))
                if aki.keywords:
                    k_str = ", ".join(aki.keywords) if isinstance(aki.keywords, list) else str(aki.keywords)
                    q_block.append(Paragraph(f"<b>Keywords:</b> {k_str}", tag_style))
                if aki.concepts:
                    c_str = ", ".join(aki.concepts) if isinstance(aki.concepts, list) else str(aki.concepts)
                    q_block.append(Paragraph(f"<b>Concepts:</b> {c_str}", tag_style))
                if aki.marking_notes:
                    q_block.append(Paragraph(f"<b>Marking Notes:</b> {aki.marking_notes}", tag_style))

                # Rubric details if assigned
                if aki.rubric and aki.rubric.criteria:
                    q_block.append(Spacer(1, 4))
                    q_block.append(Paragraph("<b>Rubric Criteria Breakdown:</b>", header_style))
                    r_rows = [[Paragraph("<b>Criterion</b>", header_style), Paragraph("<b>Description</b>", header_style), Paragraph("<b>Max Marks</b>", header_style)]]
                    for crit in aki.rubric.criteria:
                        r_rows.append([
                            Paragraph(crit.criterion, ans_style),
                            Paragraph(crit.description or "-", ans_style),
                            Paragraph(str(crit.marks), ans_style)
                        ])
                    rtable = Table(r_rows, colWidths=[140, 280, 80])
                    rtable.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
                        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
                        ('TOPPADDING', (0,0), (-1,-1), 4),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                    ]))
                    q_block.append(rtable)

            else:
                q_block.append(Paragraph("<i>No Answer Key Item configured.</i>", tag_style))

            q_block.append(Spacer(1, 6))
            q_block.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceBefore=4, spaceAfter=8))
            elements.append(KeepTogether(q_block))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
