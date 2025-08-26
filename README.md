# RAG Training Chatbot API

A simple FastAPI-based RAG (Retrieval-Augmented Generation) chatbot designed to serve as a training tool for employees using specialized training materials stored in Supabase.

## Features

- Simple `/chat` endpoint for RAG-based responses
- Integration with OpenAI GPT models
- Vector similarity search using Supabase
- No authentication or session management (as requested)
- CORS enabled for frontend integration
- Docker support for easy deployment

## Setup

### 1. Environment Variables

Copy `.env.sample` to `.env` and fill in your credentials:

```bash
cp .env.sample .env
```

Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon key

### 2. Supabase Setup

Run the SQL commands in `services/supabase_setup.sql` in your Supabase SQL editor to enable vector search functionality.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

#### Development Mode
```bash
python run.py
```

#### Production Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### DOCS
http://localhost:8000/docs

#### Using Docker
```bash
docker-compose up --build
```

## API Endpoints

### POST /chat

Send a message to the chatbot and receive a RAG-based response.

**Request Body:**
```json
{
  "message": "What is the company policy on remote work?",
  "max_tokens": 500
}
```

**Response:**
```json
{
  "response": "Based on the training materials...",
  "sources": [
    {
      "id": 123,
      "metadata": {"title": "Remote Work Policy"}
    }
  ]
}
```

### GET /health

Health check endpoint.

### GET /

Root endpoint with API information.

## Project Structure

```
├── main.py                 # FastAPI application
├── services/
│   ├── __init__.py
│   ├── rag_service.py      # RAG logic and OpenAI/Supabase integration
│   └── supabase_setup.sql  # SQL setup for vector search
├── requirements.txt        # Python dependencies
├── .env.sample            # Environment variables template
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
├── run.py                 # Development server runner
└── README.md              # This file
```

## Database Schema

The application expects the following Supabase tables:

- `storage`: Contains training documents with embeddings
  - `id`: Primary key
  - `content`: Document text content
  - `metadata`: JSON metadata about the document
  - `embedding`: Vector embedding for similarity search

## Usage

1. Populate your Supabase `storage` table with training materials and their embeddings
2. Start the API server
3. Send POST requests to `/chat` with employee questions
4. The system will find relevant training materials and generate contextual responses

## Development

The application is built with:
- FastAPI for the web framework
- OpenAI API for embeddings and chat completions
- Supabase for vector database storage
- Pydantic for request/response validation

## Notes

- No authentication or session management implemented (as requested)
- Vector search falls back to regular queries if similarity search fails
- CORS is enabled for all origins (adjust for production use)
- The system uses OpenAI's `text-embedding-3-small` for embeddings and `gpt-4o-mini` for responses