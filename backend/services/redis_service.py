import asyncio
from redis import Redis
from rq import Queue
from openai import AsyncOpenAI
from fastapi import HTTPException
from config import settings
from models.findings import PRReviewRequest, PRReviewResponse
from services.langgraph_orchestrator import create_review_graph, run_review
from services.github_service import ParsedFileDiff
from services.response_synthesizer import synthesize_results
from services.github_service import get_installation_access_token, post_github_review

redis_conn = Redis(host="localhost", port=6379, db=0,protocol=2)
queue = Queue("reviews", connection=redis_conn)
# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# Create LangGraph instance
review_graph = create_review_graph(openai_client)


def review_pr(pr_id: int, pr_title:str, pr_description: str,  repo: str, head_sha: str, pr_diff: str,installation_id:int):
    request = PRReviewRequest(
        pr_diff=pr_diff,
        # pr_diff=SAMPLE_DIFF,
        pr_title=pr_title,
        pr_description=pr_description
    )
    llm_reviews= asyncio.run(async_review_pr(request))
    print(f"reviews:{llm_reviews}")
    inline_comments, summary_body = synthesize_results(llm_reviews)
    print(f"inline_comment:{inline_comments}")
    print(f"summary:{summary_body}")
    installation_token = asyncio.run(get_installation_access_token(installation_id))
    # 3. Post to GitHub
    github_response = asyncio.run(post_github_review(
    repo=repo,
    pr_id=pr_id,
    head_sha=head_sha,
    body_summary=summary_body,
    inline_comments=inline_comments,
    token=installation_token # <--- Pass here
    ))

    return {
        "status": "completed",
        "comments_count": len(inline_comments),
        "github_review_id": github_response.get("id")
    }
    

async def async_review_pr(request:PRReviewRequest):
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
