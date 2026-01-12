# Render Deployment Guide

This guide will help you deploy your Notion Assistant to Render.

## Prerequisites

1. **GitHub Account** - Render deploys from GitHub
2. **Render Account** - Sign up at https://render.com (free)
3. **Your code pushed to GitHub** - Make sure your repository is on GitHub

## Step-by-Step Deployment

### Step 1: Prepare Your Repository

Make sure your code is pushed to GitHub with these files:
- `main.py`
- `requirements.txt`
- `Dockerfile`
- `start.sh`
- `templates/index.html`
- `prompts/paper_prompt.txt`
- `render.yaml` (optional, but helpful)

### Step 2: Create Render Account

1. Go to https://render.com
2. Sign up with your GitHub account (recommended for easy deployment)

### Step 3: Create New Web Service

1. **Click "New +"** in your Render dashboard
2. Select **"Web Service"**
3. **Connect your GitHub repository**:
   - If not connected, authorize Render to access your GitHub
   - Select your `notion_assistant` repository
   - Click "Connect"

### Step 4: Configure Service

Fill in the following settings:

**Basic Settings:**
- **Name**: `notion-assistant` (or any name you prefer)
- **Region**: Choose closest to you (e.g., `Oregon (US West)`)
- **Branch**: `main` (or your default branch)
- **Root Directory**: Leave empty (or `.` if needed)

**Build & Deploy:**
- **Runtime**: `Docker`
- **Dockerfile Path**: `./Dockerfile` (should auto-detect)
- **Docker Context**: `.` (current directory)

**Plan:**
- **Free**: Spins down after 15 minutes of inactivity (good for testing)
- **Starter ($7/month)**: Always on, better for production

**Environment Variables:**
Click "Add Environment Variable" and add:

```
NOTION_TOKEN = your_notion_integration_token
NOTION_DATABASE_ID = your_notion_database_id
OLLAMA_BASE_URL = http://localhost:11434
OLLAMA_MODEL = minimax-m2:cloud
```

**Advanced Settings (Optional):**
- **Health Check Path**: `/` (Render will check if your app is running)
- **Auto-Deploy**: `Yes` (deploys automatically on git push)

### Step 5: Deploy

1. Click **"Create Web Service"**
2. Render will:
   - Build your Docker image
   - Install dependencies
   - Start your service
3. Wait for deployment to complete (usually 5-10 minutes)

### Step 6: Access Your App

Once deployed, your app will be available at:
```
https://notion-assistant.onrender.com
```
(Your URL will be: `https://your-service-name.onrender.com`)

## Important Notes

### Free Tier Limitations

- **Spins down after 15 minutes of inactivity**
- First request after spin-down takes ~30-60 seconds (cold start)
- Limited to 750 hours/month total runtime
- 512MB RAM

### Paid Tier ($7/month - Starter)

- **Always on** (no spin-down)
- 512MB RAM
- Better for production use

### Ollama on Render

Since you're using `minimax-m2:cloud`, Ollama doesn't need to download large models locally. The cloud model will work fine on Render's infrastructure.

### Environment Variables Security

- Never commit your `NOTION_TOKEN` or `NOTION_DATABASE_ID` to GitHub
- Always set them in Render's dashboard
- Render encrypts environment variables at rest

## Troubleshooting

### Build Fails

1. Check build logs in Render dashboard
2. Common issues:
   - Missing files in repository
   - Dockerfile syntax errors
   - Network issues during build

### App Crashes

1. Check service logs in Render dashboard
2. Common issues:
   - Missing environment variables
   - Ollama not starting properly
   - Port conflicts

### Slow First Request (Free Tier)

- This is normal on free tier (cold start)
- Consider upgrading to Starter plan for always-on

### Ollama Connection Issues

- Make sure `OLLAMA_BASE_URL=http://localhost:11434` is set
- Check that `start.sh` is waiting for Ollama to be ready
- Review logs to see if Ollama started successfully

## Updating Your App

Render automatically deploys when you push to your connected branch:

```bash
git add .
git commit -m "Update app"
git push origin main
```

Render will detect the push and automatically rebuild and redeploy.

## Monitoring

- **Logs**: View real-time logs in Render dashboard
- **Metrics**: Monitor CPU, memory, and request metrics
- **Alerts**: Set up alerts for service downtime (paid plans)

## Cost Summary

- **Free Tier**: $0/month (with limitations)
- **Starter Plan**: $7/month (always-on, recommended for production)

## Next Steps

1. Test your deployed app
2. Share the URL with users
3. Monitor usage and logs
4. Consider upgrading to Starter plan if you need always-on service

## Support

- Render Docs: https://render.com/docs
- Render Community: https://community.render.com
- Render Status: https://status.render.com
