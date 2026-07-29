## this file is the main file containing the FastAPI endpoints, SSE endpoints
import json
import asyncio
from fastapi import FastAPI, HTTPException, status
from app.schemas import DocumentIngestRequest, IngestResponse
from app.tools.search import vector_store


app = FastAPI(title="Production Research Agent microservice")

@app.post("/documents", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_documents(payload: DocumentIngestRequest):
    try:
        vector_store.add_documents(payload.documents)
        return IngestResponse(count=len(payload.documents), message="Documents ingested successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))