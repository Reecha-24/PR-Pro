import time
import asyncio
from typing import Annotated
from typing_extensions import TypedDict
from operator import add

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from functools import partial
from models.findings import AgentResult, PRReviewResponse
from agents.security import SecurityAgent
from agents.performance import PerformanceAgent
from agents.style import StyleAgent
from agents.logic import LogicAgent

# LangGraph State
class ReviewState(TypedDict):
    pr_diff: str
    pr_title: str
    pr_description: str
    security_result: AgentResult
    performance_result: AgentResult
    style_result: AgentResult
    logic_result: AgentResult
    errors: Annotated[list, add]

# Node functions - each runs one agent
async def security_node(state: ReviewState, security_agent: SecurityAgent):
    result = await security_agent.analyze(
        state["pr_diff"], 
        state.get("pr_title", ""),
        state.get("pr_description", "")
    )
    return {"security_result": result}

async def performance_node(state: ReviewState, performance_agent: PerformanceAgent):
    result = await performance_agent.analyze(
        state["pr_diff"], 
        state.get("pr_title", ""),
        state.get("pr_description", "")
    )
    return {"performance_result": result}

async def style_node(state: ReviewState, style_agent: StyleAgent):
    result = await style_agent.analyze(
        state["pr_diff"], 
        state.get("pr_title", ""),
        state.get("pr_description", "")
    )
    return {"style_result": result}

async def logic_node(state: ReviewState, logic_agent: LogicAgent):
    result = await logic_agent.analyze(
        state["pr_diff"], 
        state.get("pr_title", ""),
        state.get("pr_description", "")
    )
    return {"logic_result": result}

# Build the graph
def create_review_graph(openai_client):
    # Initialize agents
    security_agent = SecurityAgent(openai_client)
    performance_agent = PerformanceAgent(openai_client)
    style_agent = StyleAgent(openai_client)
    logic_agent = LogicAgent(openai_client)

    # Create 
    workflow = StateGraph(ReviewState)

    # Add nodes with agent instances 
    workflow.add_node("performance", partial(performance_node, performance_agent=performance_agent))
    workflow.add_node("style", partial(style_node, style_agent=style_agent))
    workflow.add_node("security", partial(security_node, security_agent=security_agent))
    workflow.add_node("logic", partial(logic_node, logic_agent=logic_agent))

    # All 4 agents run in parallel from the 
    workflow.add_edge(START, "security")
    workflow.add_edge(START, "performance")
    workflow.add_edge(START, "style")
    workflow.add_edge(START, "logic")

    # 2. Join all 4 nodes into END (Fan-In)
    workflow.add_edge("security", END)
    workflow.add_edge("performance", END)
    workflow.add_edge("style", END)
    workflow.add_edge("logic", END)

    # Compile with memory checkpointing (optional but good practice)
    return workflow.compile(checkpointer=MemorySaver())

# Helper to run with timeout
async def run_review(graph, state: dict, timeout: float = 60.0) -> PRReviewResponse:
    start = time.time()
    
    try:
        # Run graph with timeout
        result = await asyncio.wait_for(
            graph.ainvoke(
                state,
                config={"configurable": {"thread_id": "pr_review_day3"}}
            ),
            timeout=timeout
        )
        
        elapsed = (time.time() - start) * 1000
        
        total = (
            len(result["security_result"].findings) +
            len(result["performance_result"].findings) +
            len(result["style_result"].findings) +
            len(result["logic_result"].findings)
        )
        
        return PRReviewResponse(
            security=result["security_result"],
            performance=result["performance_result"],
            style=result["style_result"],
            logic=result["logic_result"],
            total_findings=total,
            execution_time_ms=elapsed
        )
        
    except asyncio.TimeoutError:
        elapsed = (time.time() - start) * 1000
        # Return partial results if available, or empty
        return PRReviewResponse(
            security=AgentResult(agent_name="security", error="Timeout"),
            performance=AgentResult(agent_name="performance", error="Timeout"),
            style=AgentResult(agent_name="style", error="Timeout"),
            logic=AgentResult(agent_name="logic", error="Timeout"),
            total_findings=0,
            execution_time_ms=elapsed
        )