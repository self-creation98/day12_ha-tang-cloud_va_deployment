# Day 12 Lab - Mission Answers

> **Student Name:** Phạm Thanh Tùng 
> **Student ID:** 2A202600268
> **Date:** 17/04/2026

---

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found

Sau khi đọc file `01-localhost-vs-production/develop/app.py`, tìm được **7 anti-patterns**:

| # | Anti-pattern | Dòng code | Tại sao nguy hiểm? |
|---|-------------|-----------|---------------------|
| 1 | **Hardcode API key** | `OPENAI_API_KEY = "sk-hardcoded-fake-key..."` | Push lên GitHub → key bị lộ, bị lạm dụng, mất tiền |
| 2 | **Hardcode database URL với password** | `DATABASE_URL = "postgresql://admin:password123@..."` | Lộ credentials database, bất kỳ ai clone repo đều thấy |
| 3 | **Print thay vì proper logging** | `print(f"[DEBUG] Got question: {question}")` | Không structured, khó parse trong log aggregator (Datadog, Loki) |
| 4 | **Log ra secrets** | `print(f"[DEBUG] Using key: {OPENAI_API_KEY}")` | Lộ API key trong log files, vi phạm security |
| 5 | **Không có health check endpoint** | Không có `/health` hay `/ready` | Platform không biết agent crash → không thể tự restart |
| 6 | **Port cố định, bind localhost** | `host="localhost", port=8000` | Chỉ chạy trên local, không nhận connection từ bên ngoài container |
| 7 | **Debug reload trong production** | `reload=True` | Hot-reload tốn resource, không nên bật trong production |

### Exercise 1.2: Chạy basic version

```bash
cd 01-localhost-vs-production/develop
pip install -r requirements.txt
python app.py
```

Test:
```bash
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
```

**Kết quả:** Agent chạy được, trả về response. Tuy nhiên **KHÔNG production-ready** vì tất cả anti-patterns ở Exercise 1.1.

### Exercise 1.3: Comparison table

| Feature | Develop (Basic) | Production (Advanced) | Tại sao quan trọng? |
|---------|----------------|----------------------|---------------------|
| **Config** | Hardcode trong code | `os.getenv()` + `Settings` dataclass | Thay đổi config không cần sửa code, bảo mật secrets |
| **Health check** | ❌ Không có | ✅ `GET /health` + `GET /ready` | Platform biết khi nào restart, LB biết khi nào route traffic |
| **Logging** | `print()`, log secrets | JSON structured, KHÔNG log secrets | Dễ parse, monitor, alert; không lộ thông tin nhạy cảm |
| **Shutdown** | Đột ngột, mất request | Graceful (SIGTERM handler + lifespan) | Không mất request đang xử lý, đóng connections sạch sẽ |
| **Host binding** | `localhost` | `0.0.0.0` | Nhận connection từ bên ngoài container/VM |
| **Port** | Hardcode `8000` | `os.getenv("PORT", 8000)` | Cloud platforms inject PORT tự động (Railway, Render) |
| **Debug mode** | Luôn bật | Chỉ khi `DEBUG=true` | Không lãng phí resource, không lộ debug info trong prod |
| **CORS** | ❌ Không có | ✅ Configurable origins | Cho phép frontend gọi API cross-origin, bảo vệ API |
| **Error handling** | Crash toàn app | HTTPException + proper status codes | Client nhận error message rõ ràng, app không crash |
| **Metrics** | ❌ Không có | ✅ `/metrics` endpoint | Monitoring uptime, request count, environment info |

---

## Part 2: Docker

### Exercise 2.1: Dockerfile questions

1. **Base image là gì?**
   - `python:3.11` (full Python distribution, ~1 GB)
   - Bản production dùng `python:3.11-slim` (~150 MB) — nhỏ hơn nhiều vì loại bỏ build tools không cần thiết

2. **Working directory là gì?**
   - `/app` — đặt bằng lệnh `WORKDIR /app`
   - Tất cả lệnh tiếp theo (COPY, RUN, CMD) sẽ chạy trong thư mục này

3. **Tại sao COPY requirements.txt trước?**
   - **Docker layer cache**: Docker cache mỗi layer (mỗi lệnh là 1 layer)
   - Nếu `requirements.txt` không đổi → Docker reuse cached layer → skip `pip install` → build nhanh hơn
   - Nếu COPY code trước → mỗi lần sửa code, Docker phải cài lại dependencies → chậm

4. **CMD vs ENTRYPOINT khác nhau thế nào?**
   - `CMD` = command mặc định, có thể bị override khi `docker run ... <command>`
   - `ENTRYPOINT` = command cố định, không bị override (arguments được append)
   - `CMD ["python", "app.py"]` → có thể override: `docker run myimage bash`
   - `ENTRYPOINT ["python", "app.py"]` → luôn chạy python, không thể thay

### Exercise 2.3: Image size comparison

| Image | Base | Size |
|-------|------|------|
| **Develop** (`agent-develop`) | `python:3.11` (full) | 1.66 GB |
| **Production** (`agent-production`) | `python:3.11-slim` (multi-stage) | 236 MB |
| **Difference** | | ~60-70% nhỏ hơn |

**Tại sao production nhỏ hơn:**
- **Multi-stage build**: Stage 1 (builder) cài gcc, build tools → Stage 2 (runtime) chỉ copy packages đã compile
- **Slim base image**: Không có build tools, man pages, docs
- **`--no-cache-dir`**: Không lưu pip cache
- **Non-root user**: Security best practice (chạy với user `appuser`, không phải root)

### Exercise 2.4: Docker Compose architecture

```
docker-compose.yml — 4 services:

┌─────────────────────────────────────────────────────────┐
│                    Docker Network (internal)             │
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────┐  │
│  │  Nginx   │    │  Agent   │    │     Redis         │  │
│  │  :80/:443│───▶│  :8000   │───▶│  :6379            │  │
│  │  (LB)    │    │ (x2 rep) │    │  (cache/session)  │  │
│  └──────────┘    └──────────┘    └──────────────────┘  │
│       │                                                 │
│       │          ┌──────────────────┐                   │
│       │          │    Qdrant        │                   │
│       │          │    :6333         │                   │
│       │          │  (vector DB)     │                   │
│       │          └──────────────────┘                   │
│       │                                                 │
└───────┼─────────────────────────────────────────────────┘
        │
   External Access
   (port 80/443)
```

**Services:**
- **Nginx**: Reverse proxy + load balancer, public-facing (port 80/443)
- **Agent**: FastAPI AI agent (2 replicas), internal only
- **Redis**: Session cache + rate limiting, persistent volume
- **Qdrant**: Vector database cho RAG, persistent volume

**Communication**: Tất cả qua Docker internal network. Chỉ Nginx expose port ra ngoài. Agent không trực tiếp accessible từ internet.

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment

**Steps thực hiện:**
```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Login
railway login

# 3. Init project
railway init

# 4. Set environment variables
railway variables set PORT=8000
railway variables set AGENT_API_KEY=my-secret-key-2026
railway variables set ENVIRONMENT=production

# 5. Deploy
railway up

# 6. Get domain
railway domain
```

**Deployment URL:** _(xem DEPLOYMENT.md)_

**Test:**
```bash
# Health check
curl https://<domain>/health
# Expected: {"status": "ok", ...}

# Agent endpoint (with auth)
curl -X POST https://<domain>/ask \
  -H "X-API-Key: my-secret-key-2026" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is deployment?"}'
```

### Exercise 3.2: So sánh Railway vs Render

| Feature | `railway.toml` | `render.yaml` |
|---------|---------------|--------------|
| **Format** | TOML | YAML |
| **Build** | `builder = "DOCKERFILE"` hoặc `"NIXPACKS"` | `runtime: docker` hoặc `python` |
| **Start command** | `startCommand = "uvicorn ..."` | `startCommand: uvicorn ...` |
| **Health check** | `healthcheckPath = "/health"` | `healthCheckPath: /health` |
| **Env vars** | CLI: `railway variables set KEY=VALUE` | Trong file: `envVars:` hoặc Dashboard |
| **Auto deploy** | ✅ Tự động khi push | `autoDeploy: true` |
| **Secrets** | Dashboard/CLI | `sync: false` (set manual) hoặc `generateValue: true` |
| **Region** | Auto | Chọn được: `region: singapore` |
| **Additional services** | Railway add-ons | Inline: `type: redis` |

**Nhận xét:** Render có declarative config mạnh hơn (Infrastructure as Code), Railway đơn giản hơn cho quick deploy.

---

## Part 4: API Security

### Exercise 4.1-4.3: Test results

#### 4.1 — API Key Authentication

```bash
# ❌ Không có key → 401
$ curl http://localhost:8000/ask -X POST \
    -H "Content-Type: application/json" \
    -d '{"question": "Hello"}'

{"detail":"Missing API key. Include header: X-API-Key: <your-key>"}

# ❌ Sai key → 403
$ curl http://localhost:8000/ask -X POST \
    -H "X-API-Key: wrong-key" \
    -H "Content-Type: application/json" \
    -d '{"question": "Hello"}'

{"detail":"Invalid API key."}

# ✅ Đúng key → 200
$ curl http://localhost:8000/ask -X POST \
    -H "X-API-Key: demo-key-change-in-production" \
    -H "Content-Type: application/json" \
    -d '{"question": "Hello"}'

{"question": "Hello", "answer": "Agent đang hoạt động tốt!...", ...}
```

**API key check ở đâu?** Trong dependency `verify_api_key()`, sử dụng `APIKeyHeader(name="X-API-Key")` của FastAPI Security.

**Khi sai key?** Trả về HTTP 401 (Unauthorized) hoặc 403 (Forbidden).

**Rotate key?** Thay đổi giá trị `AGENT_API_KEY` trong environment variables → restart service. Không cần sửa code.

#### 4.2 — JWT Authentication

```bash
# Lấy token
$ curl -X POST http://localhost:8000/auth/token \
    -H "Content-Type: application/json" \
    -d '{"username": "student", "password": "demo123"}'

{"access_token": "eyJhbGciOiJIUzI1NiIs...", "token_type": "bearer", "expires_in_minutes": 60}

# Dùng token
$ curl -X POST http://localhost:8000/ask \
    -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
    -H "Content-Type: application/json" \
    -d '{"question": "Explain JWT"}'

{"question": "Explain JWT", "answer": "...", "usage": {"requests_remaining": 9, ...}}
```

**JWT Flow:**
1. Client gửi username/password → Server verify → Tạo JWT token (chứa sub, role, exp)
2. Client gửi token trong header `Authorization: Bearer <token>` cho mỗi request
3. Server verify signature (HS256) → extract user info → xử lý request
4. Token hết hạn sau 60 phút → client phải login lại

#### 4.3 — Rate Limiting

**Algorithm:** Sliding Window Counter
- Mỗi user có 1 deque chứa timestamps của requests
- Loại bỏ timestamps ngoài window (60 giây)
- Nếu `len(window) >= max_requests` → reject với 429

**Limit:**
- User (student): 10 requests/minute
- Admin (teacher): 100 requests/minute

**Bypass cho admin:** Dùng `rate_limiter_admin` instance riêng với limit cao hơn (100 req/min). Role được extract từ JWT token.

```bash
# Kết quả khi gọi liên tục 15 lần:
Request 1-10: 200 OK
Request 11+: 429 Too Many Requests
{"error": "Rate limit exceeded", "limit": 10, "retry_after_seconds": 45}
# Headers: X-RateLimit-Remaining: 0, Retry-After: 45
```

### Exercise 4.4: Cost guard implementation

**Approach:** Track spending per user per day, block khi vượt budget.

```python
# Logic trong cost_guard.py:
class CostGuard:
    def check_budget(self, user_id: str):
        record = self._get_record(user_id)  # Lấy usage record hôm nay

        # 1. Check global budget ($10/ngày)
        if self._global_cost >= self.global_daily_budget_usd:
            raise HTTPException(503, "Service temporarily unavailable")

        # 2. Check per-user budget ($1/ngày)
        if record.total_cost_usd >= self.daily_budget_usd:
            raise HTTPException(402, "Daily budget exceeded")

        # 3. Warning khi gần hết (80%)
        if record.total_cost_usd >= self.daily_budget_usd * 0.8:
            logger.warning(f"User {user_id} at 80% budget")

    def record_usage(self, user_id, input_tokens, output_tokens):
        # Tính cost: GPT-4o-mini pricing
        # Input:  $0.15/1M tokens = $0.00015/1K
        # Output: $0.60/1M tokens = $0.0006/1K
        cost = (input_tokens/1000) * 0.00015 + (output_tokens/1000) * 0.0006
        record.input_tokens += input_tokens
        record.output_tokens += output_tokens
        self._global_cost += cost
```

**Design decisions:**
- Auto-reset mỗi ngày (check `time.strftime("%Y-%m-%d")`)
- 2 tầng protection: per-user ($1) + global ($10)
- HTTP 402 (Payment Required) khi user vượt budget
- HTTP 503 khi global budget vượt (bảo vệ toàn hệ thống)
- Trong production: nên lưu trong Redis/DB thay vì in-memory

---

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes

#### 5.1 — Health Checks

**Liveness probe (`/health`):**
```python
@app.get("/health")
def health():
    uptime = round(time.time() - START_TIME, 1)
    checks = {}
    # Kiểm tra memory usage
    try:
        import psutil
        mem = psutil.virtual_memory()
        checks["memory"] = {
            "status": "ok" if mem.percent < 90 else "degraded",
            "used_percent": mem.percent,
        }
    except ImportError:
        checks["memory"] = {"status": "ok"}

    overall = "ok" if all(v["status"] == "ok" for v in checks.values()) else "degraded"
    return {"status": overall, "uptime_seconds": uptime, "checks": checks}
```

**Readiness probe (`/ready`):**
```python
@app.get("/ready")
def ready():
    if not _is_ready:
        raise HTTPException(503, "Agent not ready")
    return {"ready": True}
```

**Khác biệt:**
- **Liveness**: Container có chạy không? → Fail = platform restart
- **Readiness**: Sẵn sàng nhận traffic không? → Fail = LB ngừng route đến instance này

#### 5.2 — Graceful Shutdown

```python
# Signal handler
def handle_sigterm(signum, frame):
    logger.info(f"Received signal {signum}")
signal.signal(signal.SIGTERM, handle_sigterm)

# Lifespan shutdown
@asynccontextmanager
async def lifespan(app):
    global _is_ready
    _is_ready = True       # Startup
    yield
    _is_ready = False      # Shutdown: stop accepting new requests
    # Wait for in-flight requests (max 30s)
    while _in_flight_requests > 0 and elapsed < 30:
        time.sleep(1)
    logger.info("Shutdown complete")
```

**Flow:** SIGTERM → set `_is_ready = False` → `/ready` returns 503 → LB stops routing → wait for in-flight → exit

#### 5.3 — Stateless Design

**Anti-pattern (stateful):**
```python
# ❌ State trong memory — mất khi restart, không share giữa instances
conversation_history = {}

@app.post("/ask")
def ask(user_id, question):
    history = conversation_history.get(user_id, [])  # Instance-specific!
```

**Correct (stateless):**
```python
# ✅ State trong Redis — persist, shared giữa tất cả instances
@app.post("/chat")
def chat(body):
    session = load_session(body.session_id)  # Đọc từ Redis
    history = session.get("history", [])
    answer = ask(body.question)
    append_to_history(body.session_id, "assistant", answer)  # Lưu vào Redis
```

**Tại sao stateless quan trọng khi scale?**
- Khi có 3 instances, request có thể đến bất kỳ instance nào
- Instance 1 lưu session trong memory → Instance 2 không có session đó → Bug!
- Redis = external store → tất cả instances đều đọc/ghi cùng 1 nơi

#### 5.4 — Load Balancing

```bash
docker compose up --scale agent=3
```

**Quan sát:**
- 3 agent instances được start, mỗi instance có `INSTANCE_ID` riêng
- Nginx dùng round-robin phân tán requests
- Response header `X-Served-By` cho thấy instance nào xử lý
- Nếu 1 instance die → Nginx tự chuyển traffic sang instances khác (`proxy_next_upstream`)

#### 5.5 — Test Stateless

```bash
python test_stateless.py
```

**Kết quả mong đợi:**
```
Session ID: abc-123-def

Request 1: [instance-a1b2c3] Q: What is Docker?
Request 2: [instance-d4e5f6] Q: Why do we need containers?
Request 3: [instance-a1b2c3] Q: What is Kubernetes?
Request 4: [instance-g7h8i9] Q: How does load balancing work?
Request 5: [instance-d4e5f6] Q: What is Redis used for?

Instances used: {instance-a1b2c3, instance-d4e5f6, instance-g7h8i9}
✅ All requests served despite different instances!

--- Conversation History ---
Total messages: 10
✅ Session history preserved across all instances via Redis!
```

**Kết luận:** Mặc dù requests được xử lý bởi các instances khác nhau, conversation history vẫn liên tục vì state được lưu trong Redis, không phải memory.
