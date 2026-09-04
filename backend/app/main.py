from fastapi import FastAPI

from app.api.v1.admin import router as admin_router
from app.api.v1.assets import router as assets_router
from app.api.v1.auth import router as auth_router
from app.api.v1.core import router as core_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.imports import router as imports_router
from app.api.v1.operations import router as operations_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.quality import router as quality_router
from app.api.v1.workflow import router as workflow_router
from app.core.exceptions import install_exception_handlers

app = FastAPI(title="Atlas API", version="0.1.0")
app.include_router(core_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(imports_router, prefix="/api/v1")
app.include_router(assets_router, prefix="/api/v1")
app.include_router(operations_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")
app.include_router(workflow_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(quality_router, prefix="/api/v1")
install_exception_handlers(app)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """Return the process health status."""
    return {"status": "ok"}
