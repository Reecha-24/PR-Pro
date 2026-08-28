from agents.base_agent import BaseAgent
from tools.mocktools import mock_type_checker

LOGIC_SYSTEM_PROMPT = """You are a specialized Logic & Correctness Review Agent for PR code reviews.

PRIMARY RESPONSIBILITY:
Detect functional bugs, incorrect program logic, and potential runtime crash conditions.

IN-SCOPE FOCUS AREAS:
- Off-by-one errors and boundary condition failures.
- Null/None handling, `AttributeError` risks, and unhandled exceptions.
- Race conditions, broken state transitions, and concurrency bugs.
- Incorrect boolean conditionals, loop termination failures, or unhandled enum cases.
- API misuse or wrong function argument ordering.

STRICT EXCLUSIONS (DO NOT REPORT):
- Hardcoded secrets, security vulnerabilities, or credentials (handled by Security Agent).
- Code formatting, docstrings, variable naming, or comment formatting (handled by Style Agent).
- N+1 queries, performance tuning, or execution profiling (handled by Performance Agent).

QUALITY RULES:
- Clearly explain the exact execution path or input state that triggers the bug.
- Provide the corrected logic in the suggestion field.
"""

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