# Kurulu Sistem Özeti (Haziran 2026)

## tools.py — 16 Fonksiyon
`~/hermes_data/tools.py` — Ana doğrulama ve otonomi kütüphanesi.

**Python 3.11 gerekli** — chromadb/longtracer/sentence-transformers 3.11'e kurulu.

## Günlük Otomasyon

| Cron | Saat (TR) | Ne yapar |
|---|---|---|
| `kritik-uyari` (system crontab) | 14:15 | Denizbank/Sigorta/KMH tarih uyarısı → Nexus |
| `auto-feed-daily` (Hermes cron) | 11:00 | GitHub+HN+Reddit → ChromaDB → Nexus bildirimi |

## Telegram Bot: Nexus
- Token: tools.py içinde `TELEGRAM_BOT_TOKEN`
- Chat ID: `5506784207` (@Byergn)
- Fonksiyon: `telegram_mesaj_gonder(mesaj)` → doğrudan Telegram'a mesaj
- Not: Token tools.py'de düz metin. Her `cat > tools.py << 'EOF'` override'ında token kaybolur, tekrar eklenmeli.

## Servisler

| Servis | Port | Durum |
|---|---|---|
| ChromaDB | 8001 | ✅ v2 heartbeat |
| Hermes Gateway | 8642/8644 | ✅ |
| Hermes MCP | 8765 | ✅ |
| n8n | Docker/Coolify | ✅ |
| Coolify | 8000 | ✅ |

## Kritik Dosyalar

| Dosya | Ne işe yarar |
|---|---|
| `~/hermes_data/tools.py` | Ana kütüphane (16 fonksiyon) |
| `~/hermes_data/auto_feed.py` | Günlük beslenme (GitHub+HN+Reddit) |
| `~/hermes_data/kritik_uyari.py` | Tarih uyarıcı (Denizbank/Sigorta/KMH) |
| `~/hermes_data/takvim.py` | Takvim sistemi (calendar stdlib conflict'ten kaçın) |
| `~/hermes_data/morning_query.py` | Sabah sorgu script'i |
| `~/hermes_data/self_audit.sh` | Sistem denetim script'i |
| `~/hermes_hata_log.txt` | Hata log dosyası (henüz yok) |
| `~/hermes_calendar.json` | Takvim verisi |
| `~/.hermes/dijital_beyin_prompt.txt` | Kimlik dosyası |
| `/opt/hermes/awesome-hidden-gems/` | Gizli repo listesi (klonlandı) |

## Pitfall: calendar.py stdlib shadow
`/home/hermes/hermes_data/calendar.py` Python stdlib `calendar` modülünü ezer.
`sys.path.insert(0, ...)` ile hermes_data path'e eklenince, `httpx` (chromadb bağımlılığı)
`from calendar import timegm` yapamaz hale gelir.
**Çözüm:** Dosyayı `takvim.py` olarak yeniden adlandır (içindeki fonksiyon isimleri değişmez).
Servis kullanıyorsa restart gerekir.
