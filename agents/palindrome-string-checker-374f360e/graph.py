from typing import TypedDict
from langgraph.graph import StateGraph, END


class PalindromeState(TypedDict):
    input_string: str
    cleaned: str
    is_palindrome: bool
    result_message: str


def clean_input(state: PalindromeState) -> PalindromeState:
    """Lowercase and remove non-alphanumeric characters for a fair check."""
    raw = state["input_string"]
    cleaned = "".join(ch.lower() for ch in raw if ch.isalnum())
    return {**state, "cleaned": cleaned}


def check_palindrome(state: PalindromeState) -> PalindromeState:
    """Check whether the cleaned string is a palindrome."""
    cleaned = state["cleaned"]
    is_palindrome = cleaned == cleaned[::-1]
    return {**state, "is_palindrome": is_palindrome}


def format_result(state: PalindromeState) -> PalindromeState:
    """Format a human-readable result message."""
    original = state["input_string"]
    if state["is_palindrome"]:
        msg = f'✅ "{original}" IS a palindrome.'
    else:
        msg = f'❌ "{original}" is NOT a palindrome.'
    return {**state, "result_message": msg}


# Build the graph
builder = StateGraph(PalindromeState)

builder.add_node("clean_input", clean_input)
builder.add_node("check_palindrome", check_palindrome)
builder.add_node("format_result", format_result)

builder.set_entry_point("clean_input")
builder.add_edge("clean_input", "check_palindrome")
builder.add_edge("check_palindrome", "format_result")
builder.add_edge("format_result", END)

graph = builder.compile()
