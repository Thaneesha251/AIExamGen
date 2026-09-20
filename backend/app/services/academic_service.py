from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

try:
    from app.repositories.academic_repository import AcademicRepository
    from app.db.models import (
        User,
        RoleEnum,
        Department,
        Course,
        Semester,
        AcademicYear,
        Subject,
        Unit,
        Topic,
        LearningOutcome,
        FacultySubjectAssignment,
        AuditLog,
        AuditActionEnum,
    )
    from app.schemas.academic import (
        DepartmentCreate,
        DepartmentUpdate,
        CourseCreate,
        CourseUpdate,
        SemesterCreate,
        AcademicYearCreate,
        SubjectCreate,
        SubjectUpdate,
        UnitCreate,
        UnitUpdate,
        TopicCreate,
        TopicUpdate,
        LearningOutcomeCreate,
        LearningOutcomeUpdate,
        FacultySubjectAssignmentCreate,
    )
except ImportError:
    from backend.app.repositories.academic_repository import AcademicRepository
    from backend.app.db.models import (
        User,
        RoleEnum,
        Department,
        Course,
        Semester,
        AcademicYear,
        Subject,
        Unit,
        Topic,
        LearningOutcome,
        FacultySubjectAssignment,
        AuditLog,
        AuditActionEnum,
    )
    from backend.app.schemas.academic import (
        DepartmentCreate,
        DepartmentUpdate,
        CourseCreate,
        CourseUpdate,
        SemesterCreate,
        AcademicYearCreate,
        SubjectCreate,
        SubjectUpdate,
        UnitCreate,
        UnitUpdate,
        TopicCreate,
        TopicUpdate,
        LearningOutcomeCreate,
        LearningOutcomeUpdate,
        FacultySubjectAssignmentCreate,
    )


class AcademicService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AcademicRepository(db)

    def _log_audit(
        self,
        action: AuditActionEnum,
        user_id: Optional[str] = None,
        entity_type: str = "Subject",
        entity_id: Optional[str] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
    ):
        try:
            audit = AuditLog(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                old_values=old_values,
                new_values=new_values,
            )
            self.db.add(audit)
            self.db.commit()
        except Exception:
            self.db.rollback()

    def verify_subject_access(self, user: User, subject_id: str, is_write_operation: bool = False):
        if not user.role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role unassigned")

        role_name = user.role.name

        if role_name == RoleEnum.ADMIN:
            return # Admin has full global access

        if role_name == RoleEnum.STUDENT:
            if is_write_operation:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Students do not have permission to modify academic structure"
                )
            return # Read-only for students

        if role_name == RoleEnum.FACULTY:
            # Check subject-level authorization
            is_authorized = self.repo.is_faculty_assigned_to_subject(user.id, subject_id)
            if not is_authorized:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You are not authorized to manage content for this subject"
                )

    # --- Departments ---
    def create_department(self, data: DepartmentCreate, user_id: str) -> Department:
        if self.repo.get_department_by_code(data.code):
            raise HTTPException(status_code=400, detail=f"Department code '{data.code}' already exists")
        dept = Department(**data.model_dump())
        created = self.repo.create_department(dept)
        self._log_audit(AuditActionEnum.ACADEMIC_STRUCTURE_CREATED, user_id, "Department", created.id, new_values=data.model_dump())
        return created

    def update_department(self, dept_id: str, data: DepartmentUpdate, user_id: str) -> Department:
        dept = self.repo.get_department_by_id(dept_id)
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")
        for key, val in data.model_dump(exclude_unset=True).items():
            setattr(dept, key, val)
        updated = self.repo.update_department(dept)
        self._log_audit(AuditActionEnum.ACADEMIC_STRUCTURE_UPDATED, user_id, "Department", updated.id, new_values=data.model_dump(exclude_unset=True))
        return updated

    def list_departments(self, is_active: Optional[bool] = None) -> List[Department]:
        return self.repo.list_departments(is_active)

    def get_department(self, dept_id: str) -> Department:
        dept = self.repo.get_department_by_id(dept_id)
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")
        return dept

    # --- Courses ---
    def create_course(self, data: CourseCreate, user_id: str) -> Course:
        if self.repo.get_course_by_code(data.code):
            raise HTTPException(status_code=400, detail=f"Course code '{data.code}' already exists")
        course = Course(**data.model_dump())
        created = self.repo.create_course(course)
        self._log_audit(AuditActionEnum.ACADEMIC_STRUCTURE_CREATED, user_id, "Course", created.id, new_values=data.model_dump())
        return created

    def update_course(self, course_id: str, data: CourseUpdate, user_id: str) -> Course:
        course = self.repo.get_course_by_id(course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        for key, val in data.model_dump(exclude_unset=True).items():
            setattr(course, key, val)
        updated = self.repo.update_course(course)
        self._log_audit(AuditActionEnum.ACADEMIC_STRUCTURE_UPDATED, user_id, "Course", updated.id, new_values=data.model_dump(exclude_unset=True))
        return updated

    def list_courses(self, department_id: Optional[str] = None, is_active: Optional[bool] = None) -> List[Course]:
        return self.repo.list_courses(department_id, is_active)

    def get_course(self, course_id: str) -> Course:
        course = self.repo.get_course_by_id(course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return course

    # --- Semesters & Academic Years ---
    def list_semesters(self) -> List[Semester]:
        return self.repo.list_semesters()

    def create_semester(self, data: SemesterCreate, user_id: str) -> Semester:
        sem = Semester(**data.model_dump())
        return self.repo.create_semester(sem)

    def list_academic_years(self) -> List[AcademicYear]:
        return self.repo.list_academic_years()

    def create_academic_year(self, data: AcademicYearCreate, user_id: str) -> AcademicYear:
        year = AcademicYear(**data.model_dump())
        return self.repo.create_academic_year(year)

    # --- Subjects ---
    def create_subject(self, data: SubjectCreate, user: User) -> Subject:
        existing = self.repo.get_subject_by_code(data.code)
        if existing and existing.course_id == data.course_id:
            raise HTTPException(status_code=400, detail=f"Subject code '{data.code}' already exists in this course")
        subject = Subject(**data.model_dump(), created_by=user.id)
        created = self.repo.create_subject(subject)
        
        # Auto-assign creating faculty if created by a FACULTY member
        if user.role and user.role.name == RoleEnum.FACULTY:
            assignment = FacultySubjectAssignment(
                faculty_id=user.id,
                subject_id=created.id,
                academic_year_id=created.academic_year_id,
                is_active=True
            )
            self.repo.create_faculty_assignment(assignment)

        self._log_audit(AuditActionEnum.ACADEMIC_STRUCTURE_CREATED, user.id, "Subject", created.id, new_values=data.model_dump())
        return created

    def update_subject(self, subject_id: str, data: SubjectUpdate, user: User) -> Subject:
        self.verify_subject_access(user, subject_id, is_write_operation=True)
        subject = self.repo.get_subject_by_id(subject_id)
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        for key, val in data.model_dump(exclude_unset=True).items():
            setattr(subject, key, val)
        updated = self.repo.update_subject(subject)
        self._log_audit(AuditActionEnum.ACADEMIC_STRUCTURE_UPDATED, user.id, "Subject", updated.id, new_values=data.model_dump(exclude_unset=True))
        return updated

    def list_subjects(
        self,
        user: User,
        department_id: Optional[str] = None,
        course_id: Optional[str] = None,
        semester_id: Optional[str] = None,
        academic_year_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> List[Subject]:
        all_subjects = self.repo.list_subjects(
            department_id=department_id,
            course_id=course_id,
            semester_id=semester_id,
            academic_year_id=academic_year_id,
            is_active=is_active,
            search=search
        )
        
        # Filter for FACULTY role if asking for assigned subjects
        if user.role and user.role.name == RoleEnum.FACULTY:
            # Keep subjects created by or assigned to faculty
            assigned = self.repo.list_faculty_assignments(faculty_id=user.id)
            assigned_subject_ids = {a.subject_id for a in assigned}
            return [s for s in all_subjects if s.created_by == user.id or s.id in assigned_subject_ids]

        return all_subjects

    def get_subject(self, subject_id: str, user: User) -> Subject:
        self.verify_subject_access(user, subject_id, is_write_operation=False)
        subject = self.repo.get_subject_by_id(subject_id)
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        return subject

    # --- Units & Topics ---
    def create_unit(self, subject_id: str, data: UnitCreate, user: User) -> Unit:
        self.verify_subject_access(user, subject_id, is_write_operation=True)
        unit = Unit(**data.model_dump(), subject_id=subject_id)
        created = self.repo.create_unit(unit)
        self._log_audit(AuditActionEnum.ACADEMIC_STRUCTURE_CREATED, user.id, "Unit", created.id, new_values=data.model_dump())
        return created

    def update_unit(self, unit_id: str, data: UnitUpdate, user: User) -> Unit:
        unit = self.repo.get_unit_by_id(unit_id)
        if not unit:
            raise HTTPException(status_code=404, detail="Unit not found")
        self.verify_subject_access(user, unit.subject_id, is_write_operation=True)
        for key, val in data.model_dump(exclude_unset=True).items():
            setattr(unit, key, val)
        updated = self.repo.update_unit(unit)
        self._log_audit(AuditActionEnum.ACADEMIC_STRUCTURE_UPDATED, user.id, "Unit", updated.id, new_values=data.model_dump(exclude_unset=True))
        return updated

    def create_topic(self, unit_id: str, data: TopicCreate, user: User) -> Topic:
        unit = self.repo.get_unit_by_id(unit_id)
        if not unit:
            raise HTTPException(status_code=404, detail="Unit not found")
        self.verify_subject_access(user, unit.subject_id, is_write_operation=True)
        topic = Topic(**data.model_dump(), unit_id=unit_id)
        created = self.repo.create_topic(topic)
        self._log_audit(AuditActionEnum.ACADEMIC_STRUCTURE_CREATED, user.id, "Topic", created.id, new_values=data.model_dump())
        return created

    def update_topic(self, topic_id: str, data: TopicUpdate, user: User) -> Topic:
        topic = self.repo.get_topic_by_id(topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        unit = self.repo.get_unit_by_id(topic.unit_id)
        if unit:
            self.verify_subject_access(user, unit.subject_id, is_write_operation=True)
        for key, val in data.model_dump(exclude_unset=True).items():
            setattr(topic, key, val)
        updated = self.repo.update_topic(topic)
        self._log_audit(AuditActionEnum.ACADEMIC_STRUCTURE_UPDATED, user.id, "Topic", updated.id, new_values=data.model_dump(exclude_unset=True))
        return updated

    # --- Learning Outcomes ---
    def create_learning_outcome(self, subject_id: str, data: LearningOutcomeCreate, user: User) -> LearningOutcome:
        self.verify_subject_access(user, subject_id, is_write_operation=True)
        lo = LearningOutcome(**data.model_dump(), subject_id=subject_id)
        created = self.repo.create_learning_outcome(lo)
        self._log_audit(AuditActionEnum.ACADEMIC_STRUCTURE_CREATED, user.id, "LearningOutcome", created.id, new_values=data.model_dump())
        return created

    def update_learning_outcome(self, lo_id: str, data: LearningOutcomeUpdate, user: User) -> LearningOutcome:
        lo = self.repo.get_learning_outcome_by_id(lo_id)
        if not lo:
            raise HTTPException(status_code=404, detail="Learning Outcome not found")
        self.verify_subject_access(user, lo.subject_id, is_write_operation=True)
        for key, val in data.model_dump(exclude_unset=True).items():
            setattr(lo, key, val)
        updated = self.repo.update_learning_outcome(lo)
        self._log_audit(AuditActionEnum.ACADEMIC_STRUCTURE_UPDATED, user.id, "LearningOutcome", updated.id, new_values=data.model_dump(exclude_unset=True))
        return updated

    # --- Faculty Assignments ---
    def assign_faculty_to_subject(self, data: FacultySubjectAssignmentCreate, admin_id: str) -> FacultySubjectAssignment:
        assignment = FacultySubjectAssignment(**data.model_dump())
        created = self.repo.create_faculty_assignment(assignment)
        self._log_audit(AuditActionEnum.ACADEMIC_STRUCTURE_CREATED, admin_id, "FacultySubjectAssignment", created.id, new_values=data.model_dump())
        return created

    def list_faculty_assignments(self, faculty_id: Optional[str] = None, subject_id: Optional[str] = None) -> List[FacultySubjectAssignment]:
        return self.repo.list_faculty_assignments(faculty_id, subject_id)
