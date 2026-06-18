#!/usr/bin/env python
"""CLI test script for the calculator ReAct agent.

Usage:
    # Interactive mode
    uv run python packages/agent/src/agent/run_calculator.py

    # Single query mode
    uv run python packages/agent/src/agent/run_calculator.py "what is (5 + 3) * 12?"

    # Generate diagram image (default: calculator_agent.png)
    uv run python packages/agent/src/agent/run_calculator.py --diagram
    uv run python packages/agent/src/agent/run_calculator.py --diagram --output my_agent.jpg
    uv run python packages/agent/src/agent/run_calculator.py --diagram --output my_agent.png
"""
from __future__ import annotations

import asyncio
import io
import sys
from pathlib import Path

from langchain_core.messages import HumanMessage


def save_diagram(output: str = "calculator_agent.png") -> None:
    """Generate and save the agent graph as a PNG or JPEG image.

    Args:
        output: Destination file path. Format is inferred from the extension
                (.png or .jpg/.jpeg).
    """
    from PIL import Image

    from agent.calculator_agent.graph import build_graph

    path = Path(output)
    fmt = path.suffix.lower().lstrip(".")

    if fmt not in ("png", "jpg", "jpeg"):
        print(f"Unsupported format '{fmt}'. Use .png or .jpg", file=sys.stderr)
        sys.exit(1)

    png_bytes = build_graph().get_graph().draw_mermaid_png()

    if fmt == "png":
        path.write_bytes(png_bytes)
    else:
        img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
        img.save(path, format="JPEG", quality=95)

    print(f"Diagram saved to {path.resolve()}")


async def run_query(query: str) -> None:
    """Run a single query and print the agent's response.

    Args:
        query: The math question to send to the agent.
    """
    from agent.calculator_agent.graph import build_graph

    graph = build_graph()
    result = await graph.ainvoke({"messages": [HumanMessage(content=query)]})

    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content:
            print(msg.content)
            break


async def interactive() -> None:
    """Run the agent in interactive REPL mode."""
    from agent.calculator_agent.graph import build_graph

    graph = build_graph()
    print("Calculator Agent — type 'quit' to exit")
    print("-" * 40)

    while True:
        try:
            query = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break

        result = await graph.ainvoke({"messages": [HumanMessage(content=query)]})
        for msg in reversed(result["messages"]):
            if msg.type == "ai" and msg.content:
                print(f"\nAgent: {msg.content}")
                break


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--diagram" in args:
        args.remove("--diagram")
        output_file = "calculator_agent.png"
        if "--output" in args:
            idx = args.index("--output")
            output_file = args[idx + 1]
        save_diagram(output_file)
    elif args:
        asyncio.run(run_query(" ".join(args)))
    else:
        asyncio.run(interactive())
