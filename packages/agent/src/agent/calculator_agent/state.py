from typing import Annotated

from langchain.agents import AgentState


def reduce_list(left: list | None, right: list | None) -> list:
    """
    Safely combine two lists, handling cases where either or both inputs might be None.

    Args:
        left (list | None): The first list to combine, or None.
        right (list | None): The second list to combine, or None.
    
    Returns:
        list: A new list containing all elements from both input lists.
            If an input is None, it is treated as an empty list.
    """

    if not left:
        left = []
    if not right:
        right = []
    return left + right

class CalculatorAgentState(AgentState):
    """
        Graph State.
    """
    ops: Annotated[list[str], reduce_list]
