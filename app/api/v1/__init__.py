from fastapi import APIRouter
from app.api.v1 import inventory, project, logistics, kpi, auth, dashboard, users, settings

api_router = APIRouter()
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(project.router, prefix="/projects", tags=["projects"])
api_router.include_router(logistics.router, prefix="/logistics", tags=["logistics"])
api_router.include_router(kpi.router, prefix="/kpi", tags=["kpi"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
