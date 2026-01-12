#!/bin/bash

# Setup script for Ollama on macOS
# Run this after installing Ollama from https://ollama.com/download

set -e

echo "🚀 Setting up Ollama for Notion Assistant..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed or not in PATH."
    echo "📥 Please download and install Ollama from: https://ollama.com/download"
    echo "   After installation, make sure to add Ollama to your PATH or restart your terminal."
    exit 1
fi

echo "✅ Ollama is installed!"

# Start Ollama service in background (if not already running)
echo "🔄 Starting Ollama service..."
if ! pgrep -x "ollama" > /dev/null; then
    ollama serve &
    sleep 3
    echo "✅ Ollama service started"
else
    echo "✅ Ollama service is already running"
fi

# Pull the model
echo "📦 Downloading llama3.2:3b model (this may take a few minutes, ~2GB)..."
ollama pull llama3.2:3b

# Verify installation
echo "🧪 Testing the model..."
ollama run llama3.2:3b "Say 'Hello, setup complete!' in one sentence" --verbose

echo ""
echo "✅ Setup complete! Ollama is ready to use."
echo ""
echo "📝 Next steps:"
echo "   1. Make sure Ollama service is running: ollama serve"
echo "   2. Install Python dependencies: pip install -r requirements.txt"
echo "   3. Run your app: python main.py"
echo ""
