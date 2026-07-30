"""
Math Expression Evaluator Agent
Safely evaluates string math expressions including implicit multiplication.
Example: "5*10(5+1)-4" => 296
"""

import ast
import math
import operator
import re
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END


# ── State ─────────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    expression: str          # raw input
    cleaned: str             # after pre-processing
    result: Optional[float]  # numeric result
    error: Optional[str]     # error message, if any
    output: str              # human-readable final answer


# ── Safe AST evaluator ────────────────────────────────────────────────────────

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

ALLOWED_FUNCS = {
    "sqrt": math.sqrt,
    "abs":  abs,
    "sin":  math.sin,
    "cos":  math.cos,
    "tan":  math.tan,
    "log":  math.log,
    "log2": math.log2,
    "log10": math.log10,
    "ceil": math.ceil,
    "floor": math.floor,
    "pi":   math.pi,
    "e":    math.e,
}


def _safe_eval(node):
    """Recursively evaluate an AST node with only whitelisted operations."""
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)

    elif isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant: {node.value!r}")

    elif isinstance(node, ast.Name):
        name = node.id.lower()
        if name in ALLOWED_FUNCS:
            return ALLOWED_FUNCS[name]
        raise ValueError(f"Unknown name: {node.id!r}")

    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in ALLOWED_OPS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left  = _safe_eval(node.left)
        right = _safe_eval(node.right)
        return ALLOWED_OPS[op_type](left, right)

    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in ALLOWED_OPS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        return ALLOWED_OPS[op_type](_safe_eval(node.operand))

    elif isinstance(node, ast.Call):
        # Only allow whitelisted function names
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only simple function calls are allowed.")
        func_name = node.func.id.lower()
        if func_name not in ALLOWED_FUNCS:
            raise ValueError(f"Function not allowed: {node.func.id!r}")
        func = ALLOWED_FUNCS[func_name]
        if callable(func):
            args = [_safe_eval(a) for a in node.args]
            return func(*args)
        else:
            # It's a constant like pi or e referenced as a call — shouldn't happen
            raise ValueError(f"{func_name!r} is not callable")

    else:
        raise ValueError(f"Unsupported expression node: {type(node).__name__}")


def safe_evaluate(expr: str) -> float:
    """Parse and safely evaluate a math expression string."""
    tree = ast.parse(expr, mode="eval")
    return _safe_eval(tree)


# ── Pre-processing ─────────────────────────────────────────────────────────────

def preprocess(expr: str) -> str:
    """
    Clean and normalise the expression:
    - Strip whitespace
    - Replace ^ with ** (Python power)
    - Insert explicit * for implicit multiplication:
        2(3+1)  ->  2*(3+1)
        (2+1)(3)  ->  (2+1)*(3)
        2pi  ->  2*pi
        pi2  ->  pi*2  (constant followed by digit)
    """
    expr = expr.strip()

    # Replace ^ with **
    expr = expr.replace("^", "**")

    # Replace named constants / functions so we don't break their names
    # Insert * between a digit and '('    e.g. 2( -> 2*(
    expr = re.sub(r'(\d)\s*\(', r'\1*(', expr)

    # Insert * between ')' and '('        e.g. )(  ->  )*(
    expr = re.sub(r'\)\s*\(', r')*(', expr)

    # Insert * between ')' and a digit    e.g. )2  ->  )*2
    expr = re.sub(r'\)\s*(\d)', r')*\1', expr)

    # Insert * between a digit and a known function/constant name
    # e.g. 2pi -> 2*pi,  2sqrt -> 2*sqrt
    func_names = "|".join(sorted(ALLOWED_FUNCS.keys(), key=len, reverse=True))
    expr = re.sub(rf'(\d)\s*({func_names})', r'\1*\2', expr, flags=re.IGNORECASE)

    # Insert * between a function/constant name and '('  (already handled by ast.Call, but belt-and-suspenders)
    # e.g. pi( is invalid anyway; leave as is.

    return expr


# ── Graph nodes ───────────────────────────────────────────────────────────────

def parse_node(state: AgentState) -> AgentState:
    """Pre-process and validate the expression string."""
    raw = state.get("expression", "").strip()

    if not raw:
        return {**state, "error": "No expression provided.", "output": "❌ Error: No expression provided.", "cleaned": ""}

    try:
        cleaned = preprocess(raw)
        # Quick syntax check
        ast.parse(cleaned, mode="eval")
        return {**state, "cleaned": cleaned, "error": None}
    except SyntaxError as e:
        msg = f"Syntax error in expression: {e.msg}"
        return {**state, "cleaned": "", "error": msg, "output": f"❌ Error: {msg}"}


def evaluate_node(state: AgentState) -> AgentState:
    """Safely evaluate the cleaned expression."""
    if state.get("error"):
        return state  # skip if already errored

    try:
        result = safe_evaluate(state["cleaned"])
        return {**state, "result": result, "error": None}
    except ZeroDivisionError:
        msg = "Division by zero."
        return {**state, "result": None, "error": msg, "output": f"❌ Error: {msg}"}
    except Exception as e:
        msg = str(e)
        return {**state, "result": None, "error": msg, "output": f"❌ Error: {msg}"}


def format_node(state: AgentState) -> AgentState:
    """Format the result into a human-readable output."""
    if state.get("error"):
        return state  # already has output set

    result = state["result"]
    raw    = state["expression"]
    cleaned = state["cleaned"]

    # Show as int if the result is a whole number
    if isinstance(result, float) and result.is_integer():
        display = str(int(result))
    else:
        display = f"{result:.10g}"  # up to 10 significant figures, no trailing zeros

    output = f"Expression : {raw}\n"
    if cleaned != raw:
        output += f"Parsed as  : {cleaned}\n"
    output += f"Result     : {display}"

    return {**state, "output": output}


def route_after_parse(state: AgentState) -> str:
    return "error" if state.get("error") else "evaluate"


def route_after_evaluate(state: AgentState) -> str:
    return "error" if state.get("error") else "format"


def error_node(state: AgentState) -> AgentState:
    """Terminal error node — output is already set by the node that raised."""
    return state


# ── Build graph ───────────────────────────────────────────────────────────────

builder = StateGraph(AgentState)

builder.add_node("parse",    parse_node)
builder.add_node("evaluate", evaluate_node)
builder.add_node("format",   format_node)
builder.add_node("error",    error_node)

builder.set_entry_point("parse")

builder.add_conditional_edges("parse",    route_after_parse,    {"evaluate": "evaluate", "error": "error"})
builder.add_conditional_edges("evaluate", route_after_evaluate, {"format": "format",     "error": "error"})

builder.add_edge("format", END)
builder.add_edge("error",  END)

graph = builder.compile()
