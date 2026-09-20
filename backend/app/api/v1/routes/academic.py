from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

try:
    from app.api.deps import (
        get_db,
        get_current_user,
        require_admin,
        require_admin_or_faculty
    )
    from app.services.academic_service import AcademicService
    from app.schemas.academic import (
        DepartmentSchema,
        DepartmentCreate,
        DepartmentUpdate,
        CourseSchema,
        CourseCreate,
        CourseUpdate,
        SemesterSchema,
        SemesterCreate,
        AcademicYearSchema,
        AcademicYearCreate,
        SubjectSchema,
        SubjectCreate,
        SubjectUpdate,
        UnitSchema,
        UnitCreate,
        UnitUpdate,
        TopicSchema,
        TopicCreate,
        TopicUpdate,
        LearningOutcomeSchema,
        LearningOutcomeCreate,
        LearningOutcomeUpdate,
        FacultySubjectAssignmentResponse,
        FacultySubjectAssignmentCreate,
    )
    from app.db.models import User
except ImportError:
    from backend.app.api.deps import (
        get_db,
        get_current_user,
        require_admin,
        require_admin_or_faculty
    )
    from backend.app.services.academic_service import AcademicService
    from backend.app.schemas.academic import (
        DepartmentSchema,
        DepartmentCreate,
        DepartmentUpdate,
        CourseSchema,
        CourseCreate,
        CourseUpdate,
        SemesterSchema,
        SemesterCreate,
        AcademicYearSchema,
        AcademicYearCreate,
        SubjectSchema,
        SubjectCreate,
        SubjectUpdate,
        UnitSchema,
        UnitCreate,
        UnitUpdate,
        TopicSchema,
        TopicCreate,
        TopicUpdate,
        LearningOutcomeSchema,
        LearningOutcomeCreate,
        LearningOutcomeUpdate,
        FacultySubjectAssignmentResponse,
        FacultySubjectAssignmentCreate,
    )
    from backend.app.db.models import User

router = APIRouter(prefix="/academic", tags=["Academic Hierarchy"])


# --- Departments ---
@router.get("/departments", response_model=None)
def list_departments(
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = AcademicService(db)
    items = service.list_departments(is_active)
    return {"success": True, "data": [DepartmentSchema.model_validate(d) for d in items]}


@router.post("/departments", response_model=None)
def create_department(
    data: DepartmentCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    service = AcademicService(db)
    created = service.create_department(data, admin.id)
    return {"success": True, "data": DepartmentSchema.model_validate(created)}


@router.get("/departments/{dept_id}", response_model=None)
def get_department(
    dept_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = AcademicService(db)
    dept = service.get_department(dept_id)
    return {"success": True, "data": DepartmentSchema.model_validate(dept)}


@router.patch("/departments/{dept_id}", response_model=None)
def update_department(
    dept_id: str,
    data: DepartmentUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    service = AcademicService(db)
    updated = service.update_department(dept_id, data, admin.id)
    return {"success": True, "data": DepartmentSchema.model_validate(updated)}


# --- Courses ---
@router.get("/courses", response_model=None)
def list_courses(
    department_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = AcademicService(db)
    items = service.list_courses(department_id, is_active)
    return {"success": True, "data": [CourseSchema.model_validate(c) for c in items]}


@router.post("/courses", response_model=None)
def create_course(
    data: CourseCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    service = AcademicService(db)
    created = service.create_course(data, admin.id)
    return {"success": True, "data": CourseSchema.model_validate(created)}


@router.get("/courses/{course_id}", response_model=None)
def get_course(
    course_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = AcademicService(db)
    course = service.get_course(course_id)
    return {"success": True, "data": CourseSchema.model_validate(course)}


@router.patch("/courses/{course_id}", response_model=None)
def update_course(
    course_id: str,
    data: CourseUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    service = AcademicService(db)
    updated = service.update_course(course_id, data, admin.id)
    return {"success": True, "data": CourseSchema.model_validate(updated)}


# --- Semesters & Academic Years ---
@router.get("/semesters", response_model=None)
def list_semesters(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = AcademicService(db)
    items = service.list_semesters()
    return {"success": True, "data": [SemesterSchema.model_validate(s) for s in items]}


@router.post("/semesters", response_model=None)
def create_semester(
    data: SemesterCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    service = AcademicService(db)
    created = service.create_semester(data, admin.id)
    return {"success": True, "data": SemesterSchema.model_validate(created)}


@router.get("/years", response_model=None)
def list_academic_years(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = AcademicService(db)
    items = service.list_academic_years()
    return {"success": True, "data": [AcademicYearSchema.model_validate(y) for y in items]}


@router.post("/years", response_model=None)
def create_academic_year(
    data: AcademicYearCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    service = AcademicService(db)
    created = service.create_academic_year(data, admin.id)
    return {"success": True, "data": AcademicYearSchema.model_validate(created)}


# --- Subjects ---
@router.get("/subjects", response_model=None)
def list_subjects(
    department_id: Optional[str] = Query(None),
    course_id: Optional[str] = Query(None),
    semester_id: Optional[str] = Query(None),
    academic_year_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = AcademicService(db)
    items = service.list_subjects(
        current_user,
        department_id=department_id,
        course_id=course_id,
        semester_id=semester_id,
        academic_year_id=academic_year_id,
        is_active=is_active,
        search=search
    )
    return {"success": True, "data": [SubjectSchema.model_validate(s) for s in items]}


@router.post("/subjects", response_model=None)
def create_subject(
    data: SubjectCreate,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = AcademicService(db)
    created = service.create_subject(data, user)
    return {"success": True, "data": SubjectSchema.model_validate(created)}


@router.get("/subjects/{subject_id}", response_model=None)
def get_subject(
    subject_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = AcademicService(db)
    subject = service.get_subject(subject_id, current_user)
    return {"success": True, "data": SubjectSchema.model_validate(subject)}


@router.patch("/subjects/{subject_id}", response_model=None)
def update_subject(
    subject_id: str,
    data: SubjectUpdate,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = AcademicService(db)
    updated = service.update_subject(subject_id, data, user)
    return {"success": True, "data": SubjectSchema.model_validate(updated)}


# --- Units, Topics, Learning Outcomes ---
@router.post("/subjects/{subject_id}/units", response_model=None)
def create_unit(
    subject_id: str,
    data: UnitCreate,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = AcademicService(db)
    created = service.create_unit(subject_id, data, user)
    return {"success": True, "data": UnitSchema.model_validate(created)}


@router.patch("/units/{unit_id}", response_model=None)
def update_unit(
    unit_id: str,
    data: UnitUpdate,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = AcademicService(db)
    updated = service.update_unit(unit_id, data, user)
    return {"success": True, "data": UnitSchema.model_validate(updated)}


@router.post("/units/{unit_id}/topics", response_model=None)
def create_topic(
    unit_id: str,
    data: TopicCreate,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = AcademicService(db)
    created = service.create_topic(unit_id, data, user)
    return {"success": True, "data": TopicSchema.model_validate(created)}


@router.patch("/topics/{topic_id}", response_model=None)
def update_topic(
    topic_id: str,
    data: TopicUpdate,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = AcademicService(db)
    updated = service.update_topic(topic_id, data, user)
    return {"success": True, "data": TopicSchema.model_validate(updated)}


@router.post("/subjects/{subject_id}/learning-outcomes", response_model=None)
def create_learning_outcome(
    subject_id: str,
    data: LearningOutcomeCreate,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = AcademicService(db)
    created = service.create_learning_outcome(subject_id, data, user)
    return {"success": True, "data": LearningOutcomeSchema.model_validate(created)}


@router.patch("/learning-outcomes/{lo_id}", response_model=None)
def update_learning_outcome(
    lo_id: str,
    data: LearningOutcomeUpdate,
    user: User = Depends(require_admin_or_faculty),
    db: Session = Depends(get_db)
):
    service = AcademicService(db)
    updated = service.update_learning_outcome(lo_id, data, user)
    return {"success": True, "data": LearningOutcomeSchema.model_validate(updated)}


# --- Faculty Subject Assignments ---
@router.get("/faculty-assignments", response_model=None)
def list_faculty_assignments(
    faculty_id: Optional[str] = Query(None),
    subject_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = AcademicService(db)
    items = service.list_faculty_assignments(faculty_id, subject_id)
    return {"success": True, "data": [FacultySubjectAssignmentResponse.model_validate(a) for a in items]}


@router.post("/faculty-assignments", response_model=None)
def assign_faculty(
    data: FacultySubjectAssignmentCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    service = AcademicService(db)
    created = service.assign_faculty_to_subject(data, admin.id)
    return {"success": True, "data": FacultySubjectAssignmentResponse.model_validate(created)}
