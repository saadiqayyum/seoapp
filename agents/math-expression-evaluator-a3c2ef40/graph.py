"""
Calculator Agent — safely evaluates arithmetic expressions.
Supports: +, -, *, /, //, %, ** and parentheses.
"""
import ast
import operator
from typing import TypedDict

from langgraph.graph import StateGraph, END

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class CalcState(TypedDict):
    expression: str   # input: e.g. "10*(5-1)+6"
    result: str       # output: numeric result or error message

# ---------------------------------------------------------------------------
# Safe evaluator
# ---------------------------------------------------------------------------

ALLOWED_OPS = {
    ast.Add:      operator.add,
    ast.Sub:      operator.sub,
    ast.Mult:     operator.mul,
    ast.Div:      operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod:      operator.mod,
    ast.Pow:      operator.pow,
    ast.USub:     operator.neg,
    ast.UAdd:     operator.pos,
}

def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant: {node.value!r}")

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in ALLOWED_OPS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left  = _eval_node(node.left)
        right = _eval_node(node.right)
        return ALLOWED_OPS[op_type](left, right)

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in ALLOWED_OPS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        return ALLOWED_OPS[op_type](_eval_node(node.operand))

    raise ValueError(f"Unsupported expression type: {type(node).__name__}")


def safe_eval(expression: str) -> float:
    tree = ast.parse(expression, mode="eval")
    return _eval_node(tree.body)

# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

def calculate(state: CalcState) -> CalcState:
    expr = state["expression"].strip()
    try:
        value = safe_eval(expr)
        # Show as int when the result is a whole number
        if isinstance(value, float) and value.is_integer():
            result = str(int(value))
        else:
            result = str(value)
    except ZeroDivisionError:
        result = "Error: division by zero"
    except (ValueError, SyntaxError) as exc:
        result = f"Error: {exc}"
    except Exception as exc:
        result = f"Error: {exc}"
    return {"expression": expr, "result": result}

# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

builder = StateGraph(CalcState)
builder.add_node("calculate", calculate)
builder.set_entry_point("calculate")
builder.add_edge("calculate", END)

graph = builder.compile()
