---
name: self-improvement
version: 1.0.0
description: Use self_evolve.py to analyze, generate, fix, and improve tools.py — Hermes'in kendini geliştirme sistemi
trigger: user asks to improve Hermes, add functions, fix bugs in tools.py, or raise code quality
---

# Self-Improvement System

`/home/hermes/hermes_data/self_evolve.py` — Hermes'in kendini geliştiren beyni.

## Available Commands

```bash
python3.11 /home/hermes/hermes_data/self_evolve.py <komut>

analiz           # tools.py'yi AST ile tara, kalite skoru çıkar
ne_eklemeliyim   # "şu eksik, bunu eklemeliyim" — eksik/iyileştirme önerisi
uretim <ad> '<açıklama>' [kategori]  # DeepSeek ile kod üret + test + tools.py'ye ekle
fix <ad> '<hata>'          # hatalı fonksiyonu DeepSeek'e gönder, düzelt
denetle [fonksiyon_adı]    # detaylı kalite raporu (tablo)
gecmis                     # değişiklik geçmişi
temizlik                   # gereksiz fonksiyon temizliği önerisi
oto                        # otomatik tarama (cron)
```

## Code Quality Standards (tools.py)

- **Docstring**: Her fonksiyonda zorunlu (Args + Returns + örnek)
- **Try/Except**: Her fonksiyonda zorunlu (hatayı string olarak döndür)
- **Type Hints**: Parametre ve dönüş tipi belirtilmeli
- **Hata Mesajları**: Türkçe, "❌" ikonlu
- **Minimum Kalite Skoru**: Yeni fonksiyonlar ≥ 0.85, eski ≥ 0.7

## Adding a New Function (Manual)
1. `self_evolve.py uretim <ad> '<açıklama>'` ile DeepSeek'ten üret
2. Otomatik test edilir (python3.11 syntax check)
3. Başarısız olursa 3 defa düzeltme döngüsü
4. tools.py'nin sonuna, print satırlarından önce eklenir
5. Print listesine yeni fonksiyon adını ekle

## Fixing a Broken Function
1. `self_evolve.py fix <fonksiyon_adı> '<hata_mesajı>'`
2. Eski kod yedeklenir (tools.py.bak)
3. DeepSeek düzeltilmiş kodu üretir
4. Test edilir, geçerse tools.py'ye yazılır

## Improving Existing Functions
1. Tespit: `self_evolve.py ne_eklemeliyim` → düşük skorluları göster
2. Elle ekle: docstring, try/except, type hints
3. Test: `python3.11 -c "from tools import *; fonksiyon()"`
4. Doğrula: `self_evolve.py denetle` → skorun yükseldiğini kontrol et

## Pitfalls
## Pitfalls
- DeepSeek API key ~/.hermes/.env'de: `DEEPSEEK_API_KEY=*** - python3.11 kullan (3.10'da google kütüphaneleri yok)
- tools.py'de SENKRONIZASYON: print satırlarını da güncellemeyi unutma
- self_evolve.py cron'a eklenebilir (günde 1 kez yeterli, 12:00)
- Kullanıcı cron spam'den nefret eder — sadece gerçek verisi olan işleri kronla

## Cron Discipline (CRITICAL)
Kullanıcı cron spam konusunda çok hassas. Şu kurallara uy:

1. **Verisi olmayan cron açma** — "finans raporu" hazırlamak için önce Google Sheets'te veya başka bir yerde gerçek finans verisi olmalı. Yoksa açma.
2. **Template/boş cron açma** — "şablon rapor" atan cron'lar direkt silinir. Boş alanlar, "BOŞ" yazan satırlar kabul edilemez.
3. **Günde 1'den fazla benzer cron** — spam. X Deep Surf x3 gibi aynı işi günde 3 kere yapan cron'lar direkt silinir.
4. **Check-in/rapor cron'ları** — sadece gerçekten ihtiyaç varsa aç. Kullanıcı istemediği sürece sabah/akşam check-in'i bile açma.
5. **Sistem cron'ları** — watchdog gibi kritik sistem cron'ları da kullanıcı rahatsız olursa silinebilir. "Hepsini sil" derse sorgulamadan sil.
6. **Test et** — cron'u açmadan önce prompt'unu test et: "Bu çalışınca kullanıcıya ne gidecek?" Cevap boş/template/placeholder ise açma.