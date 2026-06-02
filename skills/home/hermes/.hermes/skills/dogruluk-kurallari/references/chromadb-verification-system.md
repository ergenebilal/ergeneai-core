# ChromaDB Doğrulama Sistemi

Kurulum: 1 Haziran 2026
Sebep: Hermes'in hafızadaki bilgilere güvenip hallüsinasyon yapması (ChromaDB "çalışıyor" dedi, çalışmıyormuş)

## Sistem Mimarisi

```
ChromaDB (localhost:8001)
├── bilal_notes          → notlar, araştırma bulguları, doğrulanmış veriler
└── hermes_hata_gecmisi  → geçmiş hatalar (tip, detay, doğru davranış)
```

## tools.py API (~/hermes_data/tools.py)

```python
from tools import *

# Sistem durumu kontrolü
check_system_status('chroma')
# → {'status': 'running', 'output': '...'}

# ChromaDB'de ara (default embedding, hızlı)
bilal_notes_ara('Gumroad fiyat', limit=3)
# → ['Gumroad API anahtarı örnek: rK_xxxx...']

# Hata kaydet
log_hata('abarti', 'Crawl4AI abartildi', 'Alternatifleri listele')
# → True

# Geçmiş hataları getir
get_hata_gecmisi(limit=5)
# → ['Hata: abarti...']

# Yeni not ekle
dosya_ekle('r10_analiz.txt', 'R10 bot pazarında 5 rakip var...')
# → True
```

## ÖNEMLİ: Python 3.11 Kullan

ChromaDB 1.5.9 ve sentence-transformers sadece Python 3.11'de kurulu.
```bash
# DOĞRU
python3.11 -c "import chromadb; ..."

# YANLIŞ (ModuleNotFoundError)
python3 -c "import chromadb; ..."
```

## Embedding Model Kararı

| Model | Diller | Hız | Ne Zaman Kullanılır |
|-------|--------|-----|---------------------|
| Default (all-MiniLM-L6-v2) | İngilizce | ⚡ Çok hızlı | Normal sorgular (tools.py varsayılanı) |
| paraphrase-multilingual-MiniLM-L12-v2 | 12 dil (Türkçe dahil) | 🐢 Yavaş | Türkçe sorgular, kesin sonuç gerek |
| emrecan/bert-base-turkish-cased-mean-nli | Türkçe | 💀 **BOZUK** | KULLANMA. Yüklenmiyor.

```python
# Türkçe sorgu için (yavaş, sadece gerektiğinde)
from tools import get_bert_client
client, ef = get_bert_client()
col = client.get_collection('bilal_notes', embedding_function=ef)
results = col.query(query_texts=['Türkçe sorgu'], n_results=3)
```

## Permission Sorunu — DİKKAT

~/.hermes/skills/ altında SKILL.md varlığını kontrol ederken:
```bash
# YANLIŞ — permission denied olunca "yok" sayar
[ ! -f "SKILL.md" ] && echo "yok"

# DOĞRU — sudo ile kontrol et
sudo ls -la "SKILL.md"
find /path -name "SKILL.md" 2>/dev/null
```

## 1 Haziran 2026 Denetim Sonuçları

Tüm sistemler fiziksel olarak kontrol edildi:

### ✅ Doğrulanan (çalışıyor/var)
- Hermes Gateway (8642/8644)
- Hermes MCP Server (8765)
- n8n (Docker/Coolify ile)
- ChromaDB (8001)
- Crawl4AI (Python 3.11)
- Hyperframes (npm v0.6.65)
- Ollama (11434, 2 model)
- Browser-Use (pip 0.12.9)
- Insta Memory Server (8899)
- Nanobot Gateway (18790/8766)
- Demo Menu (8769)
- Coolify (8000)
- Cron jobs (~12)

### ❌ Hallüsinasyon (yok/çalışmıyor)
- PilotDeck (18789/3001) — "çalışıyor" dedim, yok
- Kabine Chat (8767) — "çalışıyor" dedim, yok
- Gemini web2api proxy — "var" dedim, klasör yok
- model_switch.sh — "var" dedim, bulunamadı

## Kullanım Kuralı

Bir sistem hakkında konuşmadan ÖNCE:
1. `check_system_status()` veya manuel kontrol (ps aux, curl, ss)
2. Çıktıyı gör
3. Sonra konuş

Emin değilsen: "Bilmiyorum, şu komutu çalıştırıp bakayım" de.
