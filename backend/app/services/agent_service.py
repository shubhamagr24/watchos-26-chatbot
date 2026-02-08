"""
LangGraph Agent Service
"""
from typing import TypedDict, Annotated, Sequence, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

from app.core.config import settings
from app.core.prompts import SYSTEM_PROMPT
from app.services.tools import search_local_knowledge, fetch_webpage, web_search_tool


# State Schema
class AgentState(TypedDict):
    """State schema for the LangGraph agent"""
    messages: Annotated[Sequence[BaseMessage], add_messages]


# Initialize LLM
llm = ChatOpenAI(
    model=settings.LLM_MODEL,
    temperature=settings.LLM_TEMPERATURE,
    api_key=settings.OPENAI_API_KEY
)



tools = [search_local_knowledge, web_search_tool, fetch_webpage]
llm_with_tools = llm.bind_tools(tools)


# Graph Nodes
def should_continue(state: AgentState):
    """Determine whether to continue to tools or end"""
    messages = state["messages"]
    last_message = messages[-1]
    
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return "end"
    else:
        return "continue"


def call_model(state: AgentState):
    """Call the LLM with the current state"""
    messages = state["messages"]
    
    # Add system message if not present
    if not any(isinstance(msg, SystemMessage) for msg in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


# Build Graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))
workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "tools",
        "end": END,
    },
)
workflow.add_edge("tools", "agent")

# Compile the graph
graph = workflow.compile()


def process_message(user_message: str, conversation_history: list = None) -> Dict[str, Any]:
    """
    Process a user message through the LangGraph agent
    
    Args:
        user_message: The user's question
        conversation_history: Previous messages (LangChain format)
        
    Returns:
        Dict containing response and metadata
    """
    if conversation_history is None:
        conversation_history = []
    
    messages = conversation_history + [HumanMessage(content=user_message)]
    
    config = {
        "metadata": {
            "user_query": user_message[:100],
            "conversation_length": len(conversation_history)
        },
        "tags": ["watchos-26", "rag-agent"]
    }
    
    result = graph.invoke({"messages": messages}, config=config)
    
    final_message = result["messages"][-1]
    
    # Analyze which tools were used
    tools_used = []
    for msg in result["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tool_call in msg.tool_calls:
                tools_used.append(tool_call.get("name", "unknown"))
    
    return {
        "response": final_message.content,
        "tools_used": list(set(tools_used)),
        "used_local_kb": "search_local_knowledge" in tools_used,
        "used_web_search": "tavily_search_results_json" in tools_used,
        "conversation_history": result["messages"]
    }
