from agents.base_agent import BaseAgent
from tools.mocktools import mock_complexity_analyzer

PERFORMANCE_SYSTEM_PROMPT = """You are a Performance Review Agent. Analyze code for performance bottlenecks.
Focus on: N+1 queries, inefficient loops, memory leaks, unnecessary re-renders, blocking operations, algorithmic complexity.
Return findings in the specified JSON format."""

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