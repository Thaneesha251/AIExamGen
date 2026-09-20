from fastapi import APIRouter

try:
    from app.api.v1.routes import health, auth, users, academic, syllabus, questions, question_banks, blueprints, question_papers, answer_keys, rubrics, question_paper_reviews, answer_papers, evaluations, plagiarism, analytics, question_quality
except ImportError:
    from backend.app.api.v1.routes import health, auth, users, academic, syllabus, questions, question_banks, blueprints, question_papers, answer_keys, rubrics, question_paper_reviews, answer_papers, evaluations, plagiarism, analytics, question_quality

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health & System"])
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(academic.router)
api_router.include_router(syllabus.router)
api_router.include_router(questions.router)
api_router.include_router(question_banks.router)
api_router.include_router(blueprints.router)
api_router.include_router(question_papers.router)
api_router.include_router(answer_keys.router)
api_router.include_router(rubrics.router)
api_router.include_router(question_paper_reviews.router)
api_router.include_router(answer_papers.router)
api_router.include_router(evaluations.router)
api_router.include_router(plagiarism.router)
api_router.include_router(analytics.router)
api_router.include_router(question_quality.router)





