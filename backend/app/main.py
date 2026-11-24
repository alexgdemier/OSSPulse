from fastapi import FastAPI

from app.api.v1.router import router as v1_router

app = FastAPI(
    title="OSS Pulse API",
    description="Open source maintenance intelligence.",
    version="0.3.1-alpha",
)
app.include_router(v1_router, prefix="/api/v1")


@app.get("/", tags=["service"])
def root() -> dict[str, str]:
    return {"name": "OSS Pulse API", "docs": "/docs", "health": "/api/v1/health"}
