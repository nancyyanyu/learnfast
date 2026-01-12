# Local LLM Setup with Ollama

This application now uses **Ollama** with **Llama 3.2 3B** for local inference, eliminating API costs.

## Quick Setup

### 1. Install Ollama

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download from [ollama.com](https://ollama.com/download)

### 2. Start Ollama Service

```bash
ollama serve
```

This starts the Ollama server on `http://localhost:11434` (default).

### 3. Pull the Model

In a new terminal, pull the recommended model:

```bash
ollama pull llama3.2:3b
```

This downloads ~2GB. The model will be cached locally.

### 4. Verify Installation

Test that Ollama is working:

```bash
ollama run llama3.2:3b "Summarize AI in one sentence"
```

### 5. Update Environment Variables (Optional)

If you're running Ollama on a different host/port, update your `.env`:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

## Alternative Models

If you want a different model, you can use:

- **Smaller/Faster:** `phi3:mini` (~2.3GB)
- **Better Quality:** `llama3.2:1b` (even smaller) or `mistral:7b` (larger, better quality)
- **Multilingual:** `qwen2.5:3b` (excellent for non-English content)

Pull any model with: `ollama pull <model-name>`

## Running the Application

1. Make sure Ollama is running (`ollama serve`)
2. Install Python dependencies: `pip install -r requirements.txt`
3. Run the app: `python main.py`

## Performance Notes

- **First request** may be slower as the model loads into memory
- **Subsequent requests** are faster (model stays in memory)
- **Memory usage:** ~4-6GB RAM for llama3.2:3b
- **Inference speed:** ~10-30 tokens/second on modern CPUs, faster on GPU

## Troubleshooting

**Error: "Failed to connect to Ollama"**
- Make sure `ollama serve` is running
- Check that `OLLAMA_BASE_URL` in `.env` matches your Ollama server

**Error: "model not found"**
- Run `ollama pull llama3.2:3b` to download the model
- Verify with `ollama list`

**Slow inference:**
- Consider using a smaller model like `phi3:mini`
- Or use a GPU-accelerated setup (see Ollama docs)
