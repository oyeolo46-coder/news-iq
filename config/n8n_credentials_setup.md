# N8n Credentials Setup Guide

## Required Credentials (create these in n8n UI)

### 1. PostgreSQL
- Type: PostgreSQL
- Host: your-db-host.railway.internal (or localhost)
- Port: 5432
- Database: news_iq
- User: postgres
- Password: your-password
- SSL: true (for Railway)
- Credential ID: `postgres-cred`

### 2. NewsAPI (HTTP Basic Auth or Header Auth)
- Type: Header Auth
- Name: `x-api-key` (or query param)
- Value: your NewsAPI key
- Credential ID: `newsapi-cred`

### 3. Claude API (Header Auth)
- Type: Header Auth
- Name: `x-api-key`
- Value: your Anthropic key
- Credential ID: `claude-cred`

### 4. Google Cloud (Service Account)
- Type: Google OAuth2 API
- OR upload service account JSON
- Credential ID: `google-cred`

### 5. Gmail (OAuth2)
- Type: Gmail OAuth2 API
- Follow n8n's OAuth flow
- Credential ID: `gmail-cred`

### 6. Twilio
- Type: Twilio API
- Account SID: your_sid
- Auth Token: your_token
- Credential ID: `twilio-cred`

## Environment Variables in n8n

Set these in n8n Settings > Environment Variables:

```
NEWSAPI_KEY=xxx
SERPAPI_KEY=xxx
CLAUDE_API_KEY=xxx
GOOGLE_TTS_KEY=xxx
GOOGLE_FOLDER_ID=xxx
DATABASE_URL=postgresql://...
USER_EMAIL=your@email.com
USER_PHONE=+1234567890
TWILIO_WHATSAPP_FROM=whatsapp:+1234567890
VIDEO_SERVICE_URL=http://localhost:8001
EMBEDDING_SERVICE_URL=http://localhost:8001
```