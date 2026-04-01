from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages
import operator

from agents.reasoning_agent import reasoning_agent
from agents.router_agent import router_agent
from agents.research_agent import research_agent
from agents.tool_agent import tool_agent
from agents.memory_agent import memory_agent
from agents.interview_agent import interview_agent


class State(TypedDict):
    messages: Annotated[list, add_messages]
    next: str
    user_id: str
    iterations: Annotated[int, operator.add]
    agent_used: str
    emotion_context: Optional[dict]


def route_decision(state):
    return state["next"]


def build_graph():
    graph = StateGraph(State)

    # Nodes
    graph.add_node("router", router_agent)
    graph.add_node("reasoning", reasoning_agent)
    graph.add_node("research", research_agent)
    graph.add_node("tools", tool_agent)
    graph.add_node("memory", memory_agent)
    graph.add_node("interview", interview_agent)

    # Start
    graph.add_edge(START, "router")

    # Routing logic
    graph.add_conditional_edges(
        "router",
        route_decision,
        {
            "reasoning": "reasoning",
            "research": "research",
            "tools": "tools",
            "memory": "memory",
            "interview": "interview",
            "finish": END,
        }
    )

    # Loop back to router
    graph.add_edge("reasoning", "router")
    graph.add_edge("research", "router")
    graph.add_edge("tools", "router")
    graph.add_edge("memory", "router")
    graph.add_edge("interview", "router")

    return graph.compile()