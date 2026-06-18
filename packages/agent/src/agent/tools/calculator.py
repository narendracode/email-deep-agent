from __future__ import annotations

from typing import Literal

from langchain_core.tools import tool


@tool
def calculator(
    operation: Literal["add", "subtract", "multiply", "divide"],
    a: int | float,
    b: int | float,
) -> int | float:
    """Two-input calculator tool that returns precise answers.

    Args:
        operation: The operation to perform (add, subtract, multiply, divide).
        a: The first number.
        b: The second number.

    Returns:
        The result of the calculation.

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
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        return a / b
    else:
        raise ValueError(
            f"Invalid operation: {operation}. Supported: add, subtract, multiply, divide."
        )
