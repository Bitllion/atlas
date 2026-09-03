from fastapi import FastAPI

from app.api.v1.assets import router as assets_router
from app.api.v1.core import router as core_router
from app.api.v1.imports import router as imports_router
from app.core.exceptions import install_exception_handlers

app = FastAPI(title="Atlas API", version="0.1.0")
app.include_router(core_router, prefix="/api/v1")
app.include_router(imports_router, prefix="/api/v1")
app.include_router(assets_router, prefix="/api/v1")
install_exception_handlers(app)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """Return the process health status."""
    return {"status": "ok"}
