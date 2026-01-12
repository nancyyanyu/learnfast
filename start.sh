#!/bin/bash
set -e

# Start Ollama in background
echo "Starting Ollama..."
ollama serve &

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
sleep 5

# Check if Ollama is running
until curl -s http://localhost:11434/api/tags > /dev/null; do
    echo "Waiting for Ollama API..."
    sleep 2
done

echo "Ollama is ready. Starting FastAPI app..."

# Start FastAPI app (Render sets PORT automatically)
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
