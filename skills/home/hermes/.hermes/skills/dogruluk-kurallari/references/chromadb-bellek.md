# ChromaDB Kalıcı Bellek Sistemi

## Koleksiyonlar

| Koleksiyon | Amaç | Sorgu Fonksiyonu | Kayıt Fonksiyonu |
|---|---|---|---|
| `hermes_beyin` | Kalıcı bilgiler, sözler, hedefler, öğrenmeler | `beyin_ara()` | `beyin_kaydet()` |
| `bilal_notes` | Kullanıcının verdiği dosyalar | `bilal_notes_ara()` | `dosya_ekle()` |
| `hermes_hata_gecmisi` | Hata kayıtları | `get_hata_gecmisi()` | `log_hata()` |

## Neden ChromaDB?

Sistem hafızası (memory tool) sadece 4.000 karakter. Dolunca yeni bilgi eklenemiyor. ChromaDB sınırsız vektör tabanlı bellek — semantik arama ile en alakalı bilgiyi bulur.

## Kullanım Deseni

```python
import sys; sys.path.insert(0, '/home/hermes/hermes_data')
from tools import *

# Bilgi kaydet
beyin_kaydet("Bilal sabah 10:00'da kuryeye çıkıyor", "profil", "bilal")

# Bilgi ara
sonuc = beyin_ara("kurye saati")  # "Bilal sabah 10:00'da..." döner
```

## Ne Zaman `beyin_kaydet()` Çağrılır?

- Kullanıcı bir tercih belirttiğinde
- Kullanıcı bir hata düzelttiğinde ("şöyle yap, böyle yapma")
- Kullanıcı bir hedef veya söz verdiğinde
- Yeni bir çalışma şekli keşfedildiğinde
- Önemli bir sistem değişikliği yapıldığında

## Ne Zaman `beyin_ara()` Çağrılır?

- Kullanıcı bir şey sorduğunda — önce beyinde ara (varsayılan)
- "Ne olmuştu?" sınıfındaki sorularda
- Kullanıcı profili / hedefi / geçmişi sorgulandığında

## Teknik Detay

- **Embedding modeli:** `paraphrase-multilingual-MiniLM-L12-v2` (Türkçe destekler)
- **ChromaDB host:** localhost:8001
- **Python:** 3.11 (chromadb 3.11'e kurulu)
- `beyin_kaydet()` otomatik MD5 hash ile ID üretir (aynı bilgi tekrar kaydedilmez)
- `beyin_ara()` koleksiyon yoksa "oluşturulmamış" mesajı döndürür
