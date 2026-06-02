---
name: llm-code-evolution
version: 3.1.0
author: Hermes Agent
description: Self_evolve.py EXPERT — tools.py kod kalitesini AST ile analiz eden, eksikleri proaktif tespit eden, DeepSeek API ile 3-deneme düzeltme döngülü kod üreten ve oto-düzelten kendini-geliştirme sistemi
---

# LLM Code Evolution v3 — EXPERT

Self_evolve.py artık **sadece kod üreten bir script değil**, tools.py'nin sağlığını izleyen, eksikleri tespit eden, "şu eksik bunu eklemeliyim" diyen proaktif bir **kod evrim motoru**.

## Yetenek Matrisi

| Modül | Ne yapar | Nasıl çağrılır |
|---|---|---|
| `analiz_et()` | tools.py'yi AST ile tarar, her fonksiyona kalite skoru (0.0-1.0), kategori analizi, iyileştirme önerileri | `self_evolve.py analiz` |
| `ne_eklemeliyim()` | Analiz + hata logu trendleriyle eksikleri proaktif önerir, aciliyet belirtir | `self_evolve.py ne_eklemeliyim` |
| `kod_uret()` | DeepSeek ile fonksiyon üret → test et → 3 deneme düzeltme döngüsü → tools.py'ye ekle | `self_evolve.py uretim <ad> \"<açıklama>\" [kategori]` |
| `hata_coz()` | Hata veren fonksiyonu AST bul → DeepSeek düzelt → test et → tools.py'de değiştir | `self_evolve.py fix <ad> \"<hata>\"` |
| `kod_denetle()` | Detaylı kalite raporu: skor tablosu, en kötü 3, eksik kategoriler | `self_evolve.py denetle [ad]` |
| `degisiklik_gecmisi()` | hermes_evolve_log.json'dan son 10 değişiklik | `self_evolve.py gecmis` |
| `temizlik_oner()` | Silinebilecek kadar düşük kaliteli/kısa fonksiyonları tespit eder | `self_evolve.py temizlik` |
| `otonom_taram()` | Cron dostu özet: genel skor, düşük kaliteliler, eksik kategoriler + aciliyet | `self_evolve.py oto` |

## Analiz Motoru (AST Tabanlı)

`analiz_et()` Python AST (Abstract Syntax Tree) kullanarak her fonksiyonu yapısal olarak inceler:

**Kalite Skoru Bileşenleri:**
- `0.35` — Docstring var mı (en az 20 karakter)
- `0.35` — Try/except hata yönetimi var mı
- `0.15` — Tip ipucu (type hint) var mı
- `0.15` — Satır sayısı ≥ 8 (gerçek iş yapıyor mu)

**Skor Anlamı:**
- `≥ 0.80` = ✅ İYİ
- `0.50-0.79` = ⚠️ ORTA
- `< 0.50` = ❌ KÖTÜ

**Kategori Sistemi:** tools.py'deki `# === KATEGORİ ===` yorumlarına göre kategorileri otomatik tespit eder. Ön tanımlı kategori-fonksiyon eşlemesine göre hangi kategorilerin eksik olduğunu söyler (Google Drive, Google Sheets, Hava Durumu, Hatırlatıcı).

## Kod Üretimi — 3 Deneme Düzeltme Döngüsü

`kod_uret()` eski tek-atımlık üretimin aksine, hata alırsa DeepSeek'e hatayı geri gönderip düzeltme ister:

```
1. Üret → 2. AST + çalışma testi → 3. Hata varsa → 4. Düzeltme prompt'u → 5. Tekrar test (max 3)
```

**Önemli farklar (v2 → v3):**
- Mevcut importları ve fonksiyonları bağlam olarak gönderir
- Mevcut fonksiyonları çağırmaya izin verir (eski yasak kalktı)
- `temperature` başarısız denemelerde 0.3 → 0.2 düşer (daha konservatif)
- `max_tokens` 1024 → 2048 (daha kompleks fonksiyonlar)
- Kalite kontrol: docstring yoksa otomatik ekleme
- tools.py'ye eklerken print satırlarından önce, doğru kategori altına ekler
- Değişiklik geçmişine kaydeder + Telegram bildirimi

## Hata Düzeltme — Geri Dönüşümlü

`hata_coz()`:
1. AST'den hatalı fonksiyonun kaynak kodunu bulur
2. Eski kodu DeepSeek'e gönderir + hata mesajı
3. Düzeltilen kodu AST ile doğrular
4. tools.py'de eski kodun yerine yenisini koyar
5. Değişiklik geçmişine kaydeder

## Otomatik Tarama (Cron Silindi)

Eskiden her gün 12:00'de cron vardı. **Silindi** (kullanıcı minimal cron istiyor). Artık `self_evolve.py oto` **ihtiyaç anında** çağrılır:

```bash
python3.11 ~/hermes_data/self_evolve.py oto
```

Eğer bir gün cron'a geri eklenirse:
- Sadece tespit yapar, kod üretmez
- Genel skor < 0.5 ise KRİTİK uyarısı gönderir
- Genel skor ≥ 0.7 ise sessiz kalır (bildirim yok — spam olarak algılanır)

## ChromaDB Hermes Beyin Pattern'i

Bu session'da tools.py'ye `beyin_ara()` ve `beyin_kaydet()` fonksiyonları eklendi. Kalıcı bilgiler artık ChromaDB'de `hermes_beyin` koleksiyonunda tutulur:

- Sistem belleği (memory tool) 4.000 karakterle sınırlı — sadece yönlendirme amaçlı
- Asıl bilgiler ChromaDB'de: sınırsız, semantik arama ile bulunabilir
- `beyin_kaydet(bilgi, tur="genel", etiket="")` ile kaydet
- `beyin_ara(soru)` ile sorgula

**Bu pattern kritik:** Kullanıcı "bunu unutma" dediğinde veya uzun vadeli bilgi öğrendiğinde `beyin_kaydet()` kullan, memory tool'u tıkıştırma.

## Tam İyileştirme Pipeline'ı (Proven)

Bu session'da tools.py 0.39 → 0.88'e çıkarıldı. Kanıtlanmış sıra:

1. `ne_eklemeliyim` ile eksik kategorileri tespit et
2. Eksik kategoriler için kod üret (her fonksiyon ayrı çağrıda)
3. Düşük kaliteli mevcut fonksiyonları iyileştir (docstring + try/except + type hints)
4. `denetle` ile yeni skoru kontrol et
5. Tekrarla: hâlâ < 0.7 olan varsa iyileştir
6. `ne_eklemeliyim` ile son durumu doğrula

## CLI Referansı

```bash
# Analiz (JSON çıktı)
python3.11 ~/hermes_data/self_evolve.py analiz

# Ne eklemeliyim (doğal dil)
python3.11 ~/hermes_data/self_evolve.py ne_eklemeliyim

# Fonksiyon üret + test + ekle
python3.11 ~/hermes_data/self_evolve.py uretim drive_dosya_listele "Google Drive'daki dosyalari listeler"

# Hatalı fonksiyonu düzelt
python3.11 ~/hermes_data/self_evolve.py fix hatali_fonksiyon "NameError: ..."

# Kalite denetimi
python3.11 ~/hermes_data/self_evolve.py denetle

# Değişiklik geçmişi
python3.11 ~/hermes_data/self_evolve.py gecmis

# Otomatik tarama
python3.11 ~/hermes_data/self_evolve.py oto
```

## Önemli Uyarılar

- **Türkçe karakter değişken adı kullanma**: Python'da `ı` (dotless) ile `i` (dotted) farklı Unicode karakterlerdir. `satır` ile `satir` aynı değişken DEĞİLDİR. İngilizce değişken adları kullan.
- **tools.py mevcut fonksiyonlarını çağırabilirsin**: v3'te bu yasak kalktı. `kod_uret()` prompt'a mevcut fonksiyon listesini gönderir, üretilen kod bunları çağırabilir.
- **tools.py'ye yeni import ekleme**: Yeni bir kütüphane gerekiyorsa, fonksiyon içinde lokal import yap (`import requests as req`).
- **Hata mesajları Türkçe**: Üretilen fonksiyonlar Türkçe hata mesajı döndürmeli.
- **API key**: `~/.hermes/.env`'den okunur. `os.environ.get()` boş dönebilir.
- **python3.11**: chromadb, longtracer, google kütüphaneleri 3.11'de.
- **Hata logu**: Başarısız üretimler `~/hermes_hata_log.txt`'ye kaydedilir.
- **Değişiklik geçmişi**: Tüm ekleme/düzeltmeler `~/hermes_evolve_log.json`'a kaydedilir.

## İlişkili Skill'ler

- [autonomous-cron-scripts](../autonomous-cron-scripts/SKILL.md) — Cron script şablonları
- [external-code-discovery](references/external-code-discovery.md) — Kullanıcının harici LLM kodlarını keşfetme

## Referans Dosyalar

- `references/self_evolve_implementation.md` — self_evolve.py'nin yapısı ve karşılaşılan sorunlar
- `references/external-code-discovery.md` — Kullanıcının harici LLM'lerle (DeepSeek) yazdığı kodu keşfetme ve tools.py'ye entegre etme pattern'i
- `references/google-oauth-integration.md` — Google OAuth baştan sona gerçek hikâye: credentials keşfi, secret farkı, auth kodu exchange, token yönetimi, tüm fonksiyonların tools.py'ye entegrasyonu
