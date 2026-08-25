from fastapi import APIRouter,BackgroundTasks,  Header,Request,Response, HTTPException
import json
from services.webhook_handler import parse_pr_payload, verify_webhook_signature
from services.github_service import fetch_pr_diff,get_installation_access_token, parse_raw_diff
from config import settings
from fastapi.responses import JSONResponse
router = APIRouter(
    prefix='/webhooks',
    tags=['webhook']
)
# changes here
@router.post('/github')
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(default=""),
    x_github_event: str = Header(default="")
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
    
    print(f"Payload 31 :{payload}")

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
        
        # Retrieve installation token (from Day 1 Auth Layer)
        installation_token = await get_installation_access_token(installation_id)
        # Fetch the diff
        raw_diff = await fetch_pr_diff(owner, repo, pull_number, installation_token)
        processed_diff = parse_raw_diff(raw_diff)
        print(f"processed_diff : {processed_diff}")
        # PASS TO NEXT STEP: Send `raw_diff` to your parser / Redis worker

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