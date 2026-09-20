import uuid
from app.db.models import (
    Subject,
    QuestionPaper,
    QuestionPaperVersion,
    QuestionPaperItem,
    AnswerKey,
    AnswerKeyItem,
    User
)
from app.services.question_paper_export_service import QuestionPaperExportService

def test_question_paper_and_answer_key_pdf_export(db):
    user = db.query(User).filter(User.email == "admin@example.com").first()
    sub = db.query(Subject).first()
    assert user is not None
    assert sub is not None

    paper = QuestionPaper(
        subject_id=sub.id,
        title="Cloud Computing Examination",
        paper_code=f"QP-CLOUD-TEST-{uuid.uuid4().hex[:6]}",
        total_marks=10.0,
        duration_minutes=60,
        created_by=user.id
    )
    db.add(paper)
    db.commit()

    ver = QuestionPaperVersion(question_paper_id=paper.id, version_number=1, generated_by=user.id)
    db.add(ver)
    db.commit()

    pitem = QuestionPaperItem(
        question_paper_version_id=ver.id,
        section="Part A",
        question_number="Q1",
        marks=10.0,
        question_text_snapshot="Explain AWS S3 vs EBS and list key differences.",
        question_type_snapshot="DESCRIPTIVE",
        order_index=1
    )
    db.add(pitem)
    db.commit()

    ak = AnswerKey(question_paper_version_id=ver.id, version_number=1, status="APPROVED", generated_by=user.id)
    db.add(ak)
    db.commit()

    akitem = AnswerKeyItem(
        answer_key_id=ak.id,
        question_paper_item_id=pitem.id,
        model_answer="S3 is object storage whereas EBS is block storage...",
        keywords=["S3", "EBS", "object storage", "block storage"],
        maximum_marks=10.0
    )
    db.add(akitem)
    db.commit()

    export_service = QuestionPaperExportService(db)

    # 1. Question Paper PDF Export
    paper_pdf_bytes = export_service.generate_question_paper_pdf(paper.id)
    assert len(paper_pdf_bytes) > 0
    assert paper_pdf_bytes.startswith(b"%PDF")

    # 2. Answer Key PDF Export
    ak_pdf_bytes = export_service.generate_answer_key_pdf(paper.id)
    assert len(ak_pdf_bytes) > 0
    assert ak_pdf_bytes.startswith(b"%PDF")
