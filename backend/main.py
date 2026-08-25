import os
import string
from dotenv import load_dotenv, dotenv_values
load_dotenv()

from fastapi import Body, Depends, FastAPI, APIRouter
# from database import Base, engine, SessionLocal
from routes import webhook
# from sqlalchemy import create_engine, Column, Integer, String, text
# import models

from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

fe_url = os.getenv("FE_URL", "http://localhost:3000")
origins = [fe_url] if fe_url else ["*"]
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Parent router - everything mounted on this gets an /api prefix.
# api_router = APIRouter(prefix="/api")
api_router = APIRouter()


@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}

api_router.include_router(webhook.router)
# Base.metadata.create_all(bind=engine)


app.include_router(api_router)