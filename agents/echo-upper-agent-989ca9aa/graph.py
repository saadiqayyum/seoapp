from typing import TypedDict
from langgraph.graph import StateGraph, END


class State(TypedDict):
    text: str
    result: str


def echo_upper(state: State) -> dict:
    upper = state["text"].upper()
    return {"result": upper}


builder = StateGraph(State)
builder.add_node("echo_upper", echo_upper)
builder.set_entry_point("echo_upper")
builder.add_edge("echo_upper", END)

graph = builder.compile()
