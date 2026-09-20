from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class BaseLLMProvider(ABC):
    """Abstract interface for modular, replaceable LLM providers."""
    
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Generate plain text response from LLM provider."""
        pass
        
    @abstractmethod
    async def generate_structured(self, prompt: str, response_schema: Optional[Dict[str, Any]] = None, system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate structured JSON response following a strict schema."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify LLM service availability."""
        pass


class MockLLMProvider(BaseLLMProvider):
    """Fallback mock LLM provider for local development without external API keys."""
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        return f"[Mock LLM Response for prompt: '{prompt[:50]}...']"
        
    async def generate_structured(self, prompt: str, response_schema: Optional[Dict[str, Any]] = None, system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        # Inspect kwargs or prompt to synthesize appropriate mock data
        question_type = kwargs.get("question_type", "SHORT_ANSWER")
        difficulty = kwargs.get("difficulty", "MEDIUM")
        bloom_level = kwargs.get("bloom_level", "UNDERSTAND")
        marks = kwargs.get("marks", 5.0)
        count = kwargs.get("count", 3)
        topic_name = kwargs.get("topic_name", "Academic Topic")
        subject_name = kwargs.get("subject_name", "Subject")

        stems_mcq = [
            f"Which of the following primary architectural components defines {topic_name} in {subject_name}?",
            f"What is the main advantage of applying {topic_name} mechanisms during system design?",
            f"Identify the incorrect statement regarding the theoretical properties of {topic_name}.",
            f"How does {topic_name} handle unexpected operational state transitions?",
            f"Which metric is most suitable for evaluating performance in {topic_name}?"
        ]
        stems_text = [
            f"Explain the fundamental working principles and core architecture of {topic_name}.",
            f"Compare and contrast the operational characteristics of {topic_name} with traditional methodologies.",
            f"Discuss the practical applications and limitations of {topic_name} in enterprise software.",
            f"Describe how error recovery and fault tolerance are guaranteed within {topic_name}.",
            f"Analyze the trade-offs involved when optimizing {topic_name} for memory efficiency."
        ]

        questions: List[Dict[str, Any]] = []
        for i in range(1, count + 1):
            stem_idx = (i - 1) % len(stems_mcq)
            if question_type == "MCQ":
                q_text = stems_mcq[stem_idx]
                q_dict = {
                    "question_text": q_text,
                    "question_type": "MCQ",
                    "marks": marks,
                    "difficulty": difficulty,
                    "bloom_level": bloom_level,
                    "expected_answer": f"Option A: Standard definition for {topic_name}",
                    "options": {
                        "options": [
                            f"Option A: Correct specification for {topic_name}",
                            f"Option B: Invalid assertion regarding concept {i}",
                            f"Option C: Non-standard variant of {topic_name}",
                            f"Option D: Contradictory assertion for concept {i}"
                        ],
                        "correct_option": f"Option A: Correct specification for {topic_name}",
                        "explanation": f"Option A accurately reflects the standard definitions established in {topic_name}."
                    },
                    "keywords": [topic_name.lower(), "concept", f"aspect_{i}"],
                    "concepts": [topic_name, subject_name]
                }
            else: # SHORT_ANSWER, LONG_ANSWER, ESSAY, NUMERICAL, CODE
                q_text = stems_text[stem_idx]
                q_dict = {
                    "question_text": q_text,
                    "question_type": question_type,
                    "marks": marks,
                    "difficulty": difficulty,
                    "bloom_level": bloom_level,
                    "expected_answer": f"The key principle of {topic_name} is to ensure system integrity through structured execution.",
                    "options": None,
                    "keywords": [topic_name.lower(), "principles", f"concept_{i}"],
                    "concepts": [topic_name, subject_name]
                }
            questions.append(q_dict)

        return {
            "status": "success",
            "mock": True,
            "questions": questions
        }

    async def health_check(self) -> bool:
        return True


def get_llm_provider(provider_type: str = "mock", **kwargs) -> BaseLLMProvider:
    """Factory function to instantiate the configured LLM provider."""
    provider_type = provider_type.lower()
    if provider_type == "mock":
        return MockLLMProvider()
    return MockLLMProvider()
