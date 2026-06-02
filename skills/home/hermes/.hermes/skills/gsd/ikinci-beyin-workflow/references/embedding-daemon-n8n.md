# Embedding Daemon + n8n Entegrasyonu — Referans

## Mimarî

```
n8n Container (Docker)
  └─ HTTP Request Node ──→ http://host.docker.internal:8767/memory/save
                          ──→ http://host.docker.internal:8767/memory/search

Host (Ubuntu 22.04)
  └─ Embedding Daemon (8767)
       ├─ sentence-transformers RAM'de sıcak (384d, Türkçe)
       ├─ PostgreSQL (localhost:5432, ergeneai.hermes_memory)
       └─ Watchdog cron (her 5dk)
```

## Neden HTTP API, neden temp file DEĞİL?

**n8n container'ı host'un /tmp'sini göremez.** Docker volume izolasyonu var. Temp dosya yazma yaklaşımı ÇALIŞMAZ.

Çözüm: Embedding Daemon'u host'ta HTTP server olarak çalıştır, n8n HTTP Request node ile çağırsın.

## Embedding Daemon

**Path:** `/home/hermes/hermes_data/embedding_daemon.py`
**Port:** 8767 (MCP 8765, Nanobot 8766'ya komşu)
**Başlatma:** `python3.11 /home/hermes/hermes_data/embedding_daemon.py` (background)
**Watchdog:** Cron job ID `490a1e1a2e1d`, her 5 dk

### Endpoint'ler

| Endpoint | Method | Body | Response |
|---|---|---|---|
| `/health` | GET | - | `{"status":"ok","model_loaded":true}` |
| `/embed` | POST | `{"text":"..."}` | `{"vector":[...],"boyut":384}` |
| `/memory/save` | POST | `{"content":"...","category":"..."}` | `{"sonuc":"✅ Hafizaya kaydedildi"}` |
| `/memory/search` | POST | `{"sorgu":"...","limit":5,"esik":0.3}` | `{"sonuc":[...],"adet":N}` |

### Test
```bash
curl -s -X POST http://localhost:8767/memory/save \
  -H "Content-Type: application/json" \
  -d '{"content":"test notu","category":"test"}'
```

## n8n AI Agent Workflow (ID: 3ngLwcqxlAKWiuug)

### Değişiklik: 12 → 17 node

Eklenen node'lar:
1. **04 Intent Check** (Code) — kullanıcı mesajından intent tespiti
2. **05 Switch (Intent Router)** — save_memory/search_memory/casual_chat
3. **06 HTTP Save Memory** — POST /memory/save'a istek
4. **07 HTTP Search Memory** — POST /memory/search'a istek
5. **08 Passthrough** — switch'ten geleni Score'a iletir

### Intent Check Kodu
```javascript
const text = ($json.text || $json.body || $json.prompt || "").toLowerCase();
let intent = "casual_chat";
let payload = {};

if (text.includes("kaydet") || text.includes("not et") || text.includes("hatirla")) {
  intent = "save_memory";
  payload = { content: $json.text, category: "genel" };
} else if (text.includes("ara") || text.includes("bul") || text.includes("ne yaziyordu")) {
  intent = "search_memory";
  payload = { sorgu: $json.text, limit: 3 };
}
return [{ json: { ...$json, _hermes: { intent, payload } } }];
```

### n8n Workflow Modifikasyonu (API'siz)

n8n API key çalışmadığında direkt SQLite DB'ye müdahale:

```bash
# Export
sudo docker exec n8n-xxx sh -c "n8n export:workflow --id=3ngLwcqxlAKWiuug --output=/tmp/wf.json"

# Copy to host, edit, copy back
sudo docker cp n8n-xxx:/tmp/wf.json /tmp/wf_modified.json
# ... edit with Python ...
sudo docker cp /tmp/wf_modified.json n8n-xxx:/tmp/wf_modified.json

# Import (deactivates workflow)
sudo docker exec n8n-xxx sh -c "n8n import:workflow --input=/tmp/wf_modified.json --id=3ngLwcqxlAKWiuug"

# Activate + restart
sudo docker exec n8n-xxx sh -c "n8n publish:workflow --id=3ngLwcqxlAKWiuug"
sudo docker restart n8n-xxx
```

**ÖNEMLİ:** n8n import sonrası container restart ŞART. Yoksa eski versiyon çalışmaya devam eder.

### Backup
Her değişiklikten sonra workflow JSON'u GitHub'a pushlanır:
`ergeneai-core/n8n_ai_agent_workflow.json`

## n8n_bridge.py (CLI Fallback)

**Path:** `/home/hermes/hermes_data/n8n_bridge.py`
**Kullanım:** `python3.11 /home/hermes/hermes_data/n8n_bridge.py --save "not" "kategori"`

Önce Embedding Daemon'a istek atar, daemon yoksa direkt PostgreSQL'e yazar (model yükler).
