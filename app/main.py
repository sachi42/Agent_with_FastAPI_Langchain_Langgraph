## this file is the main file containing the FastAPI endpoints, SSE endpoints
import json
import asyncio
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse
from app.schemas import ChatRequest, ChatResponse, DocumentIngestRequest, IngestResponse
from app.tools.search import vector_store
from app.agent.graph import compiled_graph


app = FastAPI(title="Production Research Agent microservice")

## Route created to process the data ingestion.
@app.post("/documents", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_documents(payload: DocumentIngestRequest):
    try:
        vector_store.add_documents(payload.documents)
        return IngestResponse(count=len(payload.documents), message="Documents ingested successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

## this is currently working fine, but currently we have a functionality where even if we are asking any new query but we for same session-is,
## we have the tools list getting appended with the previous used tools and same for turn
# @app.post("/chat", response_model=ChatResponse)
# async def sync_chat_endpoint(payload: ChatRequest):
#     # Mapping configuration context session_id securely to thread_id
#     config = {"configurable": {"thread_id": payload.session_id}}
#     initial_input = {
#         "messages": [{"role": "user", "content": payload.message}],
#         "session_id": payload.session_id,
#         "iteration_count": 0,
#         "tool_errors": 0,
#         "tools_used": [],
#         "sources": []
#     }
    
#     try:
#         output_state = await compiled_graph.ainvoke(initial_input, config=config)
#         last_content = output_state["messages"][-1]["content"]
#         clean_ans = last_content.replace("FINAL_ANSWER:", "").strip()
        
#         return ChatResponse(
#             session_id=payload.session_id,
#             response=clean_ans,
#             tools_used=output_state.get("tools_used", []),
#             sources=output_state.get("sources", []),
#             turn=len(output_state["messages"]) // 2
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# app/main.py

@app.post("/chat", response_model=ChatResponse)
async def sync_chat_endpoint(payload: ChatRequest):
    config = {"configurable": {"thread_id": payload.session_id}}
    
    # CRITICAL: We pass empty arrays here, but LangGraph's state reducer
    # might append them if not handled. To force an overwrite on a new turn:
    initial_input = {
        "messages": [{"role": "user", "content": payload.message}],
        "session_id": payload.session_id,
        "iteration_count": 0,
        "tool_errors": 0,
        # Force-reset the tracker keys for this specific request cycle
        "tools_used": [], 
        "sources": []
    }
    
    try:
        # Update the state checkpoint first to clear out historical trackers
        await compiled_graph.aupdate_state(config, {"tools_used": [], "sources": []})
        
        # Invoke the graph engine
        output_state = await compiled_graph.ainvoke(initial_input, config=config)
        last_content = output_state["messages"][-1]["content"]
        clean_ans = last_content.replace("FINAL_ANSWER:", "").strip()
        
        return ChatResponse(
            session_id=payload.session_id,
            response=clean_ans,
            tools_used=output_state.get("tools_used", []),
            sources=output_state.get("sources", []),
            turn=len(output_state["messages"]) // 2
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def stream_chat_endpoint(payload: ChatRequest):
    config = {"configurable": {"thread_id": payload.session_id}}
    initial_input = {
        "messages": [{"role": "user", "content": payload.message}],
        "session_id": payload.session_id,
        "iteration_count": 0,
        "tool_errors": 0,
        "tools_used": [],
        "sources": []
    }
    async def event_generator():
        try:
            # Using .astream to yield step updates immediately across nodes
            async for chunk in compiled_graph.astream(initial_input, config=config, stream_mode="updates"):
                for node_name, updated_fields in chunk.items():
                    # Format matching requirement guidelines: emit progress per step completed
                    event_payload = {
                        "event": "progress" if node_name == "call_llm" else "tool_result",
                        "node": node_name,
                        "data": {k: updated_fields[k] for k in updated_fields if k != "messages"}
                    }
                    yield f"data: {json.dumps(event_payload)}\n\n"
                    await asyncio.sleep(0.01) # Yield execution handle thread cleanly
                    
            # Complete execution trace recovery data dump
            final_snapshot = await compiled_graph.aget_state(config)
            final_msg = final_snapshot.values["messages"][-1]["content"].replace("FINAL_ANSWER:", "").strip()
            
            yield f"data: {json.dumps({'event': 'final_message', 'response': final_msg})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'recovery_status': 'failed', 'detail': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")