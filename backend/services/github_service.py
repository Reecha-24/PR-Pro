import httpx
from typing import Optional, List
import time
import jwt
from config import settings
import re
from schemas.db_entry import DiffLine, ParsedFileDiff

GITHUB_API_URL = "https://api.github.com"

def generate_app_jwt() -> str:
    """Generates a RS256-signed JWT valid for up to 10 minutes."""
    with open(settings.PRIVATE_KEY_PATH, "r") as f:
        private_key = f.read()

    now = int(time.time())
    payload = {
        "iat": now - 60,       # Issued 60s in past to account for clock drift
        "exp": now + (10 * 60), # Maximum allowed expiry is 10 minutes
        "iss": settings.GITHUB_APP_ID,
    }
    
    return jwt.encode(payload, private_key, algorithm="RS256")


async def get_installation_access_token(installation_id: int) -> str:
    """Exchanges App JWT for a repo-scoped installation access token."""
    app_jwt = generate_app_jwt()
    url = f"{GITHUB_API_URL}/app/installations/{installation_id}/access_tokens"
    
    headers = {
        "Authorization": f"Bearer {app_jwt}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers)
        if response.status_code != 201:
            raise Exception(f"Failed to fetch token: {response.text}")
        
        # Returns dict containing {"token": "ghs_xxxx...", "expires_at": "..."}
        return response.json()["token"]

from typing import Optional
import httpx

GITHUB_API_URL = "https://api.github.com"

async def fetch_pr_diff(
    owner: str, 
    repo: str, 
    pull_number: int, 
    installation_token: str
) -> str:
    """
    Fetches all changed files for a PR using GitHub's /files API.
    Handles pagination (>300 files) and reconstructs a unified diff string.
    """
    headers = {
        "Authorization": f"Bearer {installation_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        return await _fetch_pr_diff_in_chunks(client, owner, repo, pull_number, headers)


async def _fetch_pr_diff_in_chunks(
    client: httpx.AsyncClient, 
    owner: str, 
    repo: str, 
    pull_number: int, 
    headers: dict
) -> str:
    diff_chunks = []
    page = 1
    per_page = 100

    while True:
        url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pull_number}/files?per_page={per_page}&page={page}"
        files_response = await client.get(url, headers=headers)

        if files_response.status_code != 200:
            raise Exception(f"Failed to fetch PR files (Status {files_response.status_code}): {files_response.text}")

        files = files_response.json()
        if not files:
            break

        for file in files:
            filename = file.get("filename")
            patch = file.get("patch")

            if patch:
                # Reconstruct git header format so diff parser can process it seamlessly
                header = f"diff --git a/{filename} b/{filename}\n--- a/{filename}\n+++ b/{filename}\n"
                diff_chunks.append(header + patch)
            elif file.get("status") not in ["removed", "renamed"]:
                # Fallback for massive files without inline patch
                raw_patch = await _fetch_single_file_patch(client, file.get("raw_url"), headers)
                if raw_patch:
                    diff_chunks.append(raw_patch)

        # Stop pagination if current page returned fewer items than the max per_page limit
        if len(files) < per_page:
            break

        page += 1

    return "\n".join(diff_chunks)


async def _fetch_single_file_patch(
    client: httpx.AsyncClient, 
    raw_url: Optional[str], 
    headers: dict
) -> Optional[str]:
    if not raw_url:
        return None
    res = await client.get(raw_url, headers=headers)
    return res.text if res.status_code == 200 else None


# Matches hunk header format: @@ -old_start,old_count +new_start,new_count @@
HUNK_HEADER_REGEX = re.compile(r"^@@\s+-(?P<old_start>\d+)(?:,(?P<old_count>\d+))?\s+\+(?P<new_start>\d+)(?:,(?P<new_count>\d+))?\s+@@")

def parse_patch(filename: str, patch_text: str) -> ParsedFileDiff:
    """
    Parses a single file's patch string into structured lines with 1-based GitHub position indexing.
    """
    lines: List[DiffLine] = []
    
    if not patch_text:
        return ParsedFileDiff(filename=filename, lines=lines)

    patch_lines = patch_text.splitlines()
    position = 0
    
    current_old_line = 0
    current_new_line = 0

    for line in patch_lines:
        position += 1  # GitHub position increments for EVERY line in the patch string
        
        # 1. Handle Hunk Header (e.g. @@ -132,7 +132,7 @@)
        hunk_match = HUNK_HEADER_REGEX.match(line)
        if hunk_match:
            current_old_line = int(hunk_match.group("old_start"))
            current_new_line = int(hunk_match.group("new_start"))
            continue

        # 2. Handle Added Lines
        if line.startswith("+"):
            lines.append(
                DiffLine(
                    position=position,
                    change_type="add",
                    old_line_number=None,
                    new_line_number=current_new_line,
                    content=line[1:],
                )
            )
            current_new_line += 1

        # 3. Handle Deleted Lines
        elif line.startswith("-"):
            lines.append(
                DiffLine(
                    position=position,
                    change_type="del",
                    old_line_number=current_old_line,
                    new_line_number=None,
                    content=line[1:],
                )
            )
            current_old_line += 1

        # 4. Handle Context Lines (Unchanged)
        elif line.startswith(" "):
            lines.append(
                DiffLine(
                    position=position,
                    change_type="context",
                    old_line_number=current_old_line,
                    new_line_number=current_new_line,
                    content=line[1:],
                )
            )
            current_old_line += 1
            current_new_line += 1

    return ParsedFileDiff(filename=filename, lines=lines)

def parse_raw_diff(raw_diff: str) -> List[ParsedFileDiff]:
    """
    Splits a multi-file raw diff string into per-file blocks 
    and passes each filename and patch_text to parse_patch.
    """
    parsed_files: List[ParsedFileDiff] = []
    
    # Split raw_diff into separate file sections
    blocks = raw_diff.split("diff --git ")
    
    for block in blocks:
        if not block.strip():
            continue
            
        # 1. Extract filename from header line (e.g. "a/src/main.py b/src/main.py")
        first_line = block.splitlines()[0]
        filename_match = re.search(r"b/(.+)$", first_line)
        
        # 2. Extract patch text starting from the first @@ hunk header
        hunk_start_index = block.find("@@")
        
        if filename_match and hunk_start_index != -1:
            filename = filename_match.group(1).strip()
            patch_text = block[hunk_start_index:]
            
            # 3. Call your function for this file
            parsed_file = parse_patch(filename, patch_text)
            parsed_files.append(parsed_file)
            
    return parsed_files