# Embedding Daemon — Sıfır Gecikmeli, Container-Güvenli Hafıza API'si

## Neden Var

1. **Model her çağrıda yükleniyordu** — n8n Execute Command her tetikte yeni Python process açar, sentence-transformers modeli diske her seferinde ~2sn yüklerdi.
2. **n8n container filesystem izolasyonu** — container içindeki `/tmp` host'tan ayrı. Temp file ile Execute Command yaklaşımı çalışmaz.
3. **Bridge script çözümü yarımcıydı** — temp file + Execute Command çalışırdı ama yavaştı.

## Çözüm: Embedding Daemon (port 8767)

```
┌─────────────┐     POST /memory/save     ┌──────────────────┐
│  n8n HTTP   │ ────────────────────────→  │  Embedding       │
│  Request    │                            │  Daemon          │
│  Node       │ ←────────────────────────  │  port 8767       │
└─────────────┘     JSON response          │  RAM'de sıcak    │
                                           │  model (384b)    │
                                           └────────┬─────────┘
                                                    │
                                           ┌────────▼─────────┐
                                           │  PostgreSQL      │
                                           │  ergeneai DB     │
                                           │  hermes_memory   │
                                           └──────────────────┘
```

## Dosya

- **Konum:** `/home/hermes/hermes_data/embedding_daemon.py`
- **Python:** `#!/usr/bin/env python3.11` (psycopg2 + sentence-transformers yüklü)
- **Bağımlılık:** tools.py'ye bağımlı DEĞİLDİR. Kendi PG + model bağlantısı var.

## Endpoints

### `GET /health`
```json
{"status": "ok", "model_loaded": true, "port": 8767, "uptime": "12345s"}
```

### `POST /embed`
```json
// Request:  {"text": "Merhaba dünya"}
// Response: {"vector": [0.012, -0.045, ...], "boyut": 384, "metin_kesiti": "Merhaba dünya"}
```

### `POST /memory/save`
```json
// Request:  {"content": "Toplantı notları", "category": "business_strategy"}
// Response: {"sonuc": "✅ Hafizaya kaydedildi (business_strategy)", "kategori": "business_strategy"}
```

### `POST /memory/search`
```json
// Request:  {"sorgu": "toplanti notlari", "limit": 5, "esik": 0.3}
// Response: {"sonuc": [{"id": 1, "content": "...", "category": "...", "benzerlik": 0.43, "tarih": "2026-06-02"}], "adet": 2}
```

## Başlatma

```bash
# Elle (test)
python3.11 /home/hermes/hermes_data/embedding_daemon.py

# Arka planda (üretim)
nohup python3.11 /home/hermes/hermes_data/embedding_daemon.py > ~/embedding_daemon.log 2>&1 &

# Durağını kontrol et
curl http://localhost:8767/health

# Log
tail -f ~/embedding_daemon.log
```

## Watchdog (Cron)

Her 5 dakikada bir kontrol eder. Düşerse restart atar.

```
Job ID: 490a1e1a2e1d
Schedule: every 5m
```

Manuel kontrol:
```bash
# Watchdog çalışıyor mu?
crontab -l | grep embedding
```

## n8n Entegrasyonu (HTTP Request Node)

n8n'de Execute Command yerine HTTP Request node kullan:

| Node Property | Değer |
|---|---|
| Method | POST |
| URL | `http://host.docker.internal:8767/memory/save` |
| Body | `{{ $json.payload }}` (JSON) |
| Response | `{{ $json }}` parse edilir |

Coolify proxy yoksa direkt `http://localhost:8767` da çalışır. Container'dan host'a erişim için `host.docker.internal` kullanılır.

## Gecikme Karşılaştırması

| Yöntem | 1. çağrı | Sonraki çağrılar |
|---|---|---|
| Inline `-c` | 3-5sn | 2-3sn |
| Bridge script (direkt) | 3-5sn | 2-3sn |
| Bridge script (daemon-first) | 5-7sn (fallback) | 20ms |
| **Daemon + HTTP Request** | **20ms** | **20ms** |

## Versiyon Geçmişi

- **v1 (2 Haz 2026):** İlk sürüm. HTTPServer + psycopg2 + sentence-transformers. 4 endpoint.
- **Varsayılan port:** 8767 (MCP=8765, Nanobot=8766 yanında)

## Önemli Detaylar

- **HTTP yerine FastAPI kullanılmadı** — ek bağımlılık (uvicorn, fastapi) gerektirmez. Python stdlib HTTPServer yeterli.
- **CORS açık** — `Access-Control-Allow-Origin: *` header'ı var, cross-origin isteklerde sorun çıkmaz.
- **Temp file cleanup** — istek otomatik cleanup yapar (manuel müdahale gerekmez).
- **Daemon down detection** — n8n_bridge otomatik fallback yapar, daemon yoksa direkt model yükler.
