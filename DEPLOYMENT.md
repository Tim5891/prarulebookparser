# Deployment Guide

This application can be easily deployed to Railway.

## Prerequisites

- GitHub account with the repository pushed
- Railway account (https://railway.app)

## Deployment Steps

### 1. Create a Railway Account

1. Go to https://railway.app
2. Sign up with GitHub
3. Authorize Railway to access your repositories

### 2. Create a New Project

1. Click "Create New Project" or "New Project"
2. Select "Deploy from GitHub"
3. Select your repository (`prarulebookparser`)
4. Confirm the GitHub connection

### 3. Configure the Deployment

Railway will automatically detect it's a Python project and create a service. The app should deploy automatically with:

- **Procfile:** `gunicorn app:app`
- **Python Runtime:** 3.11.8
- **Requirements:** From `requirements.txt`

### 4. Monitor Deployment

1. Watch the build logs in Railway's dashboard
2. Once deployed, you'll get a public URL (e.g., `https://your-app.railway.app`)
3. Click the URL to open your application

## Environment Variables

The app doesn't require any environment variables, but Railway will automatically set:

- `PORT` - The port your app should listen on (defaults to 5000)

## Verification

Once deployed:

1. Open the public URL
2. Test the structure scraper with date: `18-06-2019` and layer: `chapter`
3. Use a returned URL to test the content scraper

## Cost

Railway offers:
- Free tier: Up to 500 hours/month
- Paid tier: Pay-as-you-go ($5/month minimum)

This application will fit comfortably in the free tier for testing.

## Troubleshooting

### App won't start
- Check build logs in Railway dashboard
- Ensure all dependencies are in `requirements.txt`
- Verify `Procfile` is correct

### Port binding error
- Railway automatically sets the `PORT` environment variable
- The app correctly reads it: `port = int(os.environ.get('PORT', 5000))`

### Timeout errors when scraping
- Scraping can take time if requesting multiple rules
- Railway allows up to 120 seconds per request by default
- Consider pagination or limits for large scrapes

## Local Testing Before Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Test locally
python app.py

# Visit http://localhost:5000
```

## Domain Setup (Optional)

To use a custom domain:

1. In Railway dashboard, go to your project settings
2. Add a custom domain
3. Update your DNS records as instructed

## Monitoring

Railway provides:
- Real-time logs
- Deployment history
- Memory and CPU usage metrics
- Error tracking

Check these regularly to ensure smooth operation.
