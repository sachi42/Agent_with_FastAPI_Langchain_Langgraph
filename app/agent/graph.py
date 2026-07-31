import json
from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.agent.state import AgentState
from app.config import settings
from app.tools.search import search_documents
from app.tools.summarize import summarize_text
from app.tools.calculate import calculate_expression
import os
from dotenv import load_dotenv

# Step 1: Initialize System instructions & LLM Bindings
# app/agent/graph.py

SYSTEM_PROMPT = """You are a strict research assistant. You are forbidden from answering questions using your own internal knowledge or calculating numbers yourself.

You MUST use your tools for every step of reasoning.
- To look up policies (like a refund window), you MUST call the `search_documents` action.
- To execute ANY math calculation or multiplication, you MUST call the `calculate` action.

Available actions you can call via JSON markdown blocks matching exact string schemas:
1. `{"action": "search_documents", "query": "text to search"}`
2. `{"action": "summarize", "text": "text to condense"}`
3. `{"action": "calculate", "expression": "math problem"}`

CRITICAL RULES:
- Never answer from memory. If asked about a window, call `search_documents`.
- Never do math in your head. Call `calculate` for equations.
- Only supply your definitive response prefixed with 'FINAL_ANSWER: ' AFTER you have received and evaluated the output from your tools."""


def agent_router(state: AgentState) -> Literal["call_tools", "__end__"]:
    # Safe guard criteria check: Guard ceilings
    if state.get("iteration_count", 0) >= settings.AGENT_MAX_ITERATIONS:
        return "__end__"
    
    last_msg = state["messages"][-1]["content"]
    if "FINAL_ANSWER:" in last_msg or '{"action"' not in last_msg:
        return "__end__"
    return "call_tools"

def call_llm(state: AgentState) -> dict:
    llm = ChatOpenAI(model=settings.AGENT_LLM_MODEL, api_key=os.getenv("OPENAI_API_KEY") or settings.OPENAI_API_KEY, temperature=0)
    history = [SystemMessage(content=SYSTEM_PROMPT)]
    
    for msg in state["messages"]:
        if msg["role"] == "user":
            history.append(HumanMessage(content=msg["content"]))
        else:
            history.append(AIMessage(content=msg["content"]))
            
    res = llm.invoke(history)
    current_count = state.get("iteration_count", 0) + 1
    
    return {
        "messages": [{"role": "assistant", "content": str(res.content)}],
        "iteration_count": current_count
    }

# def call_tools(state: AgentState) -> dict:
#     last_msg = state["messages"][-1]["content"]
#     tools_used = []
#     sources = []
#     new_messages = []
#     tool_error_inc = 0
    
#     # Simple, non-brittle extraction parsing loop
#     try:
#         start_idx = last_msg.find("{")
#         end_idx = last_msg.rfind("}") + 1
#         action_data = json.loads(last_msg[start_idx:end_idx])
#         action = action_data.get("action")
        
#         if action == "search_documents":
#             tools_used.append("search_documents")
#             out = search_documents(action_data["query"])
#             if "ERROR_OR_EMPTY" not in out:
#                 sources.append(out)
#             new_messages.append({"role": "user", "content": f"Tool output: {out}"})
            
#         elif action == "summarize":
#             tools_used.append("summarize")
#             out = summarize_text(action_data["text"])
#             new_messages.append({"role": "user", "content": f"Tool output: {out}"})
            
#         elif action == "calculate":
#             tools_used.append("calculate")
#             out = calculate_expression(action_data["expression"])
#             new_messages.append({"role": "user", "content": f"Tool output: {out}"})
#         else:
#             raise ValueError("Unknown action schema triggered.")
            
#     except Exception as e:
#         tool_error_inc = 1
#         new_messages.append({"role": "user", "content": f"TOOL_FAILURE: Could not evaluate operation. {str(e)}"})
        
#     return {
#         "messages": new_messages,
#         "tools_used": tools_used,
#         "sources": sources,
#         "tool_errors": state.get("tool_errors", 0) + tool_error_inc
#     }

def call_tools(state: AgentState) -> dict:
    # 1. Isolate the absolute latest assistant response message explicitly
    assistant_messages = [m for m in state["messages"] if m.get("role") == "assistant"]
    if not assistant_messages:
        return {"messages": [{"role": "user", "content": "ERROR: No assistant instruction found to route."}]}
        
    last_msg = assistant_messages[-1]["content"]
    
    # 2. Local trackers initialized as fresh blank slates for THIS turn only
    current_turn_tools = []
    current_turn_sources = []
    new_messages = []
    
    # 3. Defensive checks to verify if an action string exists in the active turn
    if '{"action"' not in last_msg:
        return {} # Exit cleanly without appending stale state records
        
    try:
        start_idx = last_msg.find("{")
        end_idx = last_msg.rfind("}") + 1
        action_data = json.loads(last_msg[start_idx:end_idx])
        action = action_data.get("action")
        
        if action == "search_documents":
            current_turn_tools.append("search_documents")
            out = search_documents(action_data["query"])
            if "ERROR_OR_EMPTY" not in out:
                current_turn_sources.append(out)
            new_messages.append({"role": "user", "content": f"Tool output: {out}"})
            
        elif action == "summarize":
            current_turn_tools.append("summarize")
            out = summarize_text(action_data["text"])
            new_messages.append({"role": "user", "content": f"Tool output: {out}"})
            
        elif action == "calculate":
            current_turn_tools.append("calculate")
            out = calculate_expression(action_data["expression"])
            new_messages.append({"role": "user", "content": f"Tool output: {out}"})
            
    except Exception as e:
        new_messages.append({"role": "user", "content": f"TOOL_FAILURE: Exception hit on string parsing. {str(e)}"})
        
    # 4. Return only fields updated during this isolated graph step execution
    return {
        "messages": new_messages,
        "tools_used": current_turn_tools,
        "sources": current_turn_sources
    }

# Build and Compile Graph with standard In-Memory Session Checkpointer
builder = StateGraph(AgentState)
builder.add_node("call_llm", call_llm)
builder.add_node("call_tools", call_tools)

builder.set_entry_point("call_llm")
builder.add_conditional_edges("call_llm", agent_router)
builder.add_edge("call_tools", "call_llm")

# MemorySaver satisfies the explicit submission requirement for transactional separation
memory_checkpointer = MemorySaver()
compiled_graph = builder.compile(checkpointer=memory_checkpointer)

# Save the graph directly to a file
# try:
#     image_data = compiled_graph.get_graph().draw_mermaid_png()
#     with open("graph_visualization.png", "wb") as f:
#         f.write(image_data)
#     print("Graph image saved successfully as 'graph_visualization.png'")
# except Exception as e:
#     print(f"Could not generate PNG directly: {e}")
