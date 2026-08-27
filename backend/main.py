from contextlib import asynccontextmanager
import os

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

fe_url = os.getenv("FE_URL", "http://localhost:3000")
origins = [fe_url] if fe_url else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter()


@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}


api_router.include_router(webhook.router)
app.include_router(api_router)