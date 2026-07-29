from pydantic import BaseModel, Field
from typing import List, Optional

class DocumentIngestRequest(BaseModel):
    documents: List[str] = Field(..., min_items=1)

class IngestResponse(BaseModel):
    count: int
    message: str

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    session_id: str
    response: str
    tools_used: List[str]
    sources: List[str]
    turn: int
