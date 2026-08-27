from agents.base_agent import BaseAgent
from tools.mocktools import mock_linter_check

STYLE_SYSTEM_PROMPT = """You are a Code Style Review Agent. Analyze code for style, readability, and maintainability.
Focus on: Naming conventions, code duplication, comment quality, formatting consistency, dead code, magic numbers, type hints.
Return findings in the specified JSON format."""

class StyleAgent(BaseAgent):
    def __init__(self, openai_client):
        super().__init__(
            name="style",
            system_prompt=STYLE_SYSTEM_PROMPT,
            openai_client=openai_client,
            tools=[mock_linter_check]
        )
    
    def _build_prompt(self, diff, title, desc, tool_context):
        return f"""PR Title: {title}

Tool Results:
{tool_context}

Analyze this diff for style and maintainability issues:

diff:
{diff}"""
