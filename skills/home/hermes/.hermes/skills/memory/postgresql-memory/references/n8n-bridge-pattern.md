# n8n Bridge Pattern — PG Hafızayı Execute Command'den Çağırma

## Güncel Durum: Embedding Daemon Öncelikli

NOT: `n8n_bridge.py` v2 artık önce Embedding Daemon'a (port 8767) istek atar. Daemon yoksa fallback yapar.
Daemon ayaktayken gecikme ~20ms, down'ken ~2sn. Ayrıntı: `references/embedding-daemon.md`

## Architecture (Eski - Execute Command ile)

```
n8n Workflow
  └─ AI Agent (kullanıcı mesajı)
      └─ Code Node (intent belirle: save_memory / search_memory / casual_chat)
          └─ Switch Node (intent'e göre yönlendir)
              ├─ save_memory → Code Node (temp file'a yaz) → Execute Command (n8n_bridge.py --action save_memory)
              ├─ search_memory → Code Node (temp file'a yaz) → Execute Command (n8n_bridge.py --action search_memory)
              └─ casual_chat → Webhook Response
```

## Neden Inline `-c` Kullanılmaz

n8n şablonlarındaki yaygın hata:

```bash
# ❌ PATLAR:
python3 -c "import tools; tools.pg_kaydet('''{{ $json.payload.content }}''', '...')"
```

Sebep: `{{ $json.payload.content }}` çözüldükten sonra içinde `'''` veya `\n` varsa Python syntax hatası.

## Çözüm: Code Node → Temp File → Execute Command

**Code Node (temp file'a yaz):**
```javascript
const fs = require('fs');
const path = '/tmp/n8n_' + Date.now() + '.json';
fs.writeFileSync(path, JSON.stringify($json.payload));
return { ...$json, tempFile: path };
```

**Execute Command:**
```bash
python3.11 /home/hermes/hermes_data/n8n_bridge.py --action save_memory --input /tmp/n8n_1717000000.json
```

## Bridge Script Çıktı Formatı

**save_memory başarılı:**
```json
{"sonuc": "✅ PG beyne kaydedildi (business_strategy)", "kategori": "business_strategy"}
```

**save_memory hata:**
```json
{"hata": "PG kayit hatasi: No module named 'psycopg2'"}
```

**search_memory başarılı:**
```json
[{"id": 1, "content": "...", "category": "business_strategy", "benzerlik": 0.43, "tarih": "2026-06-02"}]
```

**search_memory boş:**
```json
[]
```

## Python3.11 Kontrolü

```bash
python3.11 -c "import psycopg2; import sentence_transformers; print('OK')" || echo "Paket eksik"
```

## Embedding Model Yüklenme Süresi

- İlk çağrı (diskten yükle): ~2-3sn
- Sonraki çağrılar: yine ~2-3sn (her Execute Command yeni process)
- Çözüm: embedding daemon (ileride)
