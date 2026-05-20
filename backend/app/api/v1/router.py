from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    auth,
    chatbot,
    grades,
    groups,
    messages,
    notifications,
    projects,
    references,
    submissions,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(groups.router)
api_router.include_router(projects.router)
api_router.include_router(submissions.router)
api_router.include_router(grades.router)
api_router.include_router(messages.router)
api_router.include_router(notifications.router)
api_router.include_router(chatbot.router)
api_router.include_router(references.router)
