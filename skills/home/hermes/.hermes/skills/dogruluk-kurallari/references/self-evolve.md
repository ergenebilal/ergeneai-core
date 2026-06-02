# self_evolve.py — Otomatik Fonksiyon Üretici

## Ne İşe Yarar
Yeni bir fonksiyon adı ve açıklaması verildiğinde ya şablon kod üretir ya da **DeepSeek API ile gerçek Python kodu** üretir. `/tmp/test_ekle.py`'de syntax+çalışma testi yapar, test geçerse `tools.py`'ye ekler ve Telegram bildirimi gönderir.

## İki Mod

### 1. Şablon Mod (template)
Basit try/except template'i. Hızlı placeholder fonksiyonlar için.

```python
from self_evolve import eksik_fonksiyon_yaz
eksik_fonksiyon_yaz("yeni_islev", "Kısa açıklama")
```

### 2. LLM Mod (llm) — GELİŞMİŞ
DeepSeek API ile gerçek Python fonksiyonu üretir. Prompt'a göre kod yazar, test eder, ekler.

```bash
python3.11 ~/hermes_data/self_evolve.py llm <ad> "<açıklama>" "[ek_bilgi]"
```

**API Key:** `~/.hermes/.env` dosyasından `_api_key_al()` ile okunur (shell env değil, dosyadan okur).
**Model:** `deepseek-chat` (OpenAI uyumlu), temperature 0.3, max_tokens 1024.
**Test:** `subprocess.run(["python3.11", test_dosya], capture_output=True, timeout=15)`
**Kod temizleme:** Markdown kod blokları (`` ```python ``) otomatik temizlenir.

### Örnek (test edildi)
```bash
python3.11 ~/hermes_data/self_evolve.py llm "gun_kontrol" \
  "Verilen tarihe kac gun kaldigini hesaplar. Parametre: tarih_str (YYYY-AA-GG). Dönen: str"
```
→ `gun_kontrol('2026-06-11')` → `"10 gun kaldi"` ✅

## Çalışma Mantığı
1. Kullanıcı fonksiyon adı + açıklama verir
2. LLM mod: DeepSeek API'ye POST, yanıttan kod çıkar
3. /tmp/test_ekle.py'ye yaz ve `python3.11` ile test et
4. Test OK → tools.py sonuna append + Telegram bildirimi
5. Test FAIL → `log_hata()` ile kaydet

## Önemli Uyarılar
- **Türkçe karakter değişken adı kullanma:** Python'da dotless-`ı` (U+0131) ile dotted-`i` (U+0069) farklı Unicode karakterlerdir. `satır` ≠ `satir`. Hep İngilizce değişken adı kullan.
- **tools.py fonksiyonlarını çağırma:** Üretilen fonksiyon bağımsız olmalı (tools.py import etmez).
- **`python3.11` zorunlu:** chromadb 3.11'e kurulu.
- **Path:** `/home/hermes/hermes_data/` (kullanıcı `/home/hermes_data/` yazmaya meyilli, düzelt).
- **Script'e yeni fonksiyon eklenirse `_test_ve_ekle()` ortak test motorundan geçer.**
