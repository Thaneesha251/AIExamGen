import { apiClient } from './api';
import { Subject, Unit, Topic, LearningOutcome, AcademicHierarchy } from '../types/academic';

export type { Subject, Unit, Topic, LearningOutcome, AcademicHierarchy };

export const academicService = {
  getSubjects: async (): Promise<Subject[]> => {
    const res = await apiClient.get('/academic/subjects');
    return res.data.data;
  },

  getUnitsBySubject: async (subjectId: string): Promise<Unit[]> => {
    const res = await apiClient.get(`/academic/subjects/${subjectId}/units`);
    return res.data.data;
  },

  getTopicsByUnit: async (unitId: string): Promise<Topic[]> => {
    const res = await apiClient.get(`/academic/units/${unitId}/topics`);
    return res.data.data;
  },

  getLearningOutcomesBySubject: async (subjectId: string): Promise<LearningOutcome[]> => {
    const res = await apiClient.get(`/academic/subjects/${subjectId}/learning-outcomes`);
    return res.data.data;
  },

  getAcademicHierarchy: async (subjectId: string): Promise<AcademicHierarchy> => {
    const [units, learning_outcomes, subjects] = await Promise.all([
      academicService.getUnitsBySubject(subjectId),
      academicService.getLearningOutcomesBySubject(subjectId),
      academicService.getSubjects(),
    ]);
    const subject = subjects.find((s) => s.id === subjectId) || {
      id: subjectId,
      course_id: '',
      name: 'Subject',
      code: 'SUBJ',
      semester_number: 1,
      credits: 4,
      is_active: true,
    };

    // Attach topics to each unit
    const unitsWithTopics = await Promise.all(
      units.map(async (u) => {
        try {
          const topics = await academicService.getTopicsByUnit(u.id);
          return { ...u, topics };
        } catch {
          return { ...u, topics: [] };
        }
      })
    );

    return {
      subject,
      units: unitsWithTopics,
      learning_outcomes,
    };
  },
};
