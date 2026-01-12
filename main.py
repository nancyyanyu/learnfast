import os
import re
import json
import requests
import io
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Union
from bs4 import BeautifulSoup

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from notion_client import Client
from youtube_transcript_api import YouTubeTranscriptApi
import trafilatura
import pdfplumber

# --- CONFIGURATION & SETUP ---
load_dotenv()

app = FastAPI(title="Notion Learning Assistant")
templates = Jinja2Templates(directory="templates")

# Initialize Clients
notion = Client(auth=os.getenv("NOTION_TOKEN"))

# Local LLM Configuration (Ollama)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "minimax-m2:cloud")  # Minimax M2 cloud model

MAX_INPUT_CHARS = 25000  # Approx 6k-8k tokens, safe buffer for 1.5 Flash

# Load paper prompt
PAPER_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "paper_prompt.txt")
PAPER_PROMPT = ""
if os.path.exists(PAPER_PROMPT_PATH):
    with open(PAPER_PROMPT_PATH, 'r', encoding='utf-8') as f:
        PAPER_PROMPT = f.read().strip()

# --- HELPER FUNCTIONS ---

def get_youtube_id(url: str) -> Optional[str]:
    """Extracts video ID from various YouTube URL formats."""
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)
    return match.group(1) if match else None

def is_arxiv_url(url: str) -> bool:
    """Checks if URL is an arXiv paper URL."""
    return "arxiv.org" in url.lower() and ("/abs/" in url or "/pdf/" in url)

def get_arxiv_pdf_url(url: str) -> str:
    """Converts arXiv abstract URL to PDF URL."""
    # Handle different arXiv URL formats
    if "/abs/" in url:
        # Convert /abs/ to /pdf/ and add .pdf
        pdf_url = url.replace("/abs/", "/pdf/") + ".pdf"
    elif "/pdf/" in url and not url.endswith(".pdf"):
        pdf_url = url + ".pdf"
    elif url.endswith(".pdf"):
        pdf_url = url
    else:
        raise ValueError("Invalid arXiv URL format")
    return pdf_url

def extract_pdf_content(pdf_url: str) -> str:
    """Downloads PDF from URL and extracts text content."""
    try:
        # Download PDF
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        # Extract text from PDF
        pdf_bytes = io.BytesIO(response.content)
        full_text = []
        
        with pdfplumber.open(pdf_bytes) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text.append(text)
        
        if not full_text:
            raise ValueError("Could not extract text from PDF. The PDF might be image-based or corrupted.")
        
        return "\n\n".join(full_text)
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to download PDF: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to extract PDF content: {str(e)}")

def extract_youtube_title(url: str) -> str:
    """Extracts YouTube video title from the page."""
    try:
        yt_id = get_youtube_id(url)
        if not yt_id:
            return "YouTube Video"
        
        # Use YouTube oEmbed API to get title
        oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
        response = requests.get(oembed_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("title", "YouTube Video")
        
        # Fallback: scrape the page
        page_response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if page_response.status_code == 200:
            soup = BeautifulSoup(page_response.text, 'html.parser')
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text().strip()
                # Remove " - YouTube" suffix if present
                title = re.sub(r'\s*-\s*YouTube\s*$', '', title)
                return title if title else "YouTube Video"
        
        return "YouTube Video"
    except Exception as e:
        print(f"Failed to extract YouTube title: {e}")
        return "YouTube Video"

def extract_blog_title(url: str) -> str:
    """Extracts blog/article title using trafilatura."""
    try:
        downloaded = trafilatura.fetch_url(url)
        metadata = trafilatura.extract_metadata(downloaded)
        
        if metadata and metadata.title:
            return metadata.title.strip()
        
        # Fallback: extract from HTML title tag
        soup = BeautifulSoup(downloaded, 'html.parser')
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text().strip()
            return title if title else "Blog Article"
        
        return "Blog Article"
    except Exception as e:
        print(f"Failed to extract blog title: {e}")
        return "Blog Article"

def extract_paper_title(url: str) -> str:
    """Extracts paper title from arXiv page."""
    try:
        # Get the abstract page (even if URL is PDF)
        abs_url = url.replace("/pdf/", "/abs/").replace(".pdf", "")
        if "/abs/" not in abs_url:
            # If it's already an abs URL, use it
            if "/abs/" not in url:
                abs_url = url
        
        response = requests.get(abs_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # arXiv papers have title in <h1 class="title mathjax">
            title_tag = soup.find("h1", class_="title")
            if title_tag:
                title = title_tag.get_text().strip()
                # Remove "Title:" prefix if present
                title = re.sub(r'^Title:\s*', '', title, flags=re.IGNORECASE)
                return title if title else "Research Paper"
            
            # Fallback: use page title
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text().strip()
                return title if title else "Research Paper"
        
        return "Research Paper"
    except Exception as e:
        print(f"Failed to extract paper title: {e}")
        return "Research Paper"

def extract_resource_title(url: str, resource_type: str) -> str:
    """Extracts title based on resource type."""
    if resource_type == "youtube":
        return extract_youtube_title(url)
    elif resource_type == "blog":
        return extract_blog_title(url)
    elif resource_type == "paper":
        return extract_paper_title(url)
    else:
        return "Resource"

def fetch_content(url: str, resource_type: str) -> str:
    """Fetches text content from a URL based on resource type."""
    
    if resource_type == "youtube":
        yt_id = get_youtube_id(url)
        if not yt_id:
            raise ValueError("Invalid YouTube URL. Please provide a valid YouTube video URL.")
        
        try:
            # Create API instance and fetch transcript
            api = YouTubeTranscriptApi()
            transcript = api.fetch(yt_id)
            # Combine transcript text (transcript items have .text attribute)
            full_text = " ".join([item.text for item in transcript])
            return f"Type: YouTube Video\nContent: {full_text}"
        except Exception as e:
            print(f"Transcript failed: {e}. Returning metadata placeholder.")
            return "Type: YouTube Video (No Transcript Available). Please summarize based on the title/topic inferred from the URL."
    
    elif resource_type == "paper":
        if not is_arxiv_url(url):
            raise ValueError("Paper extraction currently only supports arXiv URLs. Please provide an arXiv paper URL (e.g., https://arxiv.org/abs/XXXX.XXXXX).")
        
        try:
            pdf_url = get_arxiv_pdf_url(url)
            paper_text = extract_pdf_content(pdf_url)
            return f"Type: Research Paper (arXiv)\nContent: {paper_text}"
        except Exception as e:
            raise Exception(f"Failed to extract paper content: {str(e)}")
    
    elif resource_type == "blog":
        # Web Article/Blog
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded)
        if not text:
            raise ValueError("Could not extract content from this URL. Please ensure it's a valid article/blog URL.")
        return f"Type: Blog/Article\nContent: {text}"
    
    else:
        raise ValueError(f"Unknown resource type: {resource_type}")

def generate_summary(text: str, resource_type: str = "blog") -> Union[str, dict]:
    """
    Summarizes content using local Ollama LLM.
    Returns raw text for papers, dict with 'summary' and 'takeaways' for blog/youtube.
    
    Args:
        text: Content to summarize
        resource_type: Type of resource ('paper', 'youtube', 'blog')
    
    Returns:
        For papers: str (raw response)
        For blog/youtube: dict with 'summary' and 'takeaways' keys
    """
    # Truncate to save tokens
    truncated_text = text[:MAX_INPUT_CHARS]
    
    if resource_type == "paper" and PAPER_PROMPT:
        # Use specialized paper prompt (no JSON format)
        prompt = f"""{PAPER_PROMPT}

请基于以下论文内容进行分析。请严格按照上述要求，用中文进行详细分析。

论文内容：
{truncated_text}"""
    else:
        # Use default prompt for blog/youtube (with JSON format)
        prompt = f"""You are a helpful research assistant. 
1. Detect the language of the following text.
2. Provide a concise summary (approx 3-5 sentences) IN THE SAME LANGUAGE.
3. Provide 3-5 key bullet point takeaways IN THE SAME LANGUAGE.

IMPORTANT: Respond ONLY with valid JSON in the following format (no markdown, no code blocks, just pure JSON):
{{
    "summary": "<insert summary here as a single string>",
    "takeaways": ["<point 1>", "<point 2>", "<point 3>", ...]
}}

TEXT TO PROCESS:
{truncated_text}"""
    
    # Call Ollama API
    try:
        # Use longer output for papers (more detailed analysis required)
        max_tokens = 40000 if resource_type == "paper" else 1000
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": max_tokens,
                }
            },
            timeout=180 if resource_type == "paper" else 120  # Longer timeout for papers
        )
        response.raise_for_status()
        raw_text = response.json()["response"]
        
        # For papers, return raw text
        if resource_type == "paper":
            return raw_text.strip()
        
        # For blog/youtube, parse JSON
        try:
            # Try to extract JSON from the response (might have extra text)
            json_start = raw_text.find('{')
            json_end = raw_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = raw_text[json_start:json_end]
                parsed = json.loads(json_str)
                
                # Validate structure
                summary = parsed.get("summary", "").strip()
                takeaways = parsed.get("takeaways", [])
                
                # Ensure takeaways is a list
                if isinstance(takeaways, str):
                    # If it's a string, try to split by newlines or bullets
                    takeaways = [t.strip() for t in re.split(r'[-•*]\s*|\n', takeaways) if t.strip()]
                elif not isinstance(takeaways, list):
                    takeaways = []
                
                return {
                    "summary": summary,
                    "takeaways": takeaways
                }
            else:
                raise ValueError("No JSON object found in response")
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # Fallback: try to parse as text format
            print(f"JSON parsing failed: {e}. Attempting fallback text parsing.")
            summary_part = raw_text.split("TAKEAWAYS:")[0].replace("SUMMARY:", "").strip()
            takeaways_part = raw_text.split("TAKEAWAYS:")[1].strip() if "TAKEAWAYS:" in raw_text else ""
            
            # Convert takeaways string to list
            takeaways_list = []
            if takeaways_part:
                # Split by newlines or bullet points
                takeaways_list = [t.strip() for t in re.split(r'[-•*]\s*|\n', takeaways_part) if t.strip()]
            
            return {
                "summary": summary_part,
                "takeaways": takeaways_list if takeaways_list else [takeaways_part] if takeaways_part else []
            }
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to connect to Ollama: {str(e)}. Make sure Ollama is running and the model is installed.")

def calculate_reminder(interval: str) -> Optional[str]:
    """Calculates ISO 8601 date string for Notion."""
    now = datetime.now()
    if interval == "tomorrow":
        rem_date = now + timedelta(days=1)
    elif interval == "3days":
        rem_date = now + timedelta(days=3)
    elif interval == "1week":
        rem_date = now + timedelta(weeks=1)
    else:
        return None # No reminder
    
    # Return format compliant with Notion ISO 8601
    return rem_date.astimezone().isoformat()

def push_to_notion(data: dict):
    """Creates a page in the Notion Database."""
    
    # Use extracted title or fallback to "New Resource"
    page_title = data.get('title', 'New Resource')
    # Limit title length to 2000 characters (Notion limit)
    if len(page_title) > 2000:
        page_title = page_title[:1997] + "..."
    
    properties = {
        "Name": {"title": [{"text": {"content": page_title}}]},
        "URL": {"url": data['url']},
        "Type": {"select": {"name": data['type']}},
        "Status": {"select": {"name": "To Review"}},
    }

    # Add Reminder if exists
    if data['reminder']:
        properties["Reminder"] = {"date": {"start": data['reminder']}}

    # Build children blocks for Notion page
    children = []
    
    # Check if this is a paper (raw content) or blog/youtube (structured)
    if 'content' in data:
        # Paper: Store raw LLM response content
        content_text = data.get('content', '')
        if content_text:
            # Split content into paragraphs (by double newlines)
            # Limit to 2000 chars per block (Notion limit)
            max_chars = 2000
            
            # Split by paragraphs first
            paragraphs = re.split(r'\n\s*\n', content_text)
            
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                
                # If paragraph is too long, split it further
                if len(para) <= max_chars:
                    children.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {"rich_text": [{"text": {"content": para}}]}
                    })
                else:
                    # Split long paragraph into chunks
                    for i in range(0, len(para), max_chars):
                        chunk = para[i:i + max_chars]
                        children.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {"rich_text": [{"text": {"content": chunk}}]}
                        })
    else:
        # Blog/YouTube: Use structured format with Summary and Takeaways sections
        # Block 1: Summary Heading
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "Summary"}}]}
        })
        
        # Block 2: Summary Text (split into paragraphs if too long)
        summary_text = data.get('summary', '')
        if summary_text:
            # Limit to 2000 chars per block, split into multiple paragraphs if needed
            max_chars = 2000
            if len(summary_text) <= max_chars:
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": summary_text}}]}
                })
            else:
                # Split into multiple paragraphs
                for i in range(0, len(summary_text), max_chars):
                    chunk = summary_text[i:i + max_chars]
                    children.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {"rich_text": [{"text": {"content": chunk}}]}
                    })
        
        # Block 3: Takeaways Heading
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "Key Takeaways"}}]}
        })
        
        # Block 4: Takeaways as bulleted list
        takeaways = data.get('takeaways', [])
        if isinstance(takeaways, list) and takeaways:
            for takeaway in takeaways:
                if takeaway:  # Skip empty takeaways
                    takeaway_text = str(takeaway).strip()
                    if takeaway_text:
                        # Limit each bullet point to 2000 chars
                        takeaway_text = takeaway_text[:2000]
                        children.append({
                            "object": "block",
                            "type": "bulleted_list_item",
                            "bulleted_list_item": {
                                "rich_text": [{"text": {"content": takeaway_text}}]
                            }
                        })
        elif isinstance(takeaways, str) and takeaways:
            # Fallback: if takeaways is a string, split it
            for takeaway in takeaways.split('\n'):
                takeaway_text = takeaway.strip()
                if takeaway_text:
                    takeaway_text = takeaway_text[:2000]
                    children.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{"text": {"content": takeaway_text}}]
                        }
                    })
    
    # Create the page
    new_page = notion.pages.create(
        parent={"database_id": os.getenv("NOTION_DATABASE_ID")},
        properties=properties,
        children=children
    )
    
    # Update title with page ID or inferred title if we had one (Using page ID for uniqueness in this simple version)
    # Ideally, we would ask Gemini to extract a Title too.
    return new_page

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/submit")
async def submit_resource(request: Request, url: str = Form(...), resource_type: str = Form(...), reminder: str = Form(...)):
    try:
        # 1. Extract title based on resource type
        resource_title = extract_resource_title(url, resource_type)
        
        # 2. Fetch content based on resource type
        raw_content = fetch_content(url, resource_type)
        
        # Determine content type for Notion (capitalize first letter)
        type_mapping = {
            "youtube": "Video",
            "blog": "Article",
            "paper": "Paper"
        }
        content_type = type_mapping.get(resource_type, "Article")
        
        # 3. Summarize using local LLM (use specialized prompt for papers)
        ai_result = generate_summary(raw_content, resource_type)
        
        # 4. Calculate Reminder
        reminder_date = calculate_reminder(reminder)
        
        # 5. Push to Notion
        # For papers: ai_result is a string (raw content)
        # For blog/youtube: ai_result is a dict with 'summary' and 'takeaways'
        if resource_type == "paper":
            payload = {
                "url": url,
                "type": content_type,
                "title": resource_title,
                "content": ai_result,  # Raw string for papers
                "reminder": reminder_date
            }
        else:
            payload = {
                "url": url,
                "type": content_type,
                "title": resource_title,
                "summary": ai_result['summary'],
                "takeaways": ai_result['takeaways'],
                "reminder": reminder_date
            }
        
        push_to_notion(payload)
        
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "message": "Success! Resource saved to Notion."
        })
        
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "error": f"Error: {str(e)}"
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
