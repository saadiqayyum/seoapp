"""
Adder Agent
-----------
Accepts two numbers `a` and `b`, adds them, and saves the result to
the shared KV store under the key "sum_result".
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END


# ── State ────────────────────────────────────────────────────────────────────

class AdderState(TypedDict):
    a: float
    b: float
    sum_result: float
    message: str


# ── Nodes ────────────────────────────────────────────────────────────────────

async def add_numbers(state: AdderState) -> AdderState:
    """Add a and b, then persist the result in shared KV."""
    from orkest import kv  # only available in deployed runtime

    a = state.get("a", 0)
    b = state.get("b", 0)
    result = a + b

    await kv.put("sum_result", result)

    return {
        **state,
        "sum_result": result,
        "message": f"✅ {a} + {b} = {result}  →  saved to KV as 'sum_result'",
    }


# ── Graph ────────────────────────────────────────────────────────────────────

builder = StateGraph(AdderState)
builder.add_node("add_numbers", add_numbers)
builder.set_entry_point("add_numbers")
builder.add_edge("add_numbers", END)

graph = builder.compile()
