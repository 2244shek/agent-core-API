from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.endpoints import agent # Import the new router
# DB setup
from app.db.session import engine, Base
from app.db import models
from app.core.exceptions import global_exception_handler

# This creates the tables in your Neon Postgres DB
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)
app.add_exception_handler(Exception, global_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the Agent Router
app.include_router(agent.router, prefix=f"{settings.API_V1_STR}/agent", tags=["agent"])

@app.get("/")
async def root():
    return {"status": "Agent API is live", "version": "1.0.0"}