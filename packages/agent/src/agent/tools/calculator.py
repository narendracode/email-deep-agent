from __future__ import annotations

from typing import Annotated, Literal

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from agent.calculator_agent.state import CalculatorAgentState


@tool
def calculator(
    operation: Literal["add", "subtract", "multiply", "divide"],
    a: int | float,
    b: int | float,
    state: Annotated[CalculatorAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """Two-input calculator tool that returns precise answers.

    Args:
        operation: The operation to perform (add, subtract, multiply, divide).
        a: The first number.
        b: The second number.

    Returns:
        A Command updating state with the result and operation log.

    Raises:
        ValueError: If operation is divide and b is zero.
        ValueError: If an unsupported operation is provided.

    Example:
        divide: result = a/b
        subtract: result = a-b
    """
    if operation == "divide" and b == 0:
        raise ValueError("Division by zero is not allowed.")

    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        result = a / b
    else:
        raise ValueError(
            f"Invalid operation: {operation}. Supported: add, subtract, multiply, divide."
        )

    return Command(
        update={
            "ops": [f"({operation}, {a}, {b}) = {result}"],
            "messages": [ToolMessage(str(result), tool_call_id=tool_call_id)],
        }
    )
