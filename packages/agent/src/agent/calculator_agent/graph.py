from __future__ import annotations

from common.config import get_settings
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic

from agent.calculator_agent.state import CalculatorAgentState
from agent.tools.calculator import calculator

SYSTEM_PROMPT = (
    "You are a precise calculator assistant. "
    "Use the provided tools to evaluate mathematical expressions step by step. "
    "Always show your reasoning and the result clearly. "
    "Return all results as plain text without Markdown math delimiters."
)


def build_graph() -> object:
    """Build and return the calculator agent graph.

    Returns:
        A compiled StateGraph using langchain.agents.create_agent as the harness.
    """
    settings = get_settings()
    model = ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
    )
    agent =  create_agent(model=model, tools=[calculator], system_prompt=SYSTEM_PROMPT, state_schema=CalculatorAgentState)
    agent = agent.with_config({"recursion_limit": 20})

    return agent
