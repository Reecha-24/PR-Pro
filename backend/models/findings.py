from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from enum import Enum
from schemas.db_entry import DiffLine, ParsedFileDiff

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Finding(BaseModel):
    file: str = Field(description="Path to the affected file")
    line: Optional[int] = Field(None, description="Line number of the issue")
    position: Optional[int] = Field(None, description="Character position in the line")
    severity: Severity = Field(description="Severity of the finding")
    title: str = Field(description="Short title of the finding")
    description: str = Field(description="Detailed description of the issue")
    confidence: Confidence = Field(description="Confidence level in this finding")
    suggestion: Optional[str] = Field(None, description="Suggested fix or improvement")

class AgentResult(BaseModel):
    agent_name: str
    findings: List[Finding] = Field(default_factory=list)
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None

class PRReviewRequest(BaseModel):
    pr_diff: Optional[str] = Field(description="The git diff of the PR")
    pr_title: Optional[str] = ""
    pr_description: Optional[str] = ""

class PRReviewResponse(BaseModel):
    pr_id: Optional[str] = None
    security: AgentResult
    performance: AgentResult
    style: AgentResult
    logic: AgentResult
    total_findings: int
    execution_time_ms: float