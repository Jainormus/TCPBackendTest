import os
import uuid
from datetime import datetime
from supabase import create_client, Client
from typing import List, Dict, Any, Optional

class LangChainMemoryService:
    def __init__(self):
        # Use the same Supabase client as your existing setup - no extra credentials needed!
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        
    def create_session_id(self) -> str:
        """Generate a unique session ID"""
        return str(uuid.uuid4())
    
    async def add_user_message(self, session_id: str, message: str) -> None:
        """Add a user message to the conversation"""
        try:
            message_data = {
                'session_id': session_id,
                'message_type': 'human',
                'content': message,
                'created_at': datetime.utcnow().isoformat()
            }
            
            self.supabase.table('langchain_chat_history').insert(message_data).execute()
        except Exception as e:
            print(f"Error adding user message: {str(e)}")
    
    async def add_ai_message(self, session_id: str, message: str) -> None:
        """Add an AI message to the conversation"""
        try:
            message_data = {
                'session_id': session_id,
                'message_type': 'ai',
                'content': message,
                'created_at': datetime.utcnow().isoformat()
            }
            
            self.supabase.table('langchain_chat_history').insert(message_data).execute()
        except Exception as e:
            print(f"Error adding AI message: {str(e)}")
    
    async def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Get conversation history for a session"""
        try:
            result = self.supabase.table('langchain_chat_history')\
                .select('message_type, content')\
                .eq('session_id', session_id)\
                .order('created_at', desc=False)\
                .limit(limit)\
                .execute()
            
            if not result.data:
                return []
            
            # Format for OpenAI API - convert 'human' to 'user' and 'ai' to 'assistant'
            formatted_messages = []
            for msg in result.data:
                role = 'user' if msg['message_type'] == 'human' else 'assistant'
                formatted_messages.append({
                    "role": role,
                    "content": msg['content']
                })
            
            return formatted_messages
        except Exception as e:
            print(f"Error getting conversation history: {str(e)}")
            return []
    
    async def format_messages_for_openai(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Format conversation history for OpenAI API"""
        return await self.get_conversation_history(session_id, limit)
    
    async def clear_memory(self, session_id: str) -> None:
        """Clear memory for a session"""
        try:
            self.supabase.table('langchain_chat_history')\
                .delete()\
                .eq('session_id', session_id)\
                .execute()
        except Exception as e:
            print(f"Error clearing memory: {str(e)}")
