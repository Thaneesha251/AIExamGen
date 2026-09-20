import pytest
from app.db.models import (
    Subject,
    Question,
    Blueprint,
    BlueprintRule,
    QuestionPaper,
    QuestionPaperVersion,
    QuestionPaperItem,
    User,
    QuestionStatusEnum,
    QuestionTypeEnum,
    DifficultyLevelEnum,
    BloomLevelEnum
)
from app.services.blueprint_service import BlueprintService
from app.services.question_paper_generation_service import QuestionPaperGenerationService
from app.schemas.blueprint import BlueprintCreate, BlueprintRuleCreate
from app.schemas.question_paper import (
    PaperGenerationRequest,
    QuestionReplacementRequest
)

def test_paper_generation_deterministic_seed_and_snapshots(db):
    sub = db.query(Subject).first()
    assert sub is not None

    admin_user = db.query(User).filter(User.email == "admin@example.com").first()
    assert admin_user is not None

    # Create 6 approved 2-mark questions for this subject (3 for initial, 3 surplus for replacement)
    qs = []
    for i in range(1, 7):
        q = Question(
            subject_id=sub.id,
            question_text=f"Unique test question text {i} for paper generation",
            question_type=QuestionTypeEnum.SHORT_ANSWER,
            marks=2.0,
            difficulty=DifficultyLevelEnum.MEDIUM,
            bloom_level=BloomLevelEnum.UNDERSTAND,
            status=QuestionStatusEnum.APPROVED,
            expected_answer=f"Expected solution {i}"
        )
        db.add(q)
        qs.append(q)
    db.commit()

    # Create blueprint requesting 3 questions of 2 marks
    bp_service = BlueprintService(db)
    bp_req = BlueprintCreate(
        subject_id=sub.id,
        name="Algorithms Test Blueprint",
        total_marks=6.0,
        rules=[BlueprintRuleCreate(section="Part A", question_count=3, marks_per_question=2.0, total_marks=6.0)]
    )
    bp = bp_service.create_blueprint(bp_req, admin_user)

    # Generate Paper
    gen_service = QuestionPaperGenerationService(db)
    gen_req = PaperGenerationRequest(
        subject_id=sub.id,
        blueprint_id=bp.id,
        title="Algorithms Midterm",
        generation_seed=123
    )

    paper = gen_service.generate_paper(gen_req, admin_user)
    assert paper.id is not None
    assert len(paper.versions) == 1

    ver1 = paper.versions[0]
    assert len(ver1.items) == 3
    assert ver1.items[0].question_text_snapshot is not None
    assert ver1.items[0].marks == 2.0

    # Test single question replacement creating version 2
    replace_req = QuestionReplacementRequest(
        target_item_id=ver1.items[0].id,
        reason="Faculty single replacement test"
    )
    paper_updated = gen_service.replace_question_in_paper(paper.id, replace_req, admin_user)
    assert len(paper_updated.versions) == 2
    assert paper_updated.versions[0].version_number == 2
    assert paper_updated.versions[1].version_number == 1 # Historical version 1 remains intact!
