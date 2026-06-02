# Auto-Feed Pipeline — Günlük Bilgi Toplama

## Ne işe yarar

Her gün otomatik olarak belirlenmiş kaynaklardan veri çeker, ChromaDB'ye ekler. Böylece `bilal_notes_ara()` sorguları her gün tazelenir.

## Bileşenler

```
~/.hermes/scripts/auto_feed.py   → Çalıştırılabilir script
Cron job (auto-feed-daily)       → Her gün 11:00 TR'de tetikler
ChromaDB koleksiyonu             → bilal_notes (tüm feed'ler buraya eklenir)
```

## Kaynaklar

| Kaynak | URL | Dosya Adı |
|--------|-----|-----------|
| GitHub Trending | https://github.com/trending | feed_github_trending_{tarih}.txt |
| Hacker News | https://news.ycombinator.com | feed_hacker_news_{tarih}.txt |
| Reddit r/programming | https://www.reddit.com/r/programming.json | feed_reddit_programming_{tarih}.txt |

## Script: auto_feed.py

**Konum:** `~/hermes_data/auto_feed.py` ve `~/.hermes/scripts/auto_feed.py`

```python
#!/usr/bin/env python3
"""
Hermes için otomatik beslenme script'i
Her gün çalışır, yeni bilgileri toplar, ChromaDB'ye ekler
"""
import sys
sys.path.insert(0, '/home/hermes/hermes_data')
from tools import web_cek, dosya_ekle, log_hata, telegram_mesaj_gonder
import json
import datetime

KAYNAKLAR = [
    ("https://github.com/trending", "github_trending"),
    ("https://news.ycombinator.com", "hacker_news"),
    ("https://www.reddit.com/r/programming.json", "reddit_programming"),
]

def topla_ve_kaydet():
    yeni_eklenen = []
    for url, kaynak_adi in KAYNAKLAR:
        try:
            icerik = web_cek(url)
            dosya_adi = f"/tmp/feed_{kaynak_adi}_{datetime.date.today()}.txt"
            with open(dosya_adi, 'w', encoding='utf-8') as f:
                f.write(f"Kaynak: {url}\nTarih: {datetime.date.today()}\n\n{icerik[:5000]}")
            sonuc = dosya_ekle(dosya_adi)
            yeni_eklenen.append(f"{kaynak_adi}: {sonuc}")
        except Exception as e:
            log_hata("auto_feed", f"{kaynak_adi} hatası: {e}", "tekrar dene")
    return yeni_eklenen

if __name__ == "__main__":
    print(f"[{datetime.datetime.now()}] Beslenme başladı...")
    sonuc = topla_ve_kaydet()
    print(f"Eklenenler: {sonuc}")
    # Telegram'a bildirim (Nexus botu üzerinden)
    if sonuc:
        mesaj = f"🌿 Günlük beslenme tamamlandı.\nEklenenler: {', '.join(sonuc)}"
    else:
        mesaj = "⚠️ Beslenme yapıldı ancak hiçbir kaynak eklenemedi. Logları kontrol et."
    telegram_mesaj_gonder(mesaj)
```

## Cron Yapılandırması

```
Job ID:    3e6032ab0990
İsim:      auto-feed-daily
Zamanlama: 0 8 * * * (11:00 TR)
Tetikleme: auto_feed.py (no_agent=True → direkt script çalışır, LLM harcanmaz)
Çıktı:     ChromaDB'ye kaydet + Telegram'a bildirim (Nexus botu)
Durum:     ✅ Aktif
```

```python
bilal_notes_ara('bugün github trend')
bilal_notes_ara('hacker news son haberler')
bilal_notes_ara('reddit programming popüler')
```

**Sabah raporu:** `morning_query.py` ile kaç doküman eklendiğini ve hata durumunu görebilirsin:

```bash
python3.11 ~/hermes_data/morning_query.py
# → "📚 6 doküman, ⚠️ 0 hata, ✅ Sistem hazır"
```

Detaylı dökümantasyon: `references/morning-query.md`

## Bakım

- Yeni kaynak eklemek için `KAYNAKLAR` listesine (url, isim) tuple'ı ekle
- `web_cek()` 2000 karakter limitlidir — long-form kaynaklar için ayrıca ele alınmalı
- Hatalar `log_hata()` ile ~/hermes_hata_log.txt'ye kaydedilir
- `no_agent=True` modu LLM tüketmeden çalışır; sadece stdout'u deliver eder

## Notlar

- **Python 3.11 ile çalıştır** (chromadb 3.11'e kurulu)
- **İlk çalıştırma:** sentence-transformers modeli yüklenir (~20sn). Sonrakiler cache'den anında.
- **Önbellek:** model cache ~/.cache/huggingface/ altında. Silinirse tekrar yüklenir.

## Bilinen Sorunlar

### 1. `web_cek()` ham HTML döndürür
`web_cek(url)` sadece `requests.get(url).text[:2000]` yapar. GitHub Trending ve HN sayfalarından ham HTML gelir, parse edilmez. Bu HTML ChromaDB'ye olduğu gibi eklenir ve semantik aramada işe yaramaz.

**Geçici çözüm:** Feed verilerini manuel olarak web'den çekip özet çıkar. (`morning_query.py` sadece doküman sayısını ve hata durumunu gösterir, özet çıkarmaz.)
**Kalıcı çözüm:** `auto_feed.py`'de BeautifulSoup/html2text ile HTML'den metin çıkar veya API'leri kullan (HN Firebase API, GitHub API).

### 2. Reddit Cloudflare JS challenge ile korunuyor
`reddit.com/r/programming.json` endpoint'i Cloudflare JS challenge ile korunuyor. Normal requests/curl ile geçilemez. Browser tool da challenge'ı handle edemez.

**Alternatif:** pushshift.io API, Reddit RSS feed'leri, veya eski.reddit.com.

### 3. `sentence-transformers` yoksa ChromaDB Python client patlar
`bilal_notes` koleksiyonu `paraphrase-multilingual-MiniLM-L12-v2` embedding modeli kullanır. `sentence_transformers` kurulu değilse `collection.query()` embedding generation'da hata verir.

**Çözüm:** REST API ile sorgula (bkz. `references/chromadb-rest-api.md`).

### 4. `calendar.py` shadowing
`sys.path.insert(0, '/home/hermes/hermes_data')` yapınca `calendar.py` stdlib `calendar`'ı shadow eder, `httpx` importı patlar.

**Çözüm:** Path'i eklemeden önce `import calendar` yap (stdlib yüklenir, cache'de kalır).
