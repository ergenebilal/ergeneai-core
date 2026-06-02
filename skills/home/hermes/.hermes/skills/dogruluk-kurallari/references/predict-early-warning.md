# predict.py — Erken Uyarı Sistemi

## Ne İşe Yarar
Kritik finansal tarihlerden önce ChromaDB'de o konuda yeterli belge var mı kontrol eder. Yeterli veri yoksa Telegram'a uyarı gönderir.

## Çalışma Mantığı
1. `KRITIK_KONULAR` dict'indeki her konu için bugüne kalan günü hesapla
2. 0-3 gün kalmışsa → ChromaDB'de o konuda belge ara (`bilal_notes_ara`)
3. Hiç belge yoksa → ⚠️ uyarı
4. 2'den az belge varsa → 📄 bilgi toplama önerisi
5. Telegram'a toplu uyarı mesajı gönder (`telegram_mesaj_gonder`)

## Kullanım
```bash
python3.11 ~/hermes_data/predict.py
```

## Cron
Her gün 11:20 TR:
```
20 11 * * * /usr/bin/python3.11 /home/hermes/hermes_data/predict.py >> /home/hermes/hermes_data/predict.log 2>&1
```

## Kurulum Notları
- `python3.11` kullan (chromadb 3.11'e kurulu)
- Hedef tarihler: Denizbank (11 Haz), Sigorta (14 Haz), KMH (15 Haz)
- Sadece 0-3 gün kala uyarır, erken sessiz
- API key: tools.py import ettiği için `.env`'ye gerek yok (tools.py zaten `~/.hermes/.env` okuyor)
