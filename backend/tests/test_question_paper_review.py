import uuid
from app.db.models import (
    Subject,
    QuestionPaper,
    QuestionPaperVersion,
    QuestionPaperItem,
    AnswerKey,
    AnswerKeyItem,
    User,
    QuestionPaperStatusEnum
)
from app.services.question_paper_review_service import QuestionPaperReviewService
from app.schemas.question_paper_review import PaperApprovalRequest, PaperPublishRequest

def test_paper_review_checklist_approve_and_publish(db):
    user = db.query(User).filter(User.email == "admin@example.com").first()
    sub = db.query(Subject).first()
    assert user is not None
    assert sub is not None

    paper = QuestionPaper(
        subject_id=sub.id,
        title="Network Security Final Paper",
        paper_code=f"QP-SEC-TEST-{uuid.uuid4().hex[:6]}",
        total_marks=5.0,
        status=QuestionPaperStatusEnum.GENERATED,
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
        marks=5.0,
        question_text_snapshot="Explain Public Key Infrastructure (PKI).",
        question_type_snapshot="DESCRIPTIVE",
        order_index=1
    )
    db.add(pitem)
    db.commit()

    # Create AnswerKey
    ak = AnswerKey(question_paper_version_id=ver.id, version_number=1, status="DRAFT", generated_by=user.id)
    db.add(ak)
    db.commit()

    akitem = AnswerKeyItem(
        answer_key_id=ak.id,
        question_paper_item_id=pitem.id,
        model_answer="PKI manages digital certificates and public key encryption...",
        maximum_marks=5.0
    )
    db.add(akitem)
    db.commit()

    review_service = QuestionPaperReviewService(db)

    # 1. Checklist
    checklist = review_service.get_review_checklist(paper.id)
    assert checklist.is_approvable is True

    # 2. Approve
    approved_paper = review_service.approve_paper(paper.id, PaperApprovalRequest(comments="Approved for exam"), user)
    assert approved_paper.status == QuestionPaperStatusEnum.APPROVED

    # 3. Publish
    published_paper = review_service.publish_paper(paper.id, PaperPublishRequest(publish_notes="May 2026 exam"), user)
    assert published_paper.status == QuestionPaperStatusEnum.PUBLISHED
