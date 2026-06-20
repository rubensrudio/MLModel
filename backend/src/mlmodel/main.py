from fastapi import FastAPI

from mlmodel.api.routes.analyses import router as analyses_router
from mlmodel.api.routes.analytics import router as analytics_router
from mlmodel.api.routes.exports import router as exports_router
from mlmodel.api.routes.health import router as health_router
from mlmodel.api.routes.rock_physics import router as rock_physics_router
from mlmodel.api.routes.samples import router as samples_router
from mlmodel.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.include_router(health_router)
    app.include_router(analyses_router, prefix="/api")
    app.include_router(analytics_router, prefix="/api")
    app.include_router(exports_router, prefix="/api")
    app.include_router(rock_physics_router, prefix="/api")
    app.include_router(samples_router, prefix="/api")
    return app


app = create_app()
