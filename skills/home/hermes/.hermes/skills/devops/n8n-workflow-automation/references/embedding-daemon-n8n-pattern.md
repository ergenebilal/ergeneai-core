# Embedding Daemon as n8n HTTP Backend

A reusable architecture pattern: run a local FastAPI/HTTP server that keeps ML models warm in memory, and have n8n call it via HTTP Request nodes — eliminating file-sharing and model-reload overhead.

## Architecture

```
n8n (Docker container)
  │
  │  HTTP Request nodes (timeout: 5s)
  │  URL: http://host.docker.internal:8767/<endpoint>
  │
  ▼
Embedding Daemon (host, port 8767, Python HTTP server)
  │
  ├── /health (GET) → {"status":"ok"}
  ├── /embed (POST) → text → vector
  ├── /memory/save (POST) → content+category → PG INSERT
  └── /memory/search (POST) → sorgu → PG vector search
  │
  ├── Model cache: sentence-transformers in RAM (384d, Turkish)
  ├── DB: PostgreSQL + pgvector extension
  └── Watchdog: cron every 5min (restart if down)
```

## Key Design Decisions

1. **Why HTTP instead of file-based?** n8n Docker containers have filesystem isolation from the host. Writing to `/tmp/` on the host is invisible inside the container. HTTP bridges the isolation cleanly.

2. **Why `host.docker.internal`?** Docker Desktop and Coolify networks resolve this to the host machine. Falls back to `172.17.0.1` on bare Linux Docker.

3. **Why 5-second timeout?** Non-blocking — if the embedding daemon is down, the main n8n flow (e.g. Instagram DM reply) continues unaffected.

4. **Why model warm in RAM?** sentence-transformers takes ~2s to load on each Python invocation. A persistent HTTP server loads it once and keeps it hot (~20ms per request).

## Daemon Implementation Template

```python
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class EmbeddingAPI(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def do_POST(self):
        body = self._read_body()
        # route to handler based on self.path
        # /memory/save, /memory/search, /embed
        result = self._handle(path, body)
        self._send_json(result)

server = HTTPServer(("0.0.0.0", 8767), EmbeddingAPI)
server.serve_forever()
```

## n8n HTTP Request Node Configuration

| Field | Value |
|---|---|
| Method | POST |
| URL | `http://host.docker.internal:8767/memory/save` |
| Authentication | None |
| Send Body | Yes |
| Body Parameters | `content`, `category` (from `$json._hermes.payload`) |
| Options → Timeout | 5000 ms |

## Watchdog Cron

```bash
# Every 5 minutes, check /health, restart if dead
curl -sf http://localhost:8767/health || (
  pkill -f embedding_daemon.py
  python3.11 /path/to/embedding_daemon.py &
)
```

## Pitfalls

- **`host.docker.internal` requires explicit `--add-host` flag on Linux Docker.** Coolify adds it automatically. For manual Docker: `docker run --add-host host.docker.internal:host-gateway n8n-image`.
- **Python version mismatch.** The daemon needs psycopg2 + sentence-transformers + chromadb all in the same Python version. Use `python3.11` explicitly.
- **Port conflicts.** Pick an unused port. Check with `ss -tlnp | grep <port>`.
- **stdout buffering.** If using `print()` for logging, flush with `flush=True` or use `sys.stderr.write()`.
- **Model download on first run.** sentence-transformers downloads ~500MB on first invocation. Pre-warm by running the script once before putting it behind a watchdog.
