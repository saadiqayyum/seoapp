"""
Square-Root Agent
-----------------
Reads the value stored at "sum_result" in the shared KV store and
returns its square root.
"""

import math
from typing import TypedDict
from langgraph.graph import StateGraph, END


# ── State ────────────────────────────────────────────────────────────────────

class SqrtState(TypedDict):
    sum_result: float   # populated from KV
    sqrt_result: float
    message: str


# ── Nodes ────────────────────────────────────────────────────────────────────

async def read_and_sqrt(state: SqrtState) -> SqrtState:
    """Read 'sum_result' from shared KV and compute its square root."""
    from orkest import kv  # only available in deployed runtime

    sum_result = await kv.get("sum_result", default=None)

    if sum_result is None:
        return {
            **state,
            "message": "❌ No value found in KV under 'sum_result'. Run the Adder agent first.",
        }

    if sum_result < 0:
        return {
            **state,
            "sum_result": sum_result,
            "message": f"❌ Cannot compute square root of a negative number ({sum_result}).",
        }

    sqrt_result = math.sqrt(sum_result)

    return {
        **state,
        "sum_result": sum_result,
        "sqrt_result": sqrt_result,
        "message": f"✅ √{sum_result} = {sqrt_result}",
    }


# ── Graph ────────────────────────────────────────────────────────────────────

builder = StateGraph(SqrtState)
builder.add_node("read_and_sqrt", read_and_sqrt)
builder.set_entry_point("read_and_sqrt")
builder.add_edge("read_and_sqrt", END)

graph = builder.compile()
