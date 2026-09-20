from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

try:
    from app.db.models import (
        Subject,
        Department,
        Course,
        Semester,
        AcademicYear,
        Unit,
        Topic,
        LearningOutcome,
        FacultySubjectAssignment
    )
except ImportError:
    from backend.app.db.models import (
        Subject,
        Department,
        Course,
        Semester,
        AcademicYear,
        Unit,
        Topic,
        LearningOutcome,
        FacultySubjectAssignment
    )


class AcademicRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Departments ---
    def get_department_by_id(self, dept_id: str) -> Optional[Department]:
        return self.db.query(Department).filter(Department.id == dept_id).first()

    def get_department_by_code(self, code: str) -> Optional[Department]:
        return self.db.query(Department).filter(Department.code == code).first()

    def list_departments(self, is_active: Optional[bool] = None) -> List[Department]:
        query = self.db.query(Department)
        if is_active is not None:
            query = query.filter(Department.is_active == is_active)
        return query.order_by(Department.name).all()

    def create_department(self, dept: Department) -> Department:
        self.db.add(dept)
        self.db.commit()
        self.db.refresh(dept)
        return dept

    def update_department(self, dept: Department) -> Department:
        self.db.commit()
        self.db.refresh(dept)
        return dept

    # --- Courses ---
    def get_course_by_id(self, course_id: str) -> Optional[Course]:
        return (
            self.db.query(Course)
            .options(joinedload(Course.department))
            .filter(Course.id == course_id)
            .first()
        )

    def get_course_by_code(self, code: str) -> Optional[Course]:
        return self.db.query(Course).filter(Course.code == code).first()

    def list_courses(self, department_id: Optional[str] = None, is_active: Optional[bool] = None) -> List[Course]:
        query = self.db.query(Course).options(joinedload(Course.department))
        if department_id:
            query = query.filter(Course.department_id == department_id)
        if is_active is not None:
            query = query.filter(Course.is_active == is_active)
        return query.order_by(Course.code).all()

    def create_course(self, course: Course) -> Course:
        self.db.add(course)
        self.db.commit()
        self.db.refresh(course)
        return self.get_course_by_id(course.id) or course

    def update_course(self, course: Course) -> Course:
        self.db.commit()
        self.db.refresh(course)
        return self.get_course_by_id(course.id) or course

    # --- Semesters & Academic Years ---
    def get_semester_by_id(self, sem_id: str) -> Optional[Semester]:
        return self.db.query(Semester).filter(Semester.id == sem_id).first()

    def list_semesters(self) -> List[Semester]:
        return self.db.query(Semester).order_by(Semester.number).all()

    def create_semester(self, sem: Semester) -> Semester:
        self.db.add(sem)
        self.db.commit()
        self.db.refresh(sem)
        return sem

    def get_academic_year_by_id(self, year_id: str) -> Optional[AcademicYear]:
        return self.db.query(AcademicYear).filter(AcademicYear.id == year_id).first()

    def list_academic_years(self) -> List[AcademicYear]:
        return self.db.query(AcademicYear).order_by(AcademicYear.name.desc()).all()

    def create_academic_year(self, year: AcademicYear) -> AcademicYear:
        self.db.add(year)
        self.db.commit()
        self.db.refresh(year)
        return year

    # --- Subjects ---
    def get_subject_by_id(self, subject_id: str) -> Optional[Subject]:
        return (
            self.db.query(Subject)
            .options(
                joinedload(Subject.course),
                joinedload(Subject.department),
                joinedload(Subject.semester),
                joinedload(Subject.academic_year),
                joinedload(Subject.units).joinedload(Unit.topics),
                joinedload(Subject.learning_outcomes),
            )
            .filter(Subject.id == subject_id)
            .first()
        )

    def get_subject_by_code(self, code: str) -> Optional[Subject]:
        return self.db.query(Subject).filter(Subject.code == code).first()

    def list_subjects(
        self,
        department_id: Optional[str] = None,
        course_id: Optional[str] = None,
        semester_id: Optional[str] = None,
        academic_year_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> List[Subject]:
        query = self.db.query(Subject).options(
            joinedload(Subject.course),
            joinedload(Subject.department),
            joinedload(Subject.semester),
            joinedload(Subject.academic_year),
            joinedload(Subject.units),
            joinedload(Subject.learning_outcomes),
        )

        if department_id:
            query = query.filter(Subject.department_id == department_id)
        if course_id:
            query = query.filter(Subject.course_id == course_id)
        if semester_id:
            query = query.filter(Subject.semester_id == semester_id)
        if academic_year_id:
            query = query.filter(Subject.academic_year_id == academic_year_id)
        if is_active is not None:
            query = query.filter(Subject.is_active == is_active)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(or_(Subject.name.ilike(pattern), Subject.code.ilike(pattern)))

        return query.order_by(Subject.code).all()

    def create_subject(self, subject: Subject) -> Subject:
        self.db.add(subject)
        self.db.commit()
        self.db.refresh(subject)
        return self.get_subject_by_id(subject.id) or subject

    def update_subject(self, subject: Subject) -> Subject:
        self.db.commit()
        self.db.refresh(subject)
        return self.get_subject_by_id(subject.id) or subject

    # --- Units, Topics, Learning Outcomes ---
    def get_unit_by_id(self, unit_id: str) -> Optional[Unit]:
        return (
            self.db.query(Unit)
            .options(joinedload(Unit.topics))
            .filter(Unit.id == unit_id)
            .first()
        )

    def list_units_by_subject(self, subject_id: str) -> List[Unit]:
        return (
            self.db.query(Unit)
            .options(joinedload(Unit.topics))
            .filter(Unit.subject_id == subject_id)
            .order_by(Unit.unit_number)
            .all()
        )

    def create_unit(self, unit: Unit) -> Unit:
        self.db.add(unit)
        self.db.commit()
        self.db.refresh(unit)
        return self.get_unit_by_id(unit.id) or unit

    def update_unit(self, unit: Unit) -> Unit:
        self.db.commit()
        self.db.refresh(unit)
        return self.get_unit_by_id(unit.id) or unit

    def get_topic_by_id(self, topic_id: str) -> Optional[Topic]:
        return self.db.query(Topic).filter(Topic.id == topic_id).first()

    def list_topics_by_unit(self, unit_id: str) -> List[Topic]:
        return self.db.query(Topic).filter(Topic.unit_id == unit_id).all()

    def create_topic(self, topic: Topic) -> Topic:
        self.db.add(topic)
        self.db.commit()
        self.db.refresh(topic)
        return topic

    def update_topic(self, topic: Topic) -> Topic:
        self.db.commit()
        self.db.refresh(topic)
        return topic

    def get_learning_outcome_by_id(self, lo_id: str) -> Optional[LearningOutcome]:
        return self.db.query(LearningOutcome).filter(LearningOutcome.id == lo_id).first()

    def list_learning_outcomes(self, subject_id: str) -> List[LearningOutcome]:
        return self.db.query(LearningOutcome).filter(LearningOutcome.subject_id == subject_id).order_by(LearningOutcome.code).all()

    def create_learning_outcome(self, lo: LearningOutcome) -> LearningOutcome:
        self.db.add(lo)
        self.db.commit()
        self.db.refresh(lo)
        return lo

    def update_learning_outcome(self, lo: LearningOutcome) -> LearningOutcome:
        self.db.commit()
        self.db.refresh(lo)
        return lo

    # --- Faculty Assignments ---
    def list_faculty_assignments(self, faculty_id: Optional[str] = None, subject_id: Optional[str] = None) -> List[FacultySubjectAssignment]:
        query = self.db.query(FacultySubjectAssignment).options(
            joinedload(FacultySubjectAssignment.subject).joinedload(Subject.course),
            joinedload(FacultySubjectAssignment.faculty),
            joinedload(FacultySubjectAssignment.academic_year)
        )
        if faculty_id:
            query = query.filter(FacultySubjectAssignment.faculty_id == faculty_id)
        if subject_id:
            query = query.filter(FacultySubjectAssignment.subject_id == subject_id)
        return query.filter(FacultySubjectAssignment.is_active == True).all()

    def create_faculty_assignment(self, assignment: FacultySubjectAssignment) -> FacultySubjectAssignment:
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def is_faculty_assigned_to_subject(self, faculty_id: str, subject_id: str) -> bool:
        # Check if subject was created by faculty OR assigned via FacultySubjectAssignment
        subj = self.get_subject_by_id(subject_id)
        if subj and subj.created_by == faculty_id:
            return True
        assigned = (
            self.db.query(FacultySubjectAssignment)
            .filter(
                FacultySubjectAssignment.faculty_id == faculty_id,
                FacultySubjectAssignment.subject_id == subject_id,
                FacultySubjectAssignment.is_active == True
            )
            .first()
        )
        return assigned is not None
