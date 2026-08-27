from redis import Redis
from rq import Queue

redis_conn = Redis(host="localhost", port=6379, db=0,protocol=2)
queue = Queue("reviews", connection=redis_conn)

def review_pr(pr_id: int, repo: str, head_sha: str, files: list[dict]):
    print(f"Processing PR {pr_id} in {repo} @ {head_sha[:7]} ({len(files)} files)")
    # Day 2: fetch diff, parse hunks -> Day 3: dispatch to 4 agents -> synthesize
    return {"status": "done", "pr_id": pr_id}