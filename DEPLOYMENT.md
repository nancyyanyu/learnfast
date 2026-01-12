# Deployment Guide

## Option 1: Fly.io (Recommended - Free Tier Available)

### Prerequisites
1. Install Fly CLI: https://fly.io/docs/getting-started/installing-flyctl/
2. Sign up at https://fly.io

### Steps

1. **Login to Fly.io**
   ```bash
   fly auth login
   ```

2. **Initialize your app**
   ```bash
   fly launch
   ```
   - Choose a unique app name
   - Select a region close to you
   - Don't create a Postgres database (not needed)

3. **Set environment variables**
   ```bash
   fly secrets set NOTION_TOKEN=your_notion_token
   fly secrets set NOTION_DATABASE_ID=your_database_id
   fly secrets set OLLAMA_BASE_URL=http://localhost:11434
   fly secrets set OLLAMA_MODEL=minimax-m2:cloud
   ```

4. **Deploy**
   ```bash
   fly deploy
   ```

5. **Get your URL**
   ```bash
   fly info
   ```
   Your app will be available at: `https://your-app-name.fly.dev`

### Cost: FREE (with limits) or ~$5-10/month for better performance

---

## Option 2: Render (Simple, but Free Tier Sleeps)

### Steps

1. **Create account** at https://render.com

2. **Create new Web Service**
   - Connect your GitHub repository
   - Build Command: `pip install -r requirements.txt && curl -fsSL https://ollama.com/install.sh | sh`
   - Start Command: `ollama serve & sleep 5 && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Environment: Python 3
   - Add environment variables:
     - `NOTION_TOKEN`
     - `NOTION_DATABASE_ID`
     - `OLLAMA_BASE_URL=http://localhost:11434`
     - `OLLAMA_MODEL=minimax-m2:cloud`

3. **Deploy**

### Cost: FREE (spins down) or $7/month for always-on

---

## Option 3: Railway ($5/month)

### Steps

1. **Sign up** at https://railway.app
2. **New Project** → Deploy from GitHub
3. **Add environment variables** in Railway dashboard
4. **Deploy**

### Cost: $5/month

---

## Option 4: VPS (Most Control, Lowest Cost)

### Hetzner (€4/month ≈ $4.50/month)

1. **Create account** at https://hetzner.com
2. **Create a VPS** (CPX11 - €4.15/month)
3. **SSH into server** and run:
   ```bash
   # Install Python, pip
   sudo apt update
   sudo apt install python3 python3-pip python3-venv -y
   
   # Install Ollama
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Clone your repo
   git clone <your-repo-url>
   cd notion_assistant
   
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Set environment variables
   export NOTION_TOKEN=your_token
   export NOTION_DATABASE_ID=your_id
   export OLLAMA_BASE_URL=http://localhost:11434
   export OLLAMA_MODEL=minimax-m2:cloud
   
   # Start Ollama
   ollama serve &
   
   # Start app with systemd (create service)
   sudo nano /etc/systemd/system/notion-assistant.service
   ```
   
4. **Create systemd service** (`/etc/systemd/system/notion-assistant.service`):
   ```ini
   [Unit]
   Description=Notion Assistant
   After=network.target

   [Service]
   User=your-username
   WorkingDirectory=/home/your-username/notion_assistant
   Environment="PATH=/home/your-username/notion_assistant/venv/bin"
   Environment="NOTION_TOKEN=your_token"
   Environment="NOTION_DATABASE_ID=your_id"
   Environment="OLLAMA_BASE_URL=http://localhost:11434"
   Environment="OLLAMA_MODEL=minimax-m2:cloud"
   ExecStart=/home/your-username/notion_assistant/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

5. **Start service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable notion-assistant
   sudo systemctl start notion-assistant
   ```

6. **Set up Nginx reverse proxy** (for HTTPS)
   ```bash
   sudo apt install nginx certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

### Cost: €4-6/month (~$4.50-6.50)

---

## Option 5: Oracle Cloud (Always Free)

Similar to Hetzner setup, but with Oracle's always-free tier:
- 2 VMs with 1GB RAM each (or 1 VM with 2GB)
- Free forever (with usage limits)

---

## Recommendation

**For cost-sensitive deployment:**
1. **Start with Fly.io** - Free tier, easy deployment
2. **If you need more resources:** Switch to Hetzner VPS (€4/month)
3. **If you want simplicity:** Railway ($5/month) or Render ($7/month always-on)

**Important Notes:**
- Since you're using `minimax-m2:cloud`, Ollama doesn't need to download large models
- Make sure to set all environment variables securely
- Consider using a reverse proxy (Nginx) for HTTPS on VPS options
- Monitor your usage to avoid unexpected costs
