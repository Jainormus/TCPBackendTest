import os
import openai
from supabase import create_client, Client
import numpy as np
from typing import List, Dict, Any
from .langchain_memory import LangChainMemoryService
from .prompts import *

class RAGService:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        self.memory_service = LangChainMemoryService()
        
    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for the given text using OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"Error generating embedding: {str(e)}")
    
    async def search_similar_documents(self, query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents in Supabase vector database"""
        try:
            # Use Supabase's vector similarity search
            result = self.supabase.rpc(
                'match_documents_justin',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': 0.4,
                    'match_count': limit
                }
            ).execute()
            
            return result.data if result.data else []
        except Exception as e:
            # Fallback to regular query if vector search fails
            print(f"Vector search failed, using fallback: {str(e)}")
            result = self.supabase.table('storage').select('*').limit(limit).execute()
            return result.data if result.data else []
    
    async def get_rag_response(self, user_message: str, session_id: str = None, max_tokens: int = 500) -> Dict[str, Any]:
        """Generate RAG response using OpenAI and Supabase with LangChain memory"""
        try:
            # Create session if not provided
            if not session_id:
                session_id = self.memory_service.create_session_id()
            
            # Add user message to LangChain memory
            await self.memory_service.add_user_message(session_id, user_message)
            
            # Generate embedding for user query
            query_embedding = await self.get_embedding(user_message)
            
            # Search for similar documents
            similar_docs = await self.search_similar_documents(query_embedding)
            
            # Prepare context from retrieved documents
            context = ""
            sources = []
            
            for doc in similar_docs:
                if doc.get('content'):
                    context += f"{doc['content']}\n\n"
                    sources.append({
                        'id': doc.get('id'),
                        'metadata': doc.get('metadata', {})
                    })
            
            # Get conversation history from LangChain (automatically limited to last 10 messages)
            conversation_history = await self.memory_service.format_messages_for_openai(session_id, limit=10)
            
            # Create prompt with context
            system_prompt = prompt_two()

            # Prepare messages for OpenAI
            messages = [{"role": "system", "content": system_prompt.format(context=context)}]
            
            # Add conversation history from LangChain (excluding the current user message)
            for msg in conversation_history[:-1]:  # Exclude the current user message
                messages.append(msg)
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Generate response using OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            assistant_response = response.choices[0].message.content
            
            # Add AI response to LangChain memory
            await self.memory_service.add_ai_message(session_id, assistant_response)
            
            return {
                "answer": assistant_response,
                "sources": sources,
                "session_id": session_id
            }
            
        except Exception as e:
            raise Exception(f"Error generating RAG response: {str(e)}")
    
    async def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get conversation history for a session"""
        return await self.memory_service.get_conversation_history(session_id, limit)
    
    async def create_new_session(self) -> str:
        """Create a new chat session"""
        return self.memory_service.create_session_id()
    
    async def clear_session(self, session_id: str) -> bool:
        """Clear memory for a session"""
        try:
            await self.memory_service.clear_memory(session_id)
            return True
        except Exception as e:
            print(f"Error clearing session: {str(e)}")
            return False
