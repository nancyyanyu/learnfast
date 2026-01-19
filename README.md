# Notion Learning Assistant

A little tool to capture YouTube videos, blogs, and arXiv papers into Notion with AI summaries.
Survey papers are detected automatically and summarized with a dedicated prompt.

![Notion Learning Assistant UI](https://github.com/nancyyanyu/learnfast/blob/main/docs/image.png)

## Requirements
- Notion integration token and database
- Ollama (local or cloud via API key)

## Environment Variables
Create a `.env` file or set these in your shell:
- `NOTION_TOKEN` - Notion integration token
- `NOTION_DATABASE_ID` - Target Notion database ID
- `OLLAMA_MODEL` - Model name (default: `minimax-m2:cloud`)
- `OLLAMA_BASE_URL` - Local Ollama URL (default: `http://localhost:11434`)
- `OLLAMA_API_KEY` - Required for models with ollama.com

## Local Setup
Install Ollama if you plan to use a local model:
- https://ollama.com/download

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start Ollama (local models only):
```bash
ollama serve
```

Run the app:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`.

## Docker
Build and run:
```bash
docker build -t notion-assistant .
docker run --rm -p 8000:8000 \
  -e NOTION_TOKEN=... \
  -e NOTION_DATABASE_ID=... \
  -e OLLAMA_MODEL=minimax-m2:cloud \
  -e OLLAMA_API_KEY=... \
  notion-assistant
```

## Resource Types
- `youtube` -> YouTube video transcript summary
- `blog` -> Blog/article summary + takeaways
- `paper` -> arXiv paper full analysis
- `survey_paper` -> arXiv survey paper analysis (auto-detected)
