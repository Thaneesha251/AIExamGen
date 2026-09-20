"""
AI Question Generation Agent.
Uses PromptService and BaseLLMProvider to generate structured academic questions.
"""

from typing import List, Dict, Any, Optional
from ai.services.prompt_service import PromptService
from ai.services.llm_service import BaseLLMProvider, get_llm_provider
from backend.app.schemas.question_generation import QuestionGenerationRequest, GeneratedQuestionSchema

class QuestionGenerationAgent:
    """Agent responsible for preparing prompts and orchestrating LLM question generation."""

    def __init__(self, provider: Optional[BaseLLMProvider] = None):
        self.provider = provider or get_llm_provider("mock")

    async def generate_questions(
        self,
        req: QuestionGenerationRequest,
        subject_name: str,
        unit_name: Optional[str] = None,
        topic_name: Optional[str] = None,
        learning_outcome_code: Optional[str] = None,
        learning_outcome_desc: Optional[str] = None
    ) -> List[GeneratedQuestionSchema]:
        """Generates structured question schemas for requested parameters."""
        prompt_data = PromptService.get_question_generation_prompt(
            subject_name=subject_name,
            unit_name=unit_name,
            topic_name=topic_name,
            learning_outcome_code=learning_outcome_code,
            learning_outcome_desc=learning_outcome_desc,
            question_type=req.question_type.value,
            difficulty=req.difficulty.value,
            bloom_level=req.bloom_level.value,
            marks=req.marks,
            count=req.count,
            language=req.language
        )

        response = await self.provider.generate_structured(
            prompt=prompt_data["user_prompt"],
            response_schema={"type": "object", "properties": {"questions": {"type": "array"}}},
            system_prompt=prompt_data["system_prompt"],
            question_type=req.question_type.value,
            difficulty=req.difficulty.value,
            bloom_level=req.bloom_level.value,
            marks=req.marks,
            count=req.count,
            subject_name=subject_name,
            topic_name=topic_name or unit_name or subject_name
        )

        raw_questions = response.get("questions", [])
        results: List[GeneratedQuestionSchema] = []

        for item in raw_questions:
            try:
                q_schema = GeneratedQuestionSchema(
                    question_text=item.get("question_text", ""),
                    question_type=req.question_type,
                    marks=float(item.get("marks", req.marks)),
                    difficulty=req.difficulty,
                    bloom_level=req.bloom_level,
                    expected_answer=item.get("expected_answer"),
                    options=item.get("options"),
                    keywords=item.get("keywords", []),
                    concepts=item.get("concepts", [])
                )
                results.append(q_schema)
            except Exception as e:
                # Log or skip malformed schema item
                continue

        return results
