from fastapi import APIRouter,BackgroundTasks,  Header,Request,Response, HTTPException, Depends
import json
from services.webhook_handler import parse_pr_payload, verify_webhook_signature
from services.github_service import fetch_pr_diff,get_installation_access_token, parse_raw_diff
from services.redis_service import queue, review_pr
from config import settings
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession
from database import engine, Base, get_db
from models.jobs import Job, JobStatus
router = APIRouter(
    prefix='/webhooks',
    tags=['webhook']
)
# changes here
@router.post('/github')
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(default=""),
    x_github_event: str = Header(default=""),
    db: AsyncSession = Depends(get_db)
):
    # Read raw body for signature verification
    body = await request.body()
    # hellosfksdfhsdfjk
    # Verify signature
    if not verify_webhook_signature(body, x_hub_signature_256, settings.GITHUB_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Parse JSON after verification
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Only process PR events
    if x_github_event != "pull_request":
        return {'status' : 'ignored'}
    
    action = payload.get("action")
    
    # Only process opened or synchronized (new commits pushed) PRs
    if action in ["opened", "synchronize"]:
        installation_id = payload["installation"]["id"]
        owner = payload["repository"]["owner"]["login"]
        repo = payload["repository"]["name"]
        pull_number = payload["pull_request"]["number"]
        pr = payload["pull_request"]
        pr_title = pr.get("title", "")
        pr_description = pr.get("body") or ""
        repo_full_name = payload["repository"]["full_name"]  # e.g., "owner/repo-name"
        head_sha = pr["head"]["sha"]
        # Retrieve installation token (from Day 1 Auth Layer)
        installation_token = await get_installation_access_token(installation_id)
        # Fetch the diff
        raw_diff = await fetch_pr_diff(owner, repo, pull_number, installation_token)
        processed_diff = parse_raw_diff(raw_diff)
        print(f"processed_diff : {processed_diff}")
        str_pr_diff = json.dumps([item.model_dump() for item in processed_diff])
        # files_payload = [file.model_dump() for file in processed_diff]
        print(f"type_diff:{type(str_pr_diff)}  + {str_pr_diff}")
        
        new_job = Job(
            pr_id=pull_number,
            repo=repo_full_name,
            head_sha=head_sha,
            status=JobStatus.PENDING
        )
        db.add(new_job)
        await db.commit()
        await db.refresh(new_job)

        queue.enqueue(
            review_pr,
            pr_id=pull_number,
            pr_title =pr_title,
            pr_description = pr_description,
            repo=repo_full_name,
            head_sha=head_sha,
            pr_diff=str(str_pr_diff),
            job_timeout=300,   # 5 min ceiling per PR review
            retry=None,        # see note below on retries
        )

        return {
            "status": "queued",
            "pr": pull_number,
            "diff_size_bytes": len(raw_diff)
        }
    return {"status": "skipped"}

    # if action not in ("opened", "synchronize"):
    #     return Response(status_code=200)
    
    # pr = parse_pr_payload(payload)
    # if pr:
    #     print(f"🔔 PR #{pr.pull_request.number} {action} in {pr.repository.full_name}")
    #     print(f"   SHA: {pr.pull_request.head.sha}")
    #     # Tomorrow: enqueue to Redis queue
    
    # return Response(status_code=200)