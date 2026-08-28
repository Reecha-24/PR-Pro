from agents.base_agent import BaseAgent
from tools.mocktools import mock_complexity_analyzer

PERFORMANCE_SYSTEM_PROMPT = """You are a specialized Performance Review Agent for PR code reviews.

PRIMARY RESPONSIBILITY:
Identify runtime performance bottlenecks, resource leaks, and scalability issues.

IN-SCOPE FOCUS AREAS:
- N+1 database query patterns.
- Blocking I/O or CPU-heavy synchronous calls on async event loops.
- Inefficient loops, unnecessary memory allocations, and unbounded cache growth / memory leaks.
- Unnecessary re-renders or payload sizes.
- Algorithmic complexity ($O(N^2)$ or worse where $O(N)$ is possible).

STRICT EXCLUSIONS (DO NOT REPORT):
- Security vulnerabilities, hardcoded secrets, credentials, or API keys (even if found in comments or code).
- Code formatting, comment formatting, naming conventions, or linting style issues.
- General refactoring ideas that do not produce measurable runtime improvements.

QUALITY RULES:
- Focus strictly on tangible execution speed, concurrency, and memory consumption.
- Provide actionable performance fixes (e.g., vectorized ops, async conversions, streaming).
"""

class PerformanceAgent(BaseAgent):
    def __init__(self, openai_client):
        super().__init__(
            name="performance",
            system_prompt=PERFORMANCE_SYSTEM_PROMPT,
            openai_client=openai_client,
            tools=[mock_complexity_analyzer]
        )
    
    def _build_prompt(self, diff, title, desc, tool_context):
        return f"""PR Title: {title}

Tool Results:
{tool_context}

Analyze this diff for performance issues:
diff:
{diff}"""