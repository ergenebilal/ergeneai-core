---
name: postgresql-memory
version: 2.1.0
author: Hermes Agent
description: PostgreSQL + pgvector ile kalıcı, ölçeklenebilir, semantik bellek sistemi — ChromaDB emekli edildi, PostgreSQL birincil ve tek bellek sistemi oldu. Kurulum, tablo tasarımı, embedding entegrasyonu, tools.py fonksiyonları.
---

# PostgreSQL Memory — İkinci Beyin

## When to Use

When ChromaDB's limits are reached (4 collections, growing data) and you need a **relational vector database** with:
- ACID compliance (no data loss on crash)
- Hybrid search (keyword + vector in one query)
- SQL queryable (JOIN, filter, aggregate alongside vector search)
- No container dependency (PostgreSQL runs natively)
- Backup/restore via pg_dump

ChromaDB **EMEKLİ EDİLDİ** (Haziran 2026). Artık PostgreSQL tek bellek sistemidir.

## Architecture

```
┌──────────────────────────────────────────┐
│           HERMES BELLEK SISTEMI           │
├──────────────────┬───────────────────────┤
│  Session (geçici)│  PostgreSQL (kalıcı)  │
│  RAM              │  5432                 │
│                   │  pgvector + embedding  │
│                   │  hermes_memory tablosu │
└──────────────────┴───────────────────────┘

> **ChromaDB emekli edildi (02 Haziran 2026).** Tüm bellek operasyonları PostgreSQL + Embedding Daemon (port 8767) üzerinden yapılır. `beyin_ara()` ve `beyin_kaydet()` artık PostgreSQL'e yönlendirilmiştir.
```

## Installation (Constrained Systems)

On Ubuntu 22.04 with **read-only /usr** and **near-full disk**:

### 1. Remount required partitions

```bash
# /etc and /usr are often mounted read-only on secure servers
sudo mount -o remount,rw /etc
sudo mount -o remount,rw /usr
# Revert after: sudo mount -o remount,ro /etc
```

### 2. Install PostgreSQL 14

```bash
sudo apt-get update
sudo apt-get install -y postgresql-14 postgresql-server-dev-14
```

### 3. Build & Install pgvector from Source

```bash
cd /tmp
git clone --depth 1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

### 4. Start PostgreSQL

```bash
sudo pg_ctlcluster 14 main start
# Verify: pg_isready → "accepting connections"
```

## Database Setup

```bash
# Create database and user
sudo -u postgres psql -c "CREATE DATABASE ergeneai;"
sudo -u postgres psql -c "CREATE USER hermes WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ergeneai TO hermes;"

# Enable pgvector
sudo -u postgres psql -d ergeneai -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## Schema

```sql
-- DIMENSION: 384 for sentence-transformers, 1536 for OpenAI text-embedding-3-small
CREATE TABLE hermes_memory (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    category VARCHAR(50),           -- 'tech_note', 'business_strategy', 'personal_reminder', 'genel'
    embedding VECTOR(384),          -- or VECTOR(1536) for OpenAI
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- IVFFlat index for cosine similarity search
CREATE INDEX ON hermes_memory USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO hermes;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO hermes;
```

**Dimension decision:**
- **384** → sentence-transformers (local, free, Turkish-compatible, offline)
- **768** → Gemini embedding
- **1536** → OpenAI text-embedding-3-small (best quality, paid, needs API key)

Change dimension with: `ALTER TABLE hermes_memory ALTER COLUMN embedding TYPE VECTOR(N);`

## tools.py Functions

### pg_kaydet(content, category)

Saves text with auto-generated embedding vector.

```python
pg_kaydet("Bilal kuryelikten kurtulmak istiyor", "business_strategy")
# → "✅ PG beyne kaydedildi (business_strategy)"
```

### pg_ara(search_text, limit=5)

SQL ILIKE keyword search. Fast but not semantic.

```python
pg_ara("kurye")
# → [{"id": 1, "content": "...", "category": "business_strategy", "tarih": "2026-06-02"}]
```

### pg_ara_vector(query, limit=5, threshold=0.3)

Semantic vector search via cosine similarity. Finds conceptually similar content even with different wording.

```python
pg_ara_vector("parayi nasıl kazanacağım", limit=3)
# → [{"id": 1, "content": "...", "benzerlik": 0.43, ...}]
```

Threshold (0.0–1.0): higher = stricter match. Start at 0.3, adjust based on results.

### pg_son(limit=5)

Most recent entries.

## Embedding Model

Uses `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`:
- **384 dimensions**
- **Multilingual** (Turkish, English, German, etc.)
- **Runs offline** — no API key needed
- **Cached** — first load takes ~5s, subsequent calls instant
- **Loaded as singleton** in tools.py to avoid repeated model loading

```python
# _get_embedding("any text") → [0.012, -0.045, ...] (384 floats)
```

### Switching to OpenAI Embeddings

If you add an OpenAI API key later:

```python
def _get_embedding(text):
    import requests
    resp = requests.post(
        "https://api.openai.com/v1/embeddings",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        json={"input": text, "model": "text-embedding-3-small"}
    )
    return resp.json()['data'][0]['embedding']  # 1536-dim
```

Then change table: `ALTER TABLE hermes_memory ALTER COLUMN embedding TYPE VECTOR(1536);`

## Connection Config

```python
PG_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "ergeneai",
    "user": "hermes",
    "password": "your_password"
}
```

## Backup & Restore

```bash
# Backup
pg_dump -U hermes ergeneai > ~/pg_backup_$(date +%Y%m%d).sql

# Restore
psql -U hermes ergeneai < pg_backup_20260602.sql
```

## Pitfalls

- **pgvector compilation fails** without `postgresql-server-dev-14` — install it first
- **Read-only /usr** prevents apt install — remount with `sudo mount -o remount,rw /usr`
- **Disk full** breaks dpkg — clean with `sudo apt-get clean; sudo journalctl --vacuum-time=3d`
- **IVFFlat index needs data** — created before data insertion causes "little data" warning, normal, drop and recreate later if recall is low
- **Docker permission denied** on this server — PostgreSQL installed natively instead
- **Embedding model first load is slow** (~5s) — subsequent calls are instant once cached. Çözüm: Embedding Daemon (port 8767, HTTP API, model RAM'de sıcak)
- **sentence-transformers warning** about unauthenticated HF Hub requests is benign — set `HF_TOKEN` env var to suppress
- **psycopg2** — use `psycopg2-binary` to avoid compilation: `pip install psycopg2-binary`
- **n8n container filesystem izolasyonu** — n8n container'ının /tmp'si host'tan izoledir. Temp file yazma yaklaşımı çalışmaz. Çözüm: (1) n8n HTTP Request node ile Embedding Daemon'a direkt bağlan, (2) n8n volume mount'ına yaz (`/var/lib/docker/volumes/..._n8n-data/_data/` -> `/home/node/.n8n/`)
- **n8n HTTP Request > Execute Command** — container izolasyonu varsa Execute Command kullanma. HTTP Request node ile embedding daemon'a POST at. Çok daha temiz, hızlı ve güvenli.

## Related

- `google-oauth-headless` — how the Gmail/Calendar/Drive/Sheets tokens were obtained
- `google-api-server` — Google API service builders and operations
- `server-maintenance` — disk cleanup, command installation, service retirement patterns

---

## ChromaDB Emeklilik Notu (Haziran 2026)

ChromaDB (port 8001) üretimden kaldırıldı. Sebep: Sürekli "Connection refused" hatası, kritik olmayan ama raporları "degraded" gösteren bir bileşendi. Değiştirme adımları:

1. **Kod temizliği:** `hermes_brain_core.py`'deki `collect_runtime_health_components()` fonksiyonundan ChromaDB health check kaldırıldı
2. **Fonksiyon yönlendirme:** `tools.py`'deki `beyin_ara()` ve `beyin_kaydet()` tamamen PostgreSQL (`pg_ara_vector()` / `pg_kaydet()`) üzerinden çalışacak şekilde güncellendi
3. **Bağımlılık kaldırma:** ChromaDB Python paketi tutuldu ama kullanılmıyor — tam kaldırma için `pip3 uninstall chromadb`
4. **Test:** `hermes_durum` "healthy" döndürüyor, 6/6 bileşen OK

**Neden tamir edilmedi:** PostgreSQL + Embedding Daemon tüm işlevi 20ms gecikmeyle karşılıyordu. ChromaDB'yi tamir etmek için harcanacak efor, sıfır ek değer sağlayacaktı. Embedding Daemon (8767) zaten modeli RAM'de sıcak tutuyor, PostgreSQL vektör aramayı native yapıyor.

---

## n8n Integration — Kendini Execute'den Güvenli Çağırma

PG hafızayı n8n workflow'undan kullanmak için **Execute Command** node'u kurulur. İki yaklaşım var: hatalı olan (inline `-c`) ve güvenli olan (bridge script).

### ❌ HATALI YAKLAŞIM: Inline `-c` (SyntaxError Riski)

```bash
# ASLA BOYLE YAPMA — triple quote içinde user text patlar
python3 -c "import tools; tools.pg_kaydet('''{{ $json.payload.content }}''', '{{ $json.payload.category }}')"
```

**3 patlama noktası:**

| Sorun | Senaryo | Sonuç |
|---|---|---|
| 1 | `content` içinde `'''` varsa | Python SyntaxError — erken kapanır |
| 2 | `content` newline (`\n`) içeriyorsa | `-c` flag syntax hatası |
| 3 | `content` içinde shell special char varsa (`$`, `` ` ``, `\`) | Beklenmedik escape sorunları |

### ✅ DOĞRU YAKLAŞIM: Bridge Script

n8n ÖNCE bir Code Node ile payload'u temp file'a yazar, SONRA Execute Command bu dosyayı okur.

**Adım 1 — Code Node (temp file'a yaz):**
```javascript
const fs = require('fs');
fs.writeFileSync('/tmp/n8n_input.json', JSON.stringify($json.payload));
return $json;
```

**Adım 2 — Execute Command (bridge script'i çağır):**
```bash
python3.11 /home/hermes/hermes_data/n8n_bridge.py --action save_memory --input /tmp/n8n_input.json
```

### n8n_bridge.py — Bağımsız Bridge Script'i

`/home/hermes/hermes_data/n8n_bridge.py` dosyası tools.py'ye **bağımlı değildir**. Kendi psycopg2 + sentence-transformers bağlantısını kurar. Bu sayede hangi Python çağırırsa çağırsın tools.py'deki chromadb import sorunu yaşanmaz.

**Desteklenen aksiyonlar:**

| --action | Input bekler | Çıktı |
|---|---|---|
| `save_memory` | `{"content": "...", "category": "..."}` | `{"sonuc": "✅ PG beyne kaydedildi (...)"}` |
| `search_memory` | `{"sorgu": "...", "limit": 5, "esik": 0.3}` | `[{"id":1, "content":"...", "benzerlik":0.43}]` |

**Komut şablonu:**
```bash
# Kaydet
python3.11 /home/hermes/hermes_data/n8n_bridge.py --action save_memory --input /tmp/n8n_input.json

# Ara
python3.11 /home/hermes/hermes_data/n8n_bridge.py --action search_memory --input /tmp/n8n_input.json
```

Script kendi temp dosyasını işlem sonunda siler (otomatik cleanup).

### n8n Switch Node Yapılandırması

**Switch Node:**
- Property Name: `{{ $json.intent }}`
- Type: String
- Route 1: `save_memory` → Execute Command (save)
- Route 2: `search_memory` → Execute Command (search)
- Route 3: `casual_chat` → Webhook Response

**Code Node (intent belirleme) — Switch'ten önce:**
```javascript
const text = $json.text || $json.body || "";
const lower = text.toLowerCase();

if (lower.includes("kaydet") || lower.includes("not et") || lower.includes("hatırla")) {
  return {
    intent: "save_memory",
    payload: { content: text, category: lower.includes("strateji") ? "business_strategy" : "genel" },
    reply: "Not edildi."
  };
} else if (lower.includes("ara") || lower.includes("bul") || lower.includes("ne yazıyordu")) {
  return {
    intent: "search_memory",
    payload: { sorgu: text, limit: 3 },
    reply: "Hafızada taranıyor..."
  };
}
return { intent: "casual_chat", payload: {}, reply: "" };
```

### Python Sürüm Disiplini

Sistemde 3 farklı Python var. n8n Execute Command için hangisini kullanacağını kontrol et:

| Binary | Python | psycopg2 | sentence-transformers | chromadb |
|---|---|---|---|---|
| `/usr/bin/python3` | 3.10 | ❌ | ❌ | ❌ |
| `python3.11` | 3.11 | ✅ | ✅ | ✅ |
| `/opt/hermes/venv/bin/python3` | 3.11 | ❌ | ❌ | ✅ |

**Kural:** n8n Bridge script'i her zaman `python3.11` ile çağır.

```bash
# Kontrol:
python3.11 -c "import psycopg2; import sentence_transformers; print('OK')"
```

Hangi paket nerede? Kontrol komutu:
```bash
python3.11 -m pip list | grep -iE "psycopg|sentence|chroma"
```

### Model Loading Optimizasyonu

**Sorun:** n8n Execute Command her çağrıda yeni bir Python process açar. sentence-transformers modeli her seferinde diskten yüklenir (~2-3sn).

**Çözüm (uygulandı):** Embedding Daemon — modeli RAM'de sıcak tutan HTTP API sunucusu port 8767'de.

**Çözümler (sıralı, öncelik sırası):**
1. ✅ **Embedding Daemon (HTTP API)** → model RAM'de sıcak, n8n HTTP Request node ile direkt çağırır. Detaylar: `references/embedding-daemon.md`
2. 🔲 ChromaDB HTTP API → embedding'i ChromaDB üzerinden al (ChromaDB zaten modeli cache'ler)
3. 🔲 `sys.stdin` streaming → n8n'den pipe ile besle, tek process'te bekle

### n8n-spesifik Pitfalls

- **Inline `-c` ile triple quote kullanma** — SyntaxError patlar, her zaman bridge script kullan
- **Temp file race condition** — `/tmp/n8n_input.json` çakışabilir, unique filename kullan (örn. `uuid` ile)
- **Execute Command timeout** — model yüklenirken timeout yiyebilirsin, n8n'de timeout'u 30sn yap
- **Yanlış Python'da paket yok** — her zaman `python3.11` ile çağır, `python3` ile değil
- **Çıktı JSON parse edilemezse** — bridge script stdout'a JSON basar, n8n `{{ $json }}` ile parse eder. Print statement karışırsa JSON bozulur
- **n8n dosyaya yazamazsa** — `fs.writeFileSync` permission hatası verirse `os.tmpdir()` dene
- **n8n container dosya izolasyonu** — container içindeki `/tmp` host'tan ayrıdır. Temp file yaklaşımı çalışmaz. İki çözüm: (1) HTTP Request node ile Embedding Daemon'a bağlan (önerilen), (2) n8n volume mount'ına (`/home/node/.n8n/`) yaz, host'ta `/var/lib/docker/volumes/..._n8n-data/_data/` altından oku

### Advanced: Embedding Daemon (HTTP API) ile n8n Entegrasyonu

Model her çağrıda yüklenmesin ve container izolasyonu sorunu yaşanmasın diye **Embedding Daemon** inşa edildi.

**Mimari:**

```
n8n Workflow
  └─ AI Agent (kullanıcı mesajı)
      └─ Code Node (intent belirle)
          └─ Switch Node
              ├─ save_memory → HTTP Request: POST http://host.docker.internal:8767/memory/save
              ├─ search_memory → HTTP Request: POST http://host.docker.internal:8767/memory/search
              └─ casual_chat → Webhook Response
```

**Daemon:** `/home/hermes/hermes_data/embedding_daemon.py` — port 8767, 0.0.0.0, HTTPServer (Flask gerektirmez).

**Endpoints:**

| POST | Body | Response |
|---|---|---|
| `/embed` | `{"text": "..."}` | `{"vector": [384 floats], "boyut": 384}` |
| `/memory/save` | `{"content": "...", "category": "..."}` | `{"sonuc": "✅ Hafizaya kaydedildi (business_strategy)"}` |
| `/memory/search` | `{"sorgu": "...", "limit": 5, "esik": 0.3}` | `{"sonuc": [...], "adet": 2}` |
| `GET /health` | — | `{"status": "ok", "model_loaded": true}` |

**Gecikme:** 20ms (eski 2sn'ydi). Model başlangıçta RAM'e yüklenir, bir daha yüklenmez.

**Daemon'u başlatma:**
```python
# Arka planda:
python3.11 /home/hermes/hermes_data/embedding_daemon.py &
# Detaylar: references/embedding-daemon.md
```

**Watchdog:** Cron her 5dk'da `/health` endpoint'ini kontrol eder. Düşerse restart.

**Önemli:** n8n container'ından `host.docker.internal:8767` ile host'a erişilir (Docker host network). Coolify proxy varsa direkt `localhost:8767` da çalışabilir. `http://` kullan, HTTPS değil — internal network.

### Güncel n8n_bridge (v2) — Daemon-First Architecture

`n8n_bridge.py` artık önce Embedding Daemon'a istek atar, daemon yanıt vermezse direkt model yükleyip fallback yapar. Bu sayede:

- Daemon ayaktayken → 20ms, sıfır model yükü
- Daemon down'ken → 2sn, kendi yükler (graceful degradation)

```bash
# Daemon-first kullanım (CLI)
python3.11 /home/hermes/hermes_data/n8n_bridge.py --action save --content "not" --category "genel"
python3.11 /home/hermes/hermes_data/n8n_bridge.py --action search --query "toplanti notlari" --limit 5
```

### Reference Files

- **Script'ler:**
  - `n8n_bridge.py` — `ergeneai-core/n8n_bridge.py` veya `/home/hermes/hermes_data/n8n_bridge.py`
  - `embedding_daemon.py` — `ergeneai-core/embedding_daemon.py` veya `/home/hermes/hermes_data/embedding_daemon.py`
- **Referanslar:**
  - `references/n8n-bridge-pattern.md` — temp file + Execute Command pattern (eski)
  - `references/embedding-daemon.md` — HTTP API daemon pattern (yeni, önerilen)
- **Kurulum:**
  - `references/02-haziran-2026-kurulum-hikayesi.md` — PG kurulumu ve ilk test süreci
