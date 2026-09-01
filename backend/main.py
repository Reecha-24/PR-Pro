import os
import json
from openai import AsyncOpenAI
from contextlib import asynccontextmanager
from models.findings import PRReviewRequest, PRReviewResponse
from services.langgraph_orchestrator import create_review_graph, run_review
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from database import AsyncSessionLocal, Base, engine
import models  # Must be imported so Base.metadata knows about Job, PRReview, Suggestion
from routes import webhook


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Asynchronously create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)

api_router = APIRouter()


@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}

api_router.include_router(webhook.router)
app.include_router(api_router)