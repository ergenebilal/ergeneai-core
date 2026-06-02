# Takvim Sistemi — Haziran 2026

## Ne işe yarar

Bilal'in finansal takvimini tutar — borç ödeme günleri, sigorta bitişleri, kurye günleri. `calendar_bugun()` ile her sabah o günün yapılacaklarını gösterir.

## ⚠️ ÖNEMLİ: İsim Çakışması

`calendar.py` Python'un standart kütüphanesindeki `calendar` modülüyle çakışır. Çözüm: dosya adı `takvim.py` olarak değiştirildi.

```python
# DOĞRU KULLANIM:
from takvim import calendar_ekle, calendar_bugun

# YANLIŞ (stdlib calendar'ı ezer):
import sys; sys.path.insert(0, '/home/hermes/hermes_data')
from calendar import calendar_ekle  # ← httpx importı patlar
```

**Alternatif çözüm:** `sys.path.insert` yapmadan ÖNCE `import calendar` yap (stdlib cache'de kalır):

```python
import calendar  # önce stdlib yükle
import sys; sys.path.insert(0, '/home/hermes/hermes_data')
from calendar import calendar_ekle  # artık güvenli (stdlib cache'de)
```

## Bileşenler

```
~/hermes_data/takvim.py          → Kalıcı kaynak (git yedeklenir)
~/hermes_calendar.json           → Veri dosyası (otomatik oluşur)
```

## API

```python
from takvim import calendar_ekle, calendar_bugun

# Olay ekle
calendar_ekle("Denizbank ödeme", "2026-06-11", "09:00")
# → "Denizbank ödeme 2026-06-11 09:00 eklendi."

# Bugünün yapılacaklarını getir
calendar_bugun()
# → [{"olay": "...", "tarih": "2026-06-01", "saat": "11:00", "yapildi": False}]
```

## Veri formatı (`~/hermes_calendar.json`)

```json
[
  {"olay": "Denizbank ödeme", "tarih": "2026-06-11", "saat": "09:00", "yapildi": false},
  {"olay": "Motor sigorta bitiyor", "tarih": "2026-06-14", "saat": "23:59", "yapildi": false}
]
```

## Mevcut kayıtlar (Haziran 2026)

| Tarih      | Olay                        | Öncelik       |
|------------|-----------------------------|---------------|
| 1 Haz      | Kurye 11:00                 | ✅            |
| 11 Haz     | Denizbank ödeme ~9.000₺     | 🔴 KRİTİK     |
| 14 Haz     | Motor sigorta bitiyor       | 🔴 KRİTİK     |
| 15 Haz     | YK KMH ödeme 7.000₺         | 🔴            |

## Notlar

- JSON formatı basit, elle de düzenlenebilir
- `yapildi: false` → yapıldığında `true` yap, böylece `calendar_bugun()` onu göstermez
