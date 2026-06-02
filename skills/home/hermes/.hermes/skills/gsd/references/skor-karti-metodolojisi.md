# Hermes Skor Kartı Metodolojisi

## Ne Zaman Kullanılır
Bilal "skor kartı" veya "puan durumu" dediğinde.
Periyodik olarak (günlük) otomatik güncellenebilir.

## Veri Toplama (Canlı)
Her çalıştırmada terminal ile güncel veriler toplanır:

| Veri | Kaynak | Komut |
|---|---|---|
| Port durumu | `ss -tlnp` | grep ile port sayısı |
| PG kayıt sayısı | PostgreSQL | kategorilere göre COUNT |
| Son 24h kayıt | PostgreSQL | WHERE created_at > NOW() - INTERVAL '24 hours' |
| Daemon durumu | curl localhost:8767/health | status + uptime |
| tools.py fonksiyon | grep '^def ' | satır sayısı |
| Test sayısı | grep 'def test_' | satır sayısı |

## Kategoriler ve Puanlama

### Altyapı (max 100)
- 5 port açık: 100
- Eksik port başına -20
- Kırık servis: 0

### Hafıza (max 100)
- 100+ kayıt: 100
- 30-99 kayıt: 60
- 10-29 kayıt: 40
- <10 kayıt: (sayı/10)*40

### Embedding Daemon (max 100)
- Çalışıyor: 100
- Çalışmıyor: 0

### Proaktif (max 100)
- son 24h'de her kayıt için +10 puan
- Brifing cron'u çalışıyorsa +20 bonus

### Test Kalitesi (max 100)
- Her test fonksiyonu için +10
- 10+ test: 100

### Karar Motoru (max 100)
- pg_proaktif_analiz kullanılıyorsa: 50
- pg_karar_analiz varsa: +30
- Risk puanlaması çalışıyorsa: +20

## Genel Skor Hesaplama
Tüm kategorilerin aritmetik ortalaması.
Hedef: 85+

## Çıktı Formatı
JSON dosyası: `/home/hermes/hermes_data/hermes_skor_karti.json`
Her çalıştırmada önceki skorla karşılaştır (değişim +/-).
