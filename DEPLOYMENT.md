# Deployment Information

## Public URL
🚀 **Railway:** https://2a202600268phamthanhtungday12-production.up.railway.app

## Platform
Railway (https://railway.com)

## Project
- **Name:** 2A202600268_PhamThanhTung_Day12
- **Environment:** production
- **Builder:** Dockerfile (multi-stage)

## Test Commands & Results

### 1. Health Check ✅
```bash
curl https://2a202600268phamthanhtungday12-production.up.railway.app/health
```
```json
{
  "status": "ok",
  "version": "1.0.0",
  "environment": "production",
  "uptime_seconds": 88.4,
  "total_requests": 2,
  "checks": { "llm": "mock" },
  "timestamp": "2026-04-17T10:39:08.286813+00:00"
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
# Response: 401 Unauthorized

# With API key → 200 OK
curl -X POST https://2a202600268phamthanhtungday12-production.up.railway.app/ask \
  -H "X-API-Key: day12-agent-key-2026" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
```
```json
{
  "question": "What is Docker?",
  "answer": "Container là cách đóng gói app để chạy ở mọi nơi. Build once, run anywhere!",
  "model": "gpt-4o-mini",
  "timestamp": "2026-04-17T10:39:24.372942+00:00"
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
| `PORT` | _(auto by Railway)_ | Server port |

## Deployment Config
- **Builder:** Dockerfile (multi-stage, python:3.11-slim)
- **Health check:** `/health` (30s timeout)
- **Restart policy:** ON_FAILURE (max 3 retries)
- **Workers:** 2 (uvicorn)
- **Non-root user:** `agent`

## Screenshots
_(Xem thư mục `screenshots/`)_
