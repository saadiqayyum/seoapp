import os
from typing import TypedDict

from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    reply: str
    endpoint: str
    api_key: str


def say_hi(state: State) -> State:
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "default")
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    client = ChatAnthropic(model="claude-haiku-4-5")

    response = client.invoke("Hi!")

    return {
        "reply": response.content,
        "endpoint": base_url,
        "api_key": api_key,
    }


builder = StateGraph(State)
builder.add_node("say_hi", say_hi)
builder.add_edge(START, "say_hi")
builder.add_edge("say_hi", END)

graph = builder.compile()
