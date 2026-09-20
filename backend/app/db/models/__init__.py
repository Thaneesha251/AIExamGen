from backend.app.db.base import Base, TimestampMixin
from backend.app.db.guid import GUID, generate_uuid

# Enums
from backend.app.db.models.enums import (
    RoleEnum,
    BloomLevelEnum,
    QuestionTypeEnum,
    DifficultyLevelEnum,
    QuestionStatusEnum,
    BlueprintStatusEnum,
    QuestionPaperStatusEnum,
    PaperGenerationMethodEnum,
    AnswerKeyStatusEnum,
    ExamStatusEnum,
    AttendanceStatusEnum,
    AnswerPaperStatusEnum,
    ExtractionMethodEnum,
    EvaluatorTypeEnum,
    EvaluationStatusEnum,
    FeedbackTypeEnum,
    ReviewActionEnum,
    FileCategoryEnum,
    AuditActionEnum,
    SyllabusProcessingStatusEnum,
)

# Domain Entities
from backend.app.db.models.user import Role, User
from backend.app.db.models.academic import Department, Course, Semester, AcademicYear, Subject, Unit, Topic, LearningOutcome, FacultySubjectAssignment
from backend.app.db.models.syllabus import SyllabusDocument
from backend.app.db.models.question import Question, QuestionBank, QuestionBankItem, QuestionVersion
from backend.app.db.models.question_generation_run import QuestionGenerationRun
from backend.app.db.models.blueprint import Blueprint, BlueprintRule
from backend.app.db.models.question_paper import QuestionPaper, QuestionPaperVersion, QuestionPaperItem
from backend.app.db.models.answer_key import AnswerKey, AnswerKeyItem
from backend.app.db.models.rubric import Rubric, RubricCriterion
from backend.app.db.models.examination import Examination, ExaminationStudent
from backend.app.db.models.file_asset import FileAsset
from backend.app.db.models.answer_paper import AnswerPaper, AnswerPage, ExtractedAnswer
from backend.app.db.models.evaluation import Evaluation, EvaluationItem, EvaluationFeedback, FacultyReview
from backend.app.db.models.plagiarism import PlagiarismResult, AnswerSimilarity
from backend.app.db.models.question_quality import QuestionQualityReview
from backend.app.db.models.analytics import ExaminationAnalytics, StudentPerformance
from backend.app.db.models.audit import AuditLog

__all__ = [
    "Base",
    "TimestampMixin",
    "GUID",
    "generate_uuid",
    # Enums
    "RoleEnum",
    "BloomLevelEnum",
    "QuestionTypeEnum",
    "DifficultyLevelEnum",
    "QuestionStatusEnum",
    "BlueprintStatusEnum",
    "QuestionPaperStatusEnum",
    "PaperGenerationMethodEnum",
    "AnswerKeyStatusEnum",
    "ExamStatusEnum",
    "AttendanceStatusEnum",
    "AnswerPaperStatusEnum",
    "ExtractionMethodEnum",
    "EvaluatorTypeEnum",
    "EvaluationStatusEnum",
    "FeedbackTypeEnum",
    "ReviewActionEnum",
    "FileCategoryEnum",
    "AuditActionEnum",
    "SyllabusProcessingStatusEnum",
    # Models
    "Role",
    "User",
    "Department",
    "Course",
    "Semester",
    "AcademicYear",
    "Subject",
    "FacultySubjectAssignment",
    "SyllabusDocument",
    "Unit",
    "Topic",
    "LearningOutcome",
    "Question",
    "QuestionGenerationRun",
    "QuestionBank",

    "QuestionBankItem",
    "QuestionVersion",
    "Blueprint",
    "BlueprintRule",
    "QuestionPaper",
    "QuestionPaperVersion",
    "QuestionPaperItem",
    "AnswerKey",
    "AnswerKeyItem",
    "Rubric",
    "RubricCriterion",
    "Examination",
    "ExaminationStudent",
    "FileAsset",
    "AnswerPaper",
    "AnswerPage",
    "ExtractedAnswer",
    "Evaluation",
    "EvaluationItem",
    "EvaluationFeedback",
    "FacultyReview",
    "PlagiarismResult",
    "AnswerSimilarity",
    "QuestionQualityReview",
    "ExaminationAnalytics",
    "StudentPerformance",
    "AuditLog",
]

