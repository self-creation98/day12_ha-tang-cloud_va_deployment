# Deployment Information

## Public URLs
🚀 **Railway:** https://2a202600268phamthanhtungday12-production.up.railway.app  
🚀 **Render:** https://day12-agent-0m7k.onrender.com

## Platforms

### Railway
- **Project:** 2A202600268_PhamThanhTung_Day12
- **Environment:** production
- **Builder:** Dockerfile (multi-stage)
- **Plan:** Usage-based

### Render
- **Service:** day12-agent
- **Region:** Singapore
- **Builder:** Docker
- **Plan:** Free

## Test Commands & Results

### 1. Health Check ✅ (Both platforms)
```bash
# Railway
curl https://2a202600268phamthanhtungday12-production.up.railway.app/health

# Render
curl https://day12-agent-0m7k.onrender.com/health
```
```json
{
  "status": "ok",
  "version": "1.0.0",
  "environment": "production",
  "uptime_seconds": 88.4,
  "total_requests": 2,
  "checks": { "llm": "mock" },
  "timestamp": "2026-04-17T10:39:08+00:00"
}
```

### 2. Readiness Check ✅
```bash
curl https://2a202600268phamthanhtungday12-production.up.railway.app/ready
```
```json
{ "ready": true }
```

### 3. Authentication ✅
```bash
# Without API key → 401 Unauthorized
curl -X POST https://2a202600268phamthanhtungday12-production.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
# → 401 Unauthorized

# With API key → 200 OK
curl -X POST https://2a202600268phamthanhtungday12-production.up.railway.app/ask \
  -H "X-API-Key: day12-agent-key-2026" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
```
```json
{
  "question": "What is Docker?",
  "answer": "Container là cách đóng gói app để chạy ở mọi nơi...",
  "model": "gpt-4o-mini",
  "timestamp": "2026-04-17T10:39:24+00:00"
}
```

### 4. Rate Limiting ✅
- 20 requests/minute per user
- Returns HTTP 429 when exceeded

## Environment Variables Set

| Variable | Value | Description |
|----------|-------|-------------|
| `ENVIRONMENT` | `production` | Enables strict validation |
| `AGENT_API_KEY` | `day12-agent-key-2026` | API authentication key |
| `JWT_SECRET` | _(set securely)_ | JWT signing secret |
| `DAILY_BUDGET_USD` | `5.0` | Daily spending limit |
| `RATE_LIMIT_PER_MINUTE` | `20` | Max requests per minute |
| `LLM_MODEL` | `gpt-4o-mini` | Model identifier |
| `PORT` | _(auto-injected)_ | Server port |

## Deployment Config
- **Builder:** Dockerfile (multi-stage, python:3.11-slim)
- **Health check:** `/health` (30s timeout)
- **Restart policy:** ON_FAILURE (max 3 retries)
- **Workers:** 2 (uvicorn)
- **Non-root user:** `agent`

## Screenshots
- `screenshots/render_live.png` — Render dashboard with live service
