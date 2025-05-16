# Deploying Receipt Scanner API to Railway

This guide will help you deploy your Receipt Scanner API to Railway.

## Prerequisites

1. A [Railway](https://railway.app/) account
2. [Railway CLI](https://docs.railway.app/develop/cli) installed (optional, but recommended)
3. Git installed on your machine

## Deployment Steps

### 1. Initialize Git Repository

If your project is not already a Git repository, initialize it:

```bash
git init
git add .
git commit -m "Initial commit for Railway deployment"
```

### 2. Deploy to Railway

#### Option 1: Using Railway Dashboard

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect your GitHub account if not already connected
5. Select your repository
6. Railway will automatically detect your configuration and deploy your app

#### Option 2: Using Railway CLI

1. Login to Railway:
   ```bash
   railway login
   ```

2. Initialize Railway project:
   ```bash
   railway init
   ```

3. Deploy your app:
   ```bash
   railway up
   ```

### 3. Configure Environment Variables

You might need to set the following environment variables in your Railway project:

- `PORT`: Railway will set this automatically
- `DATABASE_URL`: Railway will set this automatically if you add a PostgreSQL plugin

### 4. Add PostgreSQL Database (Optional)

1. In your Railway project dashboard, click "New"
2. Select "Database" and then "PostgreSQL"
3. Railway will provision a PostgreSQL database and set the `DATABASE_URL` environment variable

### 5. Monitor Your Deployment

1. In the Railway dashboard, you can monitor your deployment logs
2. Once deployed, Railway will provide you with a URL to access your API

## Testing Your Deployment

Once deployed, you can test your API using the provided `api_client.py` script:

```python
# Update the base_url to your Railway deployment URL
client = ReceiptScannerClient(base_url="https://your-railway-app-url.railway.app")
health = client.health_check()
print(f"API Status: {health['status']}")
```

## Troubleshooting

If you encounter any issues:

1. Check the deployment logs in the Railway dashboard
2. Ensure Tesseract OCR is properly installed (configured in railway.toml)
3. Verify that all required environment variables are set
4. Check that the database connection is working properly

## Additional Resources

- [Railway Documentation](https://docs.railway.app/)
- [Railway CLI Documentation](https://docs.railway.app/develop/cli)
- [Railway Environment Variables](https://docs.railway.app/develop/variables)
