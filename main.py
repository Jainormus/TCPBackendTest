from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from services.rag_service import RAGService

# Load environment variables
load_dotenv()

app = FastAPI(
    title="RAG Training Chatbot API",
    description="A simple RAG-based chatbot for employee training with PostgreSQL memory",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG service
rag_service = RAGService()

class ChatRequest(BaseModel):
    message: str
    session_id: str = None
    max_tokens: int = 500

class ChatResponse(BaseModel):
    response: str
    sources: list = []
    session_id: str

class SessionResponse(BaseModel):
    session_id: str
    message: str

class HistoryResponse(BaseModel):
    messages: list
    session_id: str

@app.get("/")
async def root():
    return {"message": "RAG Training Chatbot API is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response = await rag_service.get_rag_response(
            request.message, 
            request.session_id, 
            request.max_tokens
        )
        return ChatResponse(
            response=response["answer"],
            sources=response.get("sources", []),
            session_id=response["session_id"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session/new", response_model=SessionResponse)
async def create_session():
    """Create a new chat session"""
    try:
        session_id = await rag_service.create_new_session()
        return SessionResponse(
            session_id=session_id,
            message="New chat session created"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}/history", response_model=HistoryResponse)
async def get_conversation_history(session_id: str, limit: int = 10):
    """Get conversation history for a session"""
    try:
        messages = await rag_service.get_conversation_history(session_id, limit)
        return HistoryResponse(
            messages=messages,
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear memory for a session"""
    try:
        success = await rag_service.clear_session(session_id)
        if success:
            return {"message": f"Session {session_id} cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear session")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)