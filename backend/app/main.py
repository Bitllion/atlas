from fastapi import FastAPI

app = FastAPI(title="Atlas API", version="0.1.0")


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """Return the process health status."""
    return {"status": "ok"}
