from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from backend.app.db.models.enums import BloomLevelEnum

# --- Department Schemas ---
class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    is_active: bool = True

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class DepartmentSchema(DepartmentBase):
    id: str
    model_config = ConfigDict(from_attributes=True)

class DepartmentResponse(DepartmentSchema):
    pass


# --- Course Schemas ---
class CourseBase(BaseModel):
    department_id: str
    name: str = Field(..., min_length=1, max_length=150)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    duration_years: int = Field(4, ge=1, le=6)
    is_active: bool = True

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    department_id: Optional[str] = None
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    duration_years: Optional[int] = Field(None, ge=1, le=6)
    is_active: Optional[bool] = None

class CourseSchema(CourseBase):
    id: str
    department: Optional[DepartmentSchema] = None
    model_config = ConfigDict(from_attributes=True)

class CourseResponse(CourseSchema):
    pass


# --- Semester Schemas ---
class SemesterBase(BaseModel):
    number: int = Field(..., ge=1, le=12)
    name: str = Field(..., min_length=1, max_length=50)

class SemesterCreate(SemesterBase):
    pass

class SemesterUpdate(BaseModel):
    number: Optional[int] = Field(None, ge=1, le=12)
    name: Optional[str] = Field(None, min_length=1, max_length=50)

class SemesterSchema(SemesterBase):
    id: str
    model_config = ConfigDict(from_attributes=True)


# --- Academic Year Schemas ---
class AcademicYearBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50) # e.g. "2026-2027"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False

class AcademicYearCreate(AcademicYearBase):
    pass

class AcademicYearUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: Optional[bool] = None

class AcademicYearSchema(AcademicYearBase):
    id: str
    model_config = ConfigDict(from_attributes=True)


# --- Topic Schemas ---
class TopicBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    keywords: Optional[str] = None
    importance: Optional[str] = "MEDIUM"

class TopicCreate(TopicBase):
    unit_id: Optional[str] = None

class TopicUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    keywords: Optional[str] = None
    importance: Optional[str] = None

class TopicSchema(TopicBase):
    id: str
    unit_id: str
    model_config = ConfigDict(from_attributes=True)


# --- Unit Schemas ---
class UnitBase(BaseModel):
    unit_number: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    weightage: Optional[float] = None

class UnitCreate(UnitBase):
    subject_id: Optional[str] = None

class UnitUpdate(BaseModel):
    unit_number: Optional[int] = Field(None, ge=1)
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    weightage: Optional[float] = None

class UnitSchema(UnitBase):
    id: str
    subject_id: str
    topics: List[TopicSchema] = []
    model_config = ConfigDict(from_attributes=True)


# --- Learning Outcome Schemas ---
class LearningOutcomeBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50) # e.g. "CO1"
    description: str = Field(..., min_length=1)
    bloom_level: BloomLevelEnum = BloomLevelEnum.UNDERSTAND

class LearningOutcomeCreate(LearningOutcomeBase):
    subject_id: Optional[str] = None

class LearningOutcomeUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, min_length=1)
    bloom_level: Optional[BloomLevelEnum] = None

class LearningOutcomeSchema(LearningOutcomeBase):
    id: str
    subject_id: str
    model_config = ConfigDict(from_attributes=True)


# --- Subject Schemas ---
class SubjectBase(BaseModel):
    course_id: str
    department_id: Optional[str] = None
    semester_id: str
    academic_year_id: Optional[str] = None
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = None
    credits: int = Field(4, ge=1, le=10)
    total_units: int = Field(5, ge=1, le=10)
    is_active: bool = True

class SubjectCreate(SubjectBase):
    pass

class SubjectUpdate(BaseModel):
    course_id: Optional[str] = None
    department_id: Optional[str] = None
    semester_id: Optional[str] = None
    academic_year_id: Optional[str] = None
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = None
    credits: Optional[int] = Field(None, ge=1, le=10)
    total_units: Optional[int] = Field(None, ge=1, le=10)
    is_active: Optional[bool] = None

class SubjectSchema(SubjectBase):
    id: str
    created_by: Optional[str] = None
    course: Optional[CourseSchema] = None
    department: Optional[DepartmentSchema] = None
    semester: Optional[SemesterSchema] = None
    academic_year: Optional[AcademicYearSchema] = None
    units: List[UnitSchema] = []
    learning_outcomes: List[LearningOutcomeSchema] = []

    model_config = ConfigDict(from_attributes=True)


# --- Faculty Subject Assignment Schemas ---
class FacultySubjectAssignmentCreate(BaseModel):
    faculty_id: str
    subject_id: str
    academic_year_id: Optional[str] = None
    is_active: bool = True

class FacultySubjectAssignmentResponse(BaseModel):
    id: str
    faculty_id: str
    subject_id: str
    academic_year_id: Optional[str] = None
    is_active: bool
    subject: Optional[SubjectSchema] = None

    model_config = ConfigDict(from_attributes=True)
