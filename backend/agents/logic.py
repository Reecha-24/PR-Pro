from agents.base_agent import BaseAgent
from tools.mocktools import mock_type_checker

LOGIC_SYSTEM_PROMPT = """You are a Logic & Correctness Review Agent. Analyze code for bugs and logic errors.
Focus on: Off-by-one errors, null pointer risks, race conditions, incorrect conditionals, unhandled edge cases, API misuse, type mismatches.
Return findings in the specified JSON format."""

class LogicAgent(BaseAgent):
    def __init__(self, openai_client):
        super().__init__(
            name="logic",
            system_prompt=LOGIC_SYSTEM_PROMPT,
            openai_client=openai_client,
            tools=[mock_type_checker]
        )
    
    def _build_prompt(self, diff, title, desc, tool_context):
        return f"""PR Title: {title}

Tool Results:
{tool_context}

Analyze this diff for logic errors and bugs:
diff:
{diff}"""