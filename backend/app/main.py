from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes.generate_routes import router as generate_router
from app.routes.health_routes import router as health_router
from app.routes.rag_routes import router as rag_router
from app.auth.auth_routes import router as auth_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.5.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(rag_router, prefix=f"{settings.api_prefix}/rag")
app.include_router(generate_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)