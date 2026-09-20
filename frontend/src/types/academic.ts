export interface Department {
  id: string;
  name: string;
  code: string;
  description?: string;
  is_active: boolean;
}

export interface Course {
  id: string;
  department_id: string;
  name: string;
  code: string;
  degree_level: string;
  total_semesters: number;
  is_active: boolean;
}

export interface Subject {
  id: string;
  course_id: string;
  name: string;
  code: string;
  semester_number: number;
  credits: number;
  is_active: boolean;
}

export interface Topic {
  id: string;
  unit_id: string;
  name: string;
  description?: string;
  keywords?: string[];
}

export interface Unit {
  id: string;
  subject_id: string;
  unit_number: number;
  title: string;
  description?: string;
  weightage?: number;
  topics?: Topic[];
}

export interface LearningOutcome {
  id: string;
  subject_id: string;
  code: string;
  description: string;
  bloom_level: string;
}

export interface AcademicHierarchy {
  subject: Subject;
  units: Unit[];
  learning_outcomes: LearningOutcome[];
}
