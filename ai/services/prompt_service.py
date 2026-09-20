"""
Prompt engineering and template management service for AI ExamGen.
Provides versioned prompt templates for question generation, evaluation, and blueprint creation.
"""

from typing import Dict, Any, Optional

QUESTION_GEN_V1_PROMPT = """
You are an expert academic assessment controller and subject matter specialist.
Generate high-quality assessment questions according to the following strict specifications:

Subject context: {subject_name}
Unit: {unit_name}
Topic: {topic_name}
Learning Outcome: {learning_outcome_code} - {learning_outcome_desc}

Parameters:
- Question Type: {question_type}
- Target Difficulty Level: {difficulty}
- Target Bloom's Taxonomy Level: {bloom_level}
- Target Marks: {marks}
- Quantity to Generate: {count}
- Language: {language}

Requirements:
1. Every question must directly align with the specified Learning Outcome and Topic.
2. For MCQ questions, provide exactly 4 options labeled (A, B, C, D) along with the correct option key and a concise explanation.
3. For SHORT_ANSWER, LONG_ANSWER, NUMERICAL, CODE, or ESSAY questions, provide a clear model answer / expected answer and key evaluation keywords.
4. Ensure appropriate academic depth matching the target Bloom level ({bloom_level}) and difficulty ({difficulty}).

Return your response strictly as JSON with a top-level key "questions" containing an array of question objects matching this structure:
[
  {{
    "question_text": "Question text here...",
    "question_type": "{question_type}",
    "marks": {marks},
    "difficulty": "{difficulty}",
    "bloom_level": "{bloom_level}",
    "expected_answer": "Model answer / correct answer key...",
    "options": {{ "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"], "correct_option": "A) Option 1", "explanation": "Explanation..." }}, // required only if MCQ
    "keywords": ["keyword1", "keyword2"],
    "concepts": ["concept1", "concept2"]
  }}
]
"""

class PromptService:
    @staticmethod
    def get_question_generation_prompt(
        subject_name: str,
        unit_name: Optional[str] = None,
        topic_name: Optional[str] = None,
        learning_outcome_code: Optional[str] = None,
        learning_outcome_desc: Optional[str] = None,
        question_type: str = "SHORT_ANSWER",
        difficulty: str = "MEDIUM",
        bloom_level: str = "UNDERSTAND",
        marks: float = 5.0,
        count: int = 3,
        language: str = "English",
        version: str = "v1"
    ) -> Dict[str, str]:
        """Formats and returns the prompt and system prompt for question generation."""
        system_prompt = (
            "You are an AI Question Generator specialized in university-level examination preparation. "
            "Always produce output that strictly adheres to the requested JSON format."
        )
        
        user_prompt = QUESTION_GEN_V1_PROMPT.format(
            subject_name=subject_name or "General Subject",
            unit_name=unit_name or "General Unit",
            topic_name=topic_name or "General Topic",
            learning_outcome_code=learning_outcome_code or "LO-1",
            learning_outcome_desc=learning_outcome_desc or "Core concept comprehension",
            question_type=str(question_type),
            difficulty=str(difficulty),
            bloom_level=str(bloom_level),
            marks=marks,
            count=count,
            language=language
        )
        
        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "prompt_version": version
        }
