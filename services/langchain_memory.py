import os
import uuid
from datetime import datetime
from typing import List, Dict, Any
import httpx
from dotenv import load_dotenv

load_dotenv()

class LangChainMemoryService:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and key must be set in environment variables.")

        self.supabase_headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
        }

    def create_session_id(self) -> str:
        """Generate a unique session ID."""
        return str(uuid.uuid4())

    async def add_user_message(self, session_id: str, message: str) -> None:
        """Add a user message to the conversation."""
        payload = [{
            'session_id': session_id,
            'message_type': 'human',
            'content': message,
            'created_at': datetime.utcnow().isoformat()
        }]
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{self.supabase_url}/rest/v1/langchain_chat_history",
                    headers=self.supabase_headers,
                    json=payload,
                    timeout=30
                )
            except httpx.HTTPError as e:
                print(f"Error adding user message: {e}")

    async def add_ai_message(self, session_id: str, message: str) -> None:
        """Add an AI message to the conversation."""
        payload = [{
            'session_id': session_id,
            'message_type': 'ai',
            'content': message,
            'created_at': datetime.utcnow().isoformat()
        }]
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{self.supabase_url}/rest/v1/langchain_chat_history",
                    headers=self.supabase_headers,
                    json=payload,
                    timeout=30
                )
            except httpx.HTTPError as e:
                print(f"Error adding AI message: {e}")

    async def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Get conversation history for a session."""
        params = {
            "session_id": f"eq.{session_id}",
            "select": "message_type,content,created_at",
            "order": "created_at.asc",
            "limit": str(limit)
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.supabase_url}/rest/v1/langchain_chat_history",
                    headers=self.supabase_headers,
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()

                if not data:
                    return []

                # Format for OpenAI API
                return [
                    {"role": "user" if msg["message_type"] == "human" else "assistant", "content": msg["content"]}
                    for msg in data
                ]
            except httpx.HTTPError as e:
                print(f"Error getting conversation history: {e}")
                return []

    async def format_messages_for_openai(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Format conversation history for OpenAI API."""
        return await self.get_conversation_history(session_id, limit)

    async def clear_memory(self, session_id: str) -> None:
        """Clear memory for a session."""
        async with httpx.AsyncClient() as client:
            try:
                await client.delete(
                    f"{self.supabase_url}/rest/v1/langchain_chat_history",
                    headers=self.supabase_headers,
                    params={"session_id": f"eq.{session_id}"},
                    timeout=30
                )
            except httpx.HTTPError as e:
                print(f"Error clearing memory: {e}")
