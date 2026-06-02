# Python Modül İsimlendirme Tuzakları

## Problem

`~/hermes_data/calendar.py` isimli bir dosya oluşturuldu. `from calendar import takvim_ekle` import edilmeye çalışıldığında Python kendi standart kütüphanesindeki `/usr/lib/python3.11/calendar.py`'yi buldu — ImportError.

## Etkilenen Modüller

| Dosya adı | Built-in modül | Etki |
|---|---|---|
| `calendar.py` | `calendar` | `from calendar import X` çalışmaz |
| `json.py` | `json` | `import json` standart kütüphaneyi alır |
| `datetime.py` | `datetime` | `import datetime` standart kütüphaneyi alır |
| `math.py` | `math` | `import math` standart kütüphaneyi alır |
| `os.py` | `os` | `import os` standart kütüphaneyi alır |
| `re.py` | `re` | `import re` standart kütüphaneyi alır |

## Çözümler

### 1. Dosyayı yeniden adlandır (ÖNERİLEN)
`calendar.py` → `hermes_calendar.py` veya `takvim.py`

### 2. sys.path.insert(0, ...) ile import et
```python
import sys
sys.path.insert(0, '/home/hermes/hermes_data')
from calendar import takvim_ekle  # artık özel dosyayı bulur
```
Not: Bu yöntem aynı dosya içinde sonraki tüm import'ları etkiler, dikkatli kullan.

## Önleyici Kural

Hermes_data'ya yeni bir .py dosyası eklerken:
1. Adın Python built-in modülüyle çakışmadığını kontrol et (`python3.11 -c "import X"` ile test et)
2. Çakışıyorsa ön ek ekle: `hermes_X.py`, `ergene_X.py`, `custom_X.py`
3. Alternatif: Türkçe ad kullan (`takvim.py`, `json_islemleri.py`)
