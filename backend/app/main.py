from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.routes.generate_routes import router as generate_router
from app.routes.health_routes import router as health_router
from app.routes.rag_routes import router as rag_router
from app.auth.auth_routes import router as auth_router
from app.api.routes.generations import router as generations_router
from app.db.session import init_db
from app.events.kafka_producer import kafka_events


settings = get_settings()

# Important for pytest:
# Create DB tables when app.main is imported.
# This avoids "no such table: generations" in tests.
init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.kafka_enabled:
        await kafka_events.start()
    else:
        print("Kafka disabled. Skipping Kafka producer startup.")

    try:
        yield
    finally:
        if settings.kafka_enabled:
            await kafka_events.stop()


app = FastAPI(
    title=settings.app_name,
    version="0.5.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health_router)
app.include_router(rag_router, prefix=f"{settings.api_prefix}/rag")
app.include_router(generate_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(generations_router, prefix=settings.api_prefix)