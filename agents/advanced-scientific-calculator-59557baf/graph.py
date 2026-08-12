"""
Advanced Scientific Calculator — LangGraph Agent
Nodes:  interpret → execute → (retry?) → format
"""
import os
import math
import cmath
import re
import traceback
from typing import TypedDict, Optional, List

from langgraph.graph import StateGraph, END
from anthropic import Anthropic


# ─────────────────────────── State ────────────────────────────────────────────

class CalcState(TypedDict):
    expression: str
    precision: int            # significant figures
    python_code: str
    raw_result: str
    steps: List[str]
    result: str
    explanation: str
    error: Optional[str]
    retries: int              # how many times we've retried execution


# ─────────────────────────── Prompts ──────────────────────────────────────────

INTERPRETER_SYSTEM = """You are an expert scientific calculator code generator.
Your sole job is to produce correct, executable Python 3 code for any math expression or problem.

Rules:
- Available namespaces already loaded: math, cmath, numpy (as np), sympy (all public names via star import), statistics module functions.
- Store the final answer in a variable named `result`.
- Store intermediate calculation steps as human-readable strings in a list named `steps`.
- For trig functions, default to DEGREES unless the user explicitly says radians or uses π.
- For symbolic answers (sympy), also compute a numeric approximation with N(expr, <precision>) and store both.
- For equations like "solve x²=4", use sympy.solve().
- Return ONLY raw Python code — no markdown fences, no explanations.
"""

RETRY_HINT = "\n\nPrevious attempt FAILED with:\n{error}\nFix the code and try again."


# ─────────────────────────── Nodes ────────────────────────────────────────────

def interpret_node(state: CalcState) -> CalcState:
    """Ask Claude to produce Python code for the expression."""
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    user_content = (
        f"Generate Python code to compute:\n\n  {state['expression']}\n\n"
        f"Use {state.get('precision', 10)} significant figures for floats.\n"
        "Remember: store answer in `result`, steps in `steps` list."
    )

    if state.get("error") and state.get("retries", 0) > 0:
        user_content += RETRY_HINT.format(error=state["error"][:600])

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1800,
        system=INTERPRETER_SYSTEM,
        messages=[{"role": "user", "content": user_content}],
    )

    code = response.content[0].text
    # Strip any accidental markdown code fences
    code = re.sub(r"^```(?:python)?\s*", "", code, flags=re.MULTILINE)
    code = re.sub(r"\s*```\s*$", "", code, flags=re.MULTILINE)

    return {**state, "python_code": code.strip(), "error": None}


def execute_node(state: CalcState) -> CalcState:
    """Execute the generated code in a rich but sandboxed namespace."""
    import numpy as np
    import sympy
    from sympy import (
        Symbol, symbols, Function,
        solve, dsolve, diff, integrate, limit, series, summation,
        sin, cos, tan, cot, sec, csc,
        asin, acos, atan, atan2, acot,
        sinh, cosh, tanh, asinh, acosh, atanh,
        log, exp, sqrt, root, Abs,
        factorial, binomial, fibonacci, lucas,
        gcd, lcm, isprime, factorint, totient,
        ceiling, floor, sign, Piecewise,
        Matrix,
        Rational, Integer, Float,
        pi, E, I, oo, zoo, nan, GoldenRatio, EulerGamma,
        Eq, Ne, Lt, Le, Gt, Ge,
        simplify, expand, factor, collect, cancel, apart, together,
        trigsimp, powsimp, radsimp, nsimplify,
        latex, pretty, N, re as Re, im as Im,
    )
    from statistics import mean, median, mode, stdev, variance, pstdev, pvariance

    precision = state.get("precision", 10)

    # Matrix helpers — eigenvals/eigenvects/det/trace are Matrix methods, not top-level
    def det(m):      return m.det()
    def trace(m):    return m.trace()
    def transpose(m): return m.T
    def eigenvals(m): return m.eigenvals()
    def eigenvects(m): return m.eigenvects()

    # ln is an alias for log in SymPy; cbrt via root(x,3)
    ln   = log
    cbrt = lambda x: root(x, 3)

    namespace: dict = {
        # builtins subset
        "abs": abs, "round": round, "sum": sum, "min": min, "max": max,
        "int": int, "float": float, "complex": complex, "list": list,
        "range": range, "zip": zip, "map": map, "filter": filter,
        "sorted": sorted, "reversed": reversed, "enumerate": enumerate,
        "print": print, "len": len, "pow": pow, "divmod": divmod,
        # std libs
        "math": math, "cmath": cmath,
        # numpy
        "np": np, "numpy": np,
        # sympy — module + common names
        "sympy": sympy,
        "Symbol": Symbol, "symbols": symbols, "Function": Function,
        "solve": solve, "dsolve": dsolve,
        "diff": diff, "integrate": integrate, "limit": limit,
        "series": series, "summation": summation,
        "sin": sin, "cos": cos, "tan": tan, "cot": cot, "sec": sec, "csc": csc,
        "asin": asin, "acos": acos, "atan": atan, "atan2": atan2, "acot": acot,
        "sinh": sinh, "cosh": cosh, "tanh": tanh,
        "asinh": asinh, "acosh": acosh, "atanh": atanh,
        "log": log, "ln": ln, "exp": exp, "sqrt": sqrt, "cbrt": cbrt,
        "root": root, "Abs": Abs,
        "factorial": factorial, "binomial": binomial,
        "fibonacci": fibonacci, "lucas": lucas,
        "gcd": gcd, "lcm": lcm, "isprime": isprime,
        "factorint": factorint, "totient": totient,
        "ceiling": ceiling, "floor": floor, "sign": sign,
        "Piecewise": Piecewise,
        # Matrix + helper wrappers
        "Matrix": Matrix,
        "det": det, "trace": trace, "transpose": transpose,
        "eigenvals": eigenvals, "eigenvects": eigenvects,
        "Rational": Rational, "Integer": Integer, "Float": Float,
        "pi": pi, "E": E, "I": I, "oo": oo,
        "GoldenRatio": GoldenRatio, "EulerGamma": EulerGamma,
        "Eq": Eq, "Ne": Ne, "Lt": Lt, "Le": Le, "Gt": Gt, "Ge": Ge,
        "simplify": simplify, "expand": expand, "factor": factor,
        "collect": collect, "cancel": cancel, "apart": apart, "together": together,
        "trigsimp": trigsimp, "powsimp": powsimp,
        "radsimp": radsimp, "nsimplify": nsimplify,
        "latex": latex, "pretty": pretty, "N": N,
        "Re": Re, "Im": Im,
        # statistics
        "mean": mean, "median": median, "mode": mode,
        "stdev": stdev, "variance": variance,
        "pstdev": pstdev, "pvariance": pvariance,
        # outputs
        "result": None,
        "steps": [],
        # helpers: degree conversion factors
        "deg": math.pi / 180,
        "rad": 180 / math.pi,
    }

    try:
        exec(compile(state["python_code"], "<calc>", "exec"), namespace)  # type: ignore[arg-type]
        result_val = namespace.get("result")
        steps_val = namespace.get("steps", [])

        # Serialise the result to a clean string
        raw = _serialize(result_val, precision)

        return {
            **state,
            "raw_result": raw,
            "steps": [str(s) for s in steps_val] if isinstance(steps_val, list) else [],
            "error": None,
        }

    except Exception as exc:
        return {
            **state,
            "raw_result": "",
            "steps": [],
            "error": f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}",
        }


def format_node(state: CalcState) -> CalcState:
    """Ask Claude to produce a clean, human-readable explanation."""
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    if state.get("error"):
        prompt = (
            f'The user wanted to compute: "{state["expression"]}"\n\n'
            f"Python execution failed:\n{state['error'][:700]}\n\n"
            "Provide:\n"
            "1. A clear one-sentence explanation of what went wrong.\n"
            "2. The correct answer if you can determine it analytically.\n"
            "3. One concrete suggestion to fix or rephrase the input.\n"
            "Be brief. Start with 'Error:'."
        )
    else:
        steps_block = (
            "\n".join(f"  {i+1}. {s}" for i, s in enumerate(state.get("steps", [])))
            or "  (direct computation)"
        )
        prompt = (
            f'User computed: "{state["expression"]}"\n\n'
            f"Result: {state['raw_result']}\n\n"
            f"Steps:\n{steps_block}\n\n"
            "Respond with:\n"
            "Line 1: the result formatted cleanly (e.g. '= 42', '≈ 3.14159265', 'x ∈ {2, 3}').\n"
            "Line 2 onward: 1–3 sentences of explanation or interesting context.\n"
            "Do not repeat the expression back verbatim. Be concise."
        )

    resp = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    explanation = resp.content[0].text.strip()

    final_result = state.get("raw_result") or ("Error" if state.get("error") else "")

    return {
        **state,
        "result": final_result,
        "explanation": explanation,
    }


# ─────────────────────────── Routing ──────────────────────────────────────────

MAX_RETRIES = 1

def route_after_execute(state: CalcState) -> str:
    """If execution failed and we haven't retried yet, go back and try again."""
    if state.get("error") and state.get("retries", 0) < MAX_RETRIES:
        return "retry"
    return "format"


def retry_node(state: CalcState) -> CalcState:
    """Bump the retry counter then hand off to interpret again."""
    return {**state, "retries": state.get("retries", 0) + 1}


# ─────────────────────────── Helpers ──────────────────────────────────────────

def _serialize(value, precision: int) -> str:
    """Turn any math result into a readable string."""
    if value is None:
        return "None"

    # Sympy types
    try:
        import sympy
        if isinstance(value, (sympy.Basic, sympy.MatrixBase)):
            sym_str = str(value)
            try:
                num = float(sympy.N(value, precision))
                if abs(num - round(num)) < 1e-12 and abs(num) < 1e15:
                    return str(int(round(num)))
                numeric = f"{num:.{precision}g}"
                return sym_str if sym_str == numeric else f"{sym_str}  ≈  {numeric}"
            except Exception:
                return sym_str
    except ImportError:
        pass

    # Lists / tuples (e.g. multiple solutions)
    if isinstance(value, (list, tuple)):
        return str([_serialize(v, precision) for v in value])

    # numpy arrays
    try:
        import numpy as np
        if isinstance(value, np.ndarray):
            return np.array2string(value, precision=precision, suppress_small=True)
    except ImportError:
        pass

    # Complex
    if isinstance(value, complex):
        return f"{value.real:.{precision}g} + {value.imag:.{precision}g}i"

    # Floats
    if isinstance(value, float):
        if value == int(value) and abs(value) < 1e15:
            return str(int(value))
        return f"{value:.{precision}g}"

    return str(value)


# ─────────────────────────── Graph assembly ───────────────────────────────────

def build_graph():
    wf = StateGraph(CalcState)

    wf.add_node("interpret", interpret_node)
    wf.add_node("execute", execute_node)
    wf.add_node("retry", retry_node)
    wf.add_node("format", format_node)

    wf.set_entry_point("interpret")
    wf.add_edge("interpret", "execute")
    wf.add_conditional_edges(
        "execute",
        route_after_execute,
        {"retry": "retry", "format": "format"},
    )
    wf.add_edge("retry", "interpret")   # re-interpret with error hint
    wf.add_edge("format", END)

    return wf.compile()


graph = build_graph()
