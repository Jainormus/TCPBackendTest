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
    description="A simple RAG-based chatbot for employee training",
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
    max_tokens: int = 500

class ChatResponse(BaseModel):
    response: str
    sources: list = []

@app.get("/")
async def root():
    return {"message": "RAG Training Chatbot API is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response = await rag_service.get_rag_response(request.message, request.max_tokens)
        return ChatResponse(
            response=response["answer"],
            sources=response.get("sources", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)