# otonom_calistir() — Otonom Görev Yürütücü

## Ne İşe Yarar

Bir hedefi `plan_hedef()` ile alt adımlara böler, güvenli adımları otomatik çalıştırır, tehlikeli adımlar için onay bekler.

## İmza

```python
def otonom_calistir(hedef: str, onay_gerekli: bool = True) -> list[dict]:
```

## Dönüş

Her adım için bir dict döner:
```python
{"adim": "...", "durum": "TAMAM|ONAY BEKLİYOR|HATA", "sonuc": "...", "mesaj": "..."}
```

## Güvenlik

**Tehlikeli kabul edilen işlemler** (onay gerektirir):
- `dosya_ekle`
- `terminal_calistir`
- `sil`, `yaz`, `guncelle`
- `api_post`, `gonder`

**Güvenli kabul edilen işlemler** (otomatik çalışır):
- `bilal_notes_ara` → Regex ile parsed edilir, ChromaDB'ye sorgu atılır
- `web_cek` → Regex ile URL parsed edilir, fetch yapılır
- `get_hata_gecmisi` → Doğrudan çağrılır

## Sınırlamalar

`plan_hedef()`'ten gelen adımlar şablon string'lerdir:
```python
["bilal_notes_ara(hedef)", "verify_claim(sonuc, kaynak)"]
# "hedef", "sonuc", "kaynak" placeholder olduğu için regex parse başarısız
```

Regex `func_name('argüman')` formatında tırnak içi değer arar. Placeholder değişkenleri tırnaksız olduğu için `"Hata: sorgu parse edilemedi"` döner.

## Çözüm

`otonom_calistir` doğrudan ChromaDB'ye hedefi soracak şekilde yeniden yazılmalı:

```python
def otonom_calistir(hedef, onay_gerekli=True):
    # plan_hedef'e güvenme, doğrudan ChromaDB'ye sor
    from tools import bilal_notes_ara, get_hata_gecmisi
    sonuc = bilal_notes_ara(hedef)
    hatalar = get_hata_gecmisi(3)
    return {"bulgular": sonuc, "hatalar": hatalar}
```

## Test

```python
from tools import otonom_calistir
sonuc = otonom_calistir('araştır: Etsy nişleri')
for s in sonuc:
    print(f"[{s['durum']}] {s['adim']}")
```
