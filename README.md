# ErgeneAI Core

Hermes Agent beyni — tools.py (53 fonksiyon, 0.88 kalite), self_evolve.py (EXPERT), Google entegrasyonu.

## İçindekiler
- `tools.py` — 53 fonksiyon: Gmail, Calendar, Drive, Sheets, Hava, Hatırlatıcı, ChromaDB, doğrulama
- `self_evolve.py` — Kendini geliştiren beyin (analiz, öneri, kod üretim, hata düzeltme)
- `google_api.py` — Google API wrapper (alternatif)
- `google_auth_server.py` — Local OAuth server

## Kurulum
```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2 chromadb longtracer
```

## Kullanım
```python
from tools import *
gmail_gonder("ornek@email.com", "Konu", "İçerik")
hava_durumu("Bursa")
takvim_etkinlik_ekle("Toplantı", "2026-06-03T10:00:00", "2026-06-03T11:00:00")
```
