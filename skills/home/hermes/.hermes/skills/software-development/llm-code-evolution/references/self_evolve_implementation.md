# self_evolve.py — Uygulama Referansı

Oluşturulma: 1 Haziran 2026
Hedef: tools.py'ye LLM ile yeni fonksiyon ekleme

## Dosya Yapısı

```
~/hermes_data/self_evolve.py   — ana script
~/hermes_data/tools.py          — hedef dosya (appended)
/tmp/test_ekle.py              — geçici test dosyası (silinir)
```

## Fonksiyonlar

### `_api_key_al()` — .env'den API key oku
- `~/.hermes/.env` dosyasını açar
- `DEEPSEEK_API_KEY=...` satırını bulur
- Fallback: `os.environ.get("DEEPSEEK_API_KEY")`
- **Kritik**: `os.environ` tek başına çalışmaz çünkü Hermes key'i shell'e export etmez

### `_test_ve_ekle(kod, fonksiyon_adi)` — ortak test motoru
- Kodu /tmp/test_ekle.py'ye yazar
- `subprocess.run(["python3.11", ...], timeout=15)` ile syntax kontrolü
- Test geçerse tools.py sonuna append + Telegram bildirimi
- Test geçmezse log_hata'ya kaydeder

### `llm_fonksiyon_yaz(fonksiyon_adi, aciklama, ek_bilgi="")` — DeepSeek ile kod üret
- DeepSeek API'ye POST (https://api.deepseek.com/v1/chat/completions)
- Model: deepseek-chat
- Temperature: 0.3
- Markdown kod bloklarını (` ```python `) temizler
- `_test_ve_ekle`'ye yollar

### `eksik_fonksiyon_yaz(fonksiyon_adi, aciklama)` — şablon tabanlı
- Basit try/except template'i
- Aynı test mekanizmasından geçer

## Karşılaşılan Sorunlar

### 1. `.env` okuma (ÇÖZÜLDÜ)
Hermes terminal'de `DEEPSEEK_API_KEY` set değil — sadece Hermes process'i içinde var.
`.env` dosyasını parse eden yardımcı fonksiyon eklendi.

### 2. Türkçe karakter/Unicode (ÇÖZÜLDÜ)
Python'da dotless-ı (U+0131) ile dotted-i (U+0069) FARKLI karakterlerdir.
```python
satir = satir.strip()  # BUG! sol: i, sağ: ı → iki farklı değişken
```
Çözüm: İngilizce değişken adları kullan (`line`, `result`, `key`).

### 3. Path (ÇÖZÜLDÜ)
Script path'i `/home/hermes/hermes_data/` — kullanıcı sık sık `/home/hermes_data/` yazıyor.
Python binary: `python3.11` — `python3` (3.10) chromadb import edemez.

## Test Komutu

```bash
python3.11 ~/hermes_data/self_evolve.py llm "gun_kontrol" "Verilen tarihe kac gun kaldigini hesaplar. Parametre: tarih_str (YYYY-AA-GG). Dönen: str"
```

**Not:** `gun_kontrol` test fonksiyonu başarıyla üretildi, tools.py'ye eklendi, test edildi, sonra temizlendi. Aynı pattern ile kalıcı fonksiyonlar üretilebilir.
