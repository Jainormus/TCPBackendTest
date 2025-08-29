import os
import asyncio
import httpx
from typing import List, Dict, Any
from dotenv import load_dotenv
import openai

from .langchain_memory import LangChainMemoryService
from .prompts import prompt_two

load_dotenv()

MAX_MESSAGES = 20

ACRONYM_MAP = {
    "TCP": "The Collaborative Process",
}

def expand_acronyms(query: str) -> str:
    """Expand known acronyms in the query."""
    for acronym, full_form in ACRONYM_MAP.items():
        if acronym.lower() in query.lower():
            query += f" ({full_form})"
    return query


class RAGService:
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and key must be set in environment variables.")

        self.supabase_headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
        }

        self.memory_service = LangChainMemoryService()

    async def get_embedding(self, text: str) -> List[float]:
        """Generate an embedding for the given text using OpenAI."""
        try:
            response = await self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise RuntimeError(f"Error generating embedding: {e}") from e

    async def search_similar_documents(self, query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents in Supabase via RPC."""
        rpc_url = f"{self.supabase_url}/rest/v1/rpc/match_documents_justin"

        payload = {
            "query_embedding": query_embedding,
            "match_threshold": 0.4,
            "match_count": limit
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(rpc_url, headers=self.supabase_headers, json=payload, timeout=30)
                response.raise_for_status()
                data = response.json()
                return data if data else []
            except httpx.HTTPError as e:
                print(f"Vector search failed: {e}")
                # Fallback to retrieving from storage table
                table_url = f"{self.supabase_url}/rest/v1/storage"
                response = await client.get(table_url, headers=self.supabase_headers, params={"limit": str(limit)}, timeout=30)
                response.raise_for_status()
                return response.json()

    async def get_rag_response(self, user_message: str, session_id: str = None, max_tokens: int = 500) -> Dict[str, Any]:
        """Generate a RAG-based AI response."""
        try:
            # Create session if not provided
            if not session_id:
                session_id = self.memory_service.create_session_id()

            # Store user message in memory
            await self.memory_service.add_user_message(session_id, user_message)

            # Get embedding & search results concurrently
            expanded_message = expand_acronyms(user_message)
            query_embedding = await self.get_embedding(expanded_message)
            similar_docs = await self.search_similar_documents(query_embedding)

            # Prepare context and sources
            context = ""
            sources = []
            for doc in similar_docs:
                if doc.get("content"):
                    context += f"{doc['content']}\n\n"
                    sources.append({
                        "id": doc.get("id"),
                        "metadata": doc.get("metadata", {})
                    })

            # Get conversation history
            conversation_history = await self.memory_service.format_messages_for_openai(session_id, limit=10)

            # Prepare system message
            system_prompt = prompt_two()
            messages = [{"role": "system", "content": system_prompt.format(context=context)}]

            # Append conversation history
            for msg in conversation_history[-MAX_MESSAGES-1:-1]:
                messages.append(msg)

            # Append current user message
            wrapped_user_message = f"<current_user_message> {user_message} <current_user_message>"
            messages.append({"role": "user", "content": wrapped_user_message})

            # Call OpenAI API
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.67
            )

            assistant_response = response.choices[0].message.content

            # Save AI response to memory
            await self.memory_service.add_ai_message(session_id, assistant_response)

            return {
                "answer": assistant_response,
                "sources": sources,
                "session_id": session_id
            }

        except Exception as e:
            raise RuntimeError(f"Error generating RAG response: {e}") from e

    async def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        return await self.memory_service.get_conversation_history(session_id, limit)

    async def create_new_session(self) -> str:
        return self.memory_service.create_session_id()

    async def clear_session(self, session_id: str) -> bool:
        try:
            await self.memory_service.clear_memory(session_id)
            return True
        except Exception as e:
            print(f"Error clearing session: {e}")
            return False
