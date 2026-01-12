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

echo "Ollama is ready. Checking for model..."

# Get the model name from environment variable or use default
MODEL_NAME=${OLLAMA_MODEL:-minimax-m2:cloud}

# For cloud models, check if authentication is needed
if [[ "$MODEL_NAME" == *":cloud"* ]]; then
    echo "Cloud model detected: $MODEL_NAME"
    echo "Note: Cloud models require Ollama.com authentication."
    
    # Check for OLLAMA_API_KEY
    if [ -n "$OLLAMA_API_KEY" ]; then
        echo "OLLAMA_API_KEY found. Using direct ollama.com API access."
        echo "The application will connect to https://ollama.com with API key authentication."
        export OLLAMA_API_KEY
    else
        echo "Warning: No OLLAMA_API_KEY found for cloud model."
        echo "Cloud models require OLLAMA_API_KEY to work."
        echo "Please set OLLAMA_API_KEY environment variable."
        echo "The application will attempt to use local Ollama server (may not work for cloud models)."
    fi
fi

# Only check/pull models if using local Ollama server
# For cloud models with API key, we'll use ollama.com API directly
if [[ "$MODEL_NAME" != *":cloud"* ]] || [ -z "$OLLAMA_API_KEY" ]; then
    # Check if model exists, if not pull it (only for local models or if no API key)
    if ! ollama list | grep -q "$MODEL_NAME"; then
        echo "Model $MODEL_NAME not found. Pulling model..."
        ollama pull "$MODEL_NAME" || {
            echo "Warning: Failed to pull $MODEL_NAME."
            if [[ "$MODEL_NAME" == *":cloud"* ]]; then
                echo "Cloud models require authentication."
                echo "Please set OLLAMA_API_KEY environment variable."
            fi
            echo "Attempting to continue anyway - model may be available via cloud if authenticated."
        }
    else
        echo "Model $MODEL_NAME is already available."
    fi
else
    echo "Skipping local model pull - will use ollama.com API directly with API key."
fi

echo "Starting FastAPI app..."

# Start FastAPI app (Render sets PORT automatically)
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
