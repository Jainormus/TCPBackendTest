-- LangChain PostgreSQL Setup for Supabase
-- Run this in your Supabase SQL Editor

-- Create the langchain_chat_history table (LangChain will create this automatically, but we can pre-create it)
CREATE TABLE IF NOT EXISTS langchain_chat_history (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR NOT NULL,
    message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('human', 'ai')),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_langchain_session_id ON langchain_chat_history(session_id);
CREATE INDEX IF NOT EXISTS idx_langchain_created_at ON langchain_chat_history(created_at);

-- Enable Row Level Security (RLS)
ALTER TABLE langchain_chat_history ENABLE ROW LEVEL SECURITY;

-- Create policy for public access
CREATE POLICY "Allow public access to langchain_chat_history" ON langchain_chat_history
    FOR ALL USING (true);

-- Optional: Create a function to clean old messages (older than 30 days)
CREATE OR REPLACE FUNCTION clean_old_langchain_history()
RETURNS void AS $$
BEGIN
    DELETE FROM langchain_chat_history 
    WHERE created_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;
