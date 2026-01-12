# Render Deployment Checklist

## Pre-Deployment

- [ ] Code is pushed to GitHub
- [ ] All required files are in the repository:
  - [ ] `main.py`
  - [ ] `requirements.txt`
  - [ ] `Dockerfile`
  - [ ] `start.sh`
  - [ ] `templates/index.html`
  - [ ] `prompts/paper_prompt.txt`
- [ ] You have your Notion credentials ready:
  - [ ] NOTION_TOKEN
  - [ ] NOTION_DATABASE_ID

## Deployment Steps

1. [ ] Sign up at https://render.com
2. [ ] Click "New +" → "Web Service"
3. [ ] Connect your GitHub repository
4. [ ] Configure service:
   - [ ] Name: `notion-assistant`
   - [ ] Runtime: `Docker`
   - [ ] Dockerfile Path: `./Dockerfile`
   - [ ] Plan: Choose Free (testing) or Starter $7/month (production)
5. [ ] Add environment variables:
   - [ ] `NOTION_TOKEN` = your_notion_token
   - [ ] `NOTION_DATABASE_ID` = your_database_id
   - [ ] `OLLAMA_BASE_URL` = `http://localhost:11434`
   - [ ] `OLLAMA_MODEL` = `minimax-m2:cloud`
6. [ ] Click "Create Web Service"
7. [ ] Wait for deployment (5-10 minutes)
8. [ ] Test your app at the provided URL

## Post-Deployment

- [ ] Test the app is accessible
- [ ] Test submitting a resource (YouTube, blog, or paper)
- [ ] Check Render logs for any errors
- [ ] Verify Notion integration is working
- [ ] Share the URL with users

## Troubleshooting

If deployment fails:
- [ ] Check build logs in Render dashboard
- [ ] Verify all files are in GitHub
- [ ] Check environment variables are set correctly
- [ ] Review `RENDER_DEPLOYMENT.md` for detailed troubleshooting

## Cost Reminder

- **Free Tier**: $0/month (spins down after 15 min inactivity)
- **Starter Plan**: $7/month (always-on, recommended for production)
