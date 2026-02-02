"""Main API router that includes all sub-routers."""

from fastapi import APIRouter

from app.api import projects, tasks, courses, calendar, rules, config, schedule, resources

api_router = APIRouter()

api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Household Tasks"])
api_router.include_router(courses.router, prefix="/courses", tags=["Courses"])
api_router.include_router(calendar.router, prefix="/calendar", tags=["Calendar"])
api_router.include_router(rules.router, prefix="/rules", tags=["Scheduling Rules"])
api_router.include_router(config.router, prefix="/config", tags=["Configuration"])
api_router.include_router(schedule.router, prefix="/schedule", tags=["Scheduling"])
api_router.include_router(resources.router, prefix="/resources", tags=["Resources"])
