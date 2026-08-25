from pydantic import BaseModel
from typing import List, Optional, Literal

class DiffLine(BaseModel):
    position: int                  # 1-based index within the patch (required for GitHub Review API)
    change_type: Literal["add", "del", "context"]
    old_line_number: Optional[int] # Line number in original file (None for additions)
    new_line_number: Optional[int] # Line number in modified file (None for deletions)
    content: str                   # Line text without '+' / '-' / ' ' prefix

class ParsedFileDiff(BaseModel):
    filename: str
    lines: List[DiffLine]