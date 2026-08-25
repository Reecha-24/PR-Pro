from fastapi import APIRouter, Header,Request,Response, HTTPException
import json
from github.webhook_handler import parse_pr_payload, verify_webhook_signature
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
    
    # Only process PR events
    if x_github_event != "pull_request":
        return Response(status_code=200)
    
    action = payload.get("action")
    if action not in ("opened", "synchronize"):
        return Response(status_code=200)
    
    pr = parse_pr_payload(payload)
    if pr:
        print(f"🔔 PR #{pr.pull_request.number} {action} in {pr.repository.full_name}")
        print(f"   SHA: {pr.pull_request.head.sha}")
        # Tomorrow: enqueue to Redis queue
    
    return Response(status_code=200)