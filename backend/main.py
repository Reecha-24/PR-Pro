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

# # Initialize OpenAI client
# openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# # Create LangGraph instance
# review_graph = create_review_graph(openai_client)

app = FastAPI(lifespan=lifespan)

# fe_url = os.getenv("FE_URL", "http://localhost:3000")
# origins = [fe_url] if fe_url else ["*"]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

api_router = APIRouter()


@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/review", response_model=PRReviewResponse)
async def review_pr(request: PRReviewRequest):
    """
    Process a PR through 4 specialist agents running in parallel via LangGraph.
    Timeout: 60 seconds.
    """
    if not request.pr_diff:
        raise HTTPException(status_code=400, detail="pr_diff required")
    
    state = {
        "pr_diff": request.pr_diff,
        "pr_title": request.pr_title or "",
        "pr_description": request.pr_description or "",
        "security_result": None,
        "performance_result": None,
        "style_result": None,
        "logic_result": None,
        "errors": []
    }
    
    result = await run_review(review_graph, state, timeout=60.0)
    return result

@app.post("/review/debug")
async def review_pr_debug(request: PRReviewRequest):
    """
    Same as /review but returns raw JSON blobs for debugging.
    """
    result = await review_pr(request)
    return JSONResponse(content=json.loads(result.model_dump_json()))

# Sample diff for testing
SAMPLE_DIFF = """diff --git a/src/auth.js b/src/auth.js
index 1234..5678 100644
--- a/src/auth.js
+++ b/src/auth.js
@@ -10,5 +10,5 @@ function login(username, password) {
-    const query = `SELECT * FROM users WHERE username = '${username}'`;
+    const query = "SELECT * FROM users WHERE username = '" + username + "'";
     const result = db.query(query);
     if (result.length > 0) {
         return jwt.sign({user: result[0]}, 'hardcoded_secret_key');
@@ -25,5 +25,10 @@ function getUserData(id) {
+    for (let i = 0; i < ids.length; i++) {
+        users.push(db.query("SELECT * FROM users WHERE id = " + ids[i]));
+    }
     return users;
 }
"""

@app.get("/demo")
async def demo(processed_diff):
    """Run a demo review with sample diff"""
    request = PRReviewRequest(
        pr_diff=processed_diff,
        # pr_diff=SAMPLE_DIFF,
        pr_title="Fix auth flow",
        pr_description="Updated login and user data retrieval"
    )
    return await review_pr(request)

api_router.include_router(webhook.router)
app.include_router(api_router)