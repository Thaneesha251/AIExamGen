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
from app.services.answer_key_service import AnswerKeyService
from app.schemas.answer_key import AnswerKeyUpdate, AnswerKeyItemCreate

def test_answer_key_generation_and_versioning(db):
    user = db.query(User).filter(User.email == "admin@example.com").first()
    sub = db.query(Subject).first()
    assert user is not None
    assert sub is not None

    paper = QuestionPaper(
        subject_id=sub.id,
        title="DBMS Paper",
        paper_code=f"QP-DBMS-TEST-{uuid.uuid4().hex[:6]}",
        total_marks=10.0,
        created_by=user.id
    )
    db.add(paper)
    db.commit()

    ver = QuestionPaperVersion(
        question_paper_id=paper.id,
        version_number=1,
        generated_by=user.id
    )
    db.add(ver)
    db.commit()

    pitem = QuestionPaperItem(
        question_paper_version_id=ver.id,
        section="Part A",
        question_number="Q1",
        marks=10.0,
        question_text_snapshot="Explain B-Trees and indexing.",
        question_type_snapshot="DESCRIPTIVE",
        order_index=1
    )
    db.add(pitem)
    db.commit()

    ak_service = AnswerKeyService(db)
    ak = ak_service.generate_initial_answer_key(ver.id, user)

    assert ak.id is not None
    assert ak.version_number == 1
    assert len(ak.items) == 1
    assert ak.items[0].question_paper_item_id == pitem.id
    assert ak.items[0].maximum_marks == 10.0

    val_res = ak_service.validate_answer_key_by_id(ak.id)
    assert val_res.is_valid is True

    # Test update answer key
    update_req = AnswerKeyUpdate(
        items=[
            AnswerKeyItemCreate(
                question_paper_item_id=pitem.id,
                model_answer="B-Tree is a self-balancing search tree...",
                keywords=["B-Tree", "indexing", "balanced tree"],
                maximum_marks=10.0
            )
        ]
    )
    updated_ak = ak_service.update_answer_key(ak.id, update_req, user)
    assert updated_ak.items[0].keywords == ["B-Tree", "indexing", "balanced tree"]
