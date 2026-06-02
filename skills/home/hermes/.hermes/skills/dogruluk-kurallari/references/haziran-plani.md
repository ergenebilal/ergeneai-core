# haziran_plani.py — Finansal Planlama Sistemi

## Ne İşe Yarar
Ödeme/gelir takvimini tutar, vadesi 5 gün içinde olanları Telegram'a bildirir. `hesap_hesapla()` ile günlük bütçe hesaplar.

## Mevcut Plan (Haziran 2026)

| Ödeme | Tarih | Tutar | İlk Uyarı |
|---|---|---|---|
| Denizbank | 11 Haz | 5.000₺ | 6 Haz |
| Motor Sigorta | 14 Haz | 3.500₺ | 9 Haz |
| YK KMH | 15 Haz | 2.000₺ | 10 Haz |

## Kod Yapısı

```python
PLAN = {
    "Denizbank": {"tarih": "2026-06-11", "tur": "gider", "miktar": 5000},
    "Sigorta":   {"tarih": "2026-06-14", "tur": "gider", "miktar": 3500},
    "KMH":       {"tarih": "2026-06-15", "tur": "gider", "miktar": 2000},
}
```

`tur` alanı: `"gider"` veya `"gelir"`

## Cron
Her gün 10:30 TR: `30 10 * * * /usr/bin/python3.11 /home/hermes/hermes_data/haziran_plani.py`

## İlgili Dosyalar
- `~/hermes_data/haziran_plani.py`
- `~/hermes_data/hermes_calendar.py` — takvim yönetimi (4 fonksiyon: takvim_ekle, takvim_bugun, takvim_sonraki, takvim_tamamla)
- `~/hermes_calendar.json` — JSON takvim verisi
- `tools.py` — `hesap_hesapla()` ve `suan()` fonksiyonları

## Pitfall
- `PLAN` dict'i içinde `tur: "gider"` yazımı — türkçe karakter değil (ascii). `tur: "gelir"` de aynı şekilde.
- Calendar modülü çakışması: `calendar.py` ismi stdlib `calendar` ile çakışır. `hermes_calendar.py` kullan.
