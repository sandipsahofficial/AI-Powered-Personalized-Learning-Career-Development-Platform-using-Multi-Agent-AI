from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    system,
    auth,
    users,
    profiles,
    skills,
    profiling,
    careers,
    roadmaps,
    assessments,
    mentor
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health & Infrastructure"])
api_router.include_router(system.router, prefix="/system", tags=["System Telemetry"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Session"])
api_router.include_router(users.router, prefix="/users", tags=["User Management"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["Profile Management"])
api_router.include_router(skills.router, prefix="/skills", tags=["Skills Catalog & Management"])
api_router.include_router(profiling.router, prefix="/profiling", tags=["AI Profiling & Skill Extraction"])
api_router.include_router(careers.router, prefix="/careers", tags=["Career Intelligence & Gap Analysis"])
api_router.include_router(roadmaps.router, prefix="/roadmaps", tags=["Personalized Learning Roadmaps"])
api_router.include_router(assessments.router, prefix="/assessments", tags=["Assessments & Adaptive Replanning"])
api_router.include_router(mentor.router, prefix="/mentor", tags=["AI Career Mentorship"])
