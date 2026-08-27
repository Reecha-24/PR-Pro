from agents.base_agent import BaseAgent
from tools.mocktools import mock_npm_audit

SECURITY_SYSTEM_PROMPT = """You are a Security Review Agent. Analyze code diffs for security vulnerabilities.
Focus on: SQL injection, XSS, CSRF, insecure dependencies, hardcoded secrets, auth flaws, input validation.
Return findings in the specified JSON format. Only report issues with medium+ confidence."""

class SecurityAgent(BaseAgent):
    def __init__(self, openai_client):
        super().__init__(
            name="security",
            system_prompt=SECURITY_SYSTEM_PROMPT,
            openai_client=openai_client,
            tools=[mock_npm_audit]  # Fake tool stub
        )
    
    def _build_prompt(self, diff, title, desc, tool_context):
        return f"""PR Title: {title}
PR Description: {desc}

Tool Results:
{tool_context}

Analyze this diff for security issues:

diff:
{diff}"""