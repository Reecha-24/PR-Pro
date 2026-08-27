import json
import time
from typing import List, Optional, Callable, Any
from openai import AsyncOpenAI
from pydantic import ValidationError

from models.findings import Finding, AgentResult

class BaseAgent:
    def __init__(
        self,
        name: str,
        system_prompt: str,
        openai_client: AsyncOpenAI,
        model: str = "gpt-5-mini",
        tools: Optional[List[Callable]] = None,
        max_retries: int = 1
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.client = openai_client
        self.model = model
        self.tools = tools or []
        self.max_retries = max_retries

    async def _call_llm(self, user_prompt: str, attempt: int = 0) -> List[Finding]:
        """Call OpenAI with structured output. Retry once on failure."""
        try:
            response = await self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "agent_findings",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "findings": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "file": {"type": "string"},
                                            "line": {"type": ["integer", "null"]},
                                            "position": {"type": ["integer", "null"]},
                                            "severity": {
                                                "type": "string",
                                                "enum": ["critical", "high", "medium", "low", "info"]
                                            },
                                            "title": {"type": "string"},
                                            "description": {"type": "string"},
                                            "confidence": {
                                                "type": "string",
                                                "enum": ["high", "medium", "low"]
                                            },
                                            "suggestion": {"type": ["string", "null"]}
                                        },
                                        "required": [
                                        "file",
                                        "line",
                                        "position",
                                        "severity",
                                        "title",
                                        "description",
                                        "confidence",
                                        "suggestion"
                                        ],
                                    "additionalProperties": False
                                }
                            }
                        },
                        "required": ["findings"],
                        "additionalProperties": False
                    }
                }
            },
                max_completion_tokens=4000
            )
            
            content = response.choices[0].message.content
            parsed = json.loads(content)
            findings_data = parsed.get("findings", [])
            
            # Validate each finding
            validated = []
            for f in findings_data:
                try:
                    validated.append(Finding(**f))
                except ValidationError as ve:
                    # Skip invalid findings but log them
                    print(f"[{self.name}] Skipping invalid finding: {ve}")
            return validated

        except (json.JSONDecodeError, ValidationError, Exception) as e:
            if attempt < self.max_retries:
                print(f"[{self.name}] LLM call failed, retrying... ({e})")
                return await self._call_llm(user_prompt, attempt + 1)
            raise Exception(f"Failed after {self.max_retries + 1} attempts: {e}")

    async def _run_tools(self, diff: str) -> str:
        """Execute mock tools and append results to context"""
        tool_results = []
        for tool in self.tools:
            try:
                result = await tool(diff)
                tool_results.append(f"Tool: {tool.__name__}\nResult: {json.dumps(result, indent=2)}")
            except Exception as e:
                tool_results.append(f"Tool: {tool.__name__}\nError: {e}")
        return "\n\n".join(tool_results) if tool_results else ""

    async def analyze(self, pr_diff: str,  pr_title: str = "", pr_description: str = "") -> AgentResult:
        start = time.time()
        try:
            # Run mock tools
            tool_context = await self._run_tools(pr_diff)
            
            # Build user prompt
            user_prompt = self._build_prompt(pr_diff, pr_title, pr_description, tool_context)
            
            # Call LLM with structured output
            findings = await self._call_llm(user_prompt)
            
            elapsed = (time.time() - start) * 1000
            return AgentResult(
                agent_name=self.name,
                findings=findings,
                execution_time_ms=elapsed
            )
            
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return AgentResult(
                agent_name=self.name,
                findings=[],
                error=str(e),
                execution_time_ms=elapsed
            )

    def _build_prompt(self, diff: str, title: str, desc: str, tool_context: str) -> str:
        raise NotImplementedError