import hmac
import hashlib
from typing import Optional
from pydantic import BaseModel


class PullRequestHead(BaseModel):
    sha: str


class PullRequestBase(BaseModel):
    ref: str


class PullRequest(BaseModel):
    number: int
    head: PullRequestHead
    base: PullRequestBase
    title: str
    diff_url: str


class RepositoryOwner(BaseModel):
    login: str


class Repository(BaseModel):
    full_name: str
    name: str
    owner: RepositoryOwner


class PRWebhookPayload(BaseModel):
    action: str
    pull_request: PullRequest
    repository: Repository


def verify_webhook_signature(body: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature using HMAC-SHA256."""
    expected = "sha256=" + hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def parse_pr_payload(body: dict) -> Optional[PRWebhookPayload]:
    """Validate and parse PR webhook payload."""
    if "pull_request" not in body:
        return None
    return PRWebhookPayload(**body)