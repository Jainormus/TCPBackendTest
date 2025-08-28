import os
import openai
from supabase import create_client, Client
import numpy as np
from typing import List, Dict, Any

class RAGService:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        
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
    
    async def get_rag_response(self, user_message: str, max_tokens: int = 500) -> Dict[str, Any]:
        """Generate RAG response using OpenAI and Supabase"""
        try:
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
            
            # Create prompt with context
            system_prompt = """You are TCP (also known as The Collaborative process) RAG Chatbot, a mentor built on The Collaborative Process, a framework that helps teams work better together and cut inefficiencies. You will use the database tool to answer users' questions authentically and engagingly. For each user prompt you will be injected with relevant database context to help formulate a valid response.

# CORE CHARACTERISTICS:
- ANSWER IN PARAGRAPHS
- Every instance of TCP stands for the The Collaborative Process
- Speak naturally and informally while maintaining expertise
- Balance insights with everyday language
- When replying answer in ordered paragraphs based on what you are saying

2. Language Patterns:
- Use connector phrases ('you know,' 'look,' 'think about this')
- Incorporate strategic pauses for emphasis (...)
- Balance professional terms with accessible explanations

# RULES:
1. Always use the database information to try and answer
2. Never fabricate answers - if information isn't in the database, acknowledge it
3. Maintain authentic, conversational style while delivering expert advice
4. Balance empathy with professional insights
5. Use clear examples to illustrate complex concepts
6. Ensure responses are both engaging and informative
7. Before answering a question ask questions to determent the situation of the user ask the questions one by so they won't get overwhelmed
8. If the user says something like "I want to kill myself" or something along those lines that implies that they can possibly have the idea of harming themselves use the disclaimer.
9. Avoid responding in big walls of text always seperate your response

<TCP DATA INFORMATION>
{context}
<TCP DATA INFORMATION>

"""

            user_prompt = f"Question: {user_message}"
            
            # Generate response using OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt.format(context=context)},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return {
                "answer": response.choices[0].message.content,
                "sources": sources
            }
            
        except Exception as e:
            raise Exception(f"Error generating RAG response: {str(e)}")
