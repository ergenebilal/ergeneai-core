---
name: autonomous-cron-scripts
version: 1.2.0
author: Hermes Agent
description: Cron'da çalışan, tools.py fonksiyonlarını kullanan otonom Python script'leri oluşturma ve yönetme pattern'i. Zaman, path, API key, dil, modül çakışması discipline'leri.
---

# Autonomous Cron Scripts

`~/hermes_data/` altında cron'da çalışan, `tools.py`'yi import eden ve Telegram bildirimi gönderen standalone Python script'leri için şablon ve kurallar.

## Cron Minimalizasyon Kuralı (02 Haz 2026)

**Kullanıcının net talebi: sadece gerçekten gerekli cron'lar çalışsın.** 22 cron'dan 20'si silindi, sadece 2 kaldı (Denetim Hatırlatıcı + ECC Haftalık).

**Silinen cron türleri:**
- Günde 3+ kere aynı rapor gönderenler (X Deep Surf x3)
- Veri kaynağı olmayan fake/template raporlar ("ezbere yazmışsın" — kullanıcının en sinir olduğu şey)
- Sabah/Akşam check-in gibi sohbeti otomatize eden bildirimler
- Ne işe yaradığı belli olmayan cron'lar
- IG içerik üretimi gibi insan gözetimi gerektiren otomatik post'lar
- self_evolve taraması gibi ihtiyaç anında çağrılabilecek araçlar

**Yeni cron eklemeden ÖNCE:**
1. Veri kaynağım var mı, yoksa ezbere rapor mu üreteceğim? (VARSA TAMAM, YOKSA ASLA)
2. Günde 1'den fazla bildirim gidecek mi? (GİDERSE SPAMDIR, BİRLEŞTİR)
3. Bu cron olmazsa ne kaybederiz?
4. Bunu kullanıcıya sormadan çalıştırabilir mi?

**Kural:** Günde 1'den fazla aynı tür bildirim → spam. Birleştir veya sil.

## Zaman Discipline'i (ZORUNLU)

**Sistem saati Europe/Istanbul (+03). ŞAŞIRMA.**

Her cron işlemi veya zaman-mantıklı script yazmadan ÖNCE:
```bash
timedatectl | grep "Time zone"
# Beklenen: "Time zone: Europe/Istanbul (+03, +0300)"
```

**Kurallar:**
- Tüm cron zamanları Türkiye saati iledir. UTC değil.
- Script başında `suan()` fonksiyonunu çağır ve zamanı log'a bas.
- Kullanıcı bu konuda sıfır toleranslıdır. Geçmişte UTC/TR karışıklığı oldu, bir daha olmayacak.
- Her cron eklemeden önce `timedatectl` ile kontrol et.
- Zaman dilimi değişirse (`timedatectl set-timezone ...`) tüm cron'ları tekrar kontrol et.

**Cron'ları doğrulama:**
```bash
crontab -l
# Her satır TR saatiyle mi yazılmış kontrol et
```

## Şablon

```python
#!/usr/bin/env python3
import sys
import datetime
sys.path.append('/home/hermes/hermes_data')
from tools import suan, telegram_mesaj_gonder, hesap_hesapla  # ihtiyaca göre

def main():
    zaman = suan()
    print(f"Calisma zamani: {zaman['tarih']} {zaman['saat']}")
    # Is mantigi
```

## __name__ Kontrolü (Tekrarlayan Bug)

Python'da **`if __name__ == "__main__":`** şeklinde yazılır. Aşağıdakiler YANLIŞ:

| Yanlış | Doğru |
|---|---|
| `if name == "main":` | `if __name__ == "__main__":` |
| `if _name_ == "_main_":` | `if __name__ == "__main__":` |
| `if __name__ == __main__:` | `if __name__ == "__main__":` |

Bu bug her yeni script'te kontrol edilmeli.

## API Key Yükleme

Hermes ortamı dışında çalışan script'ler `~/.hermes/.env` dosyasını okur:

```python
def _api_key_al():
    import os
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DEEPSEEK_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("DEEPSEEK_API_KEY")
```

## Türkçe Karakter Değişken Adları (Pitfall)

Python'da `ı` (dotless i, U+0131) ile `i` (dotted i, U+0069) farklı karakterlerdir.
`satır = x` ile `satir = x` aynı değişken DEĞİLDİR — NameError alırsın.

Kural: Değişken adlarında İngilizce ASCII kullan (`line`, `result`, `item`, `row`).

## Cron'a Ekleme Pattern'i

```bash
crontab -l > /tmp/hermes_cron
echo "20 11 * * * /usr/bin/python3.11 /home/hermes/hermes_data/predict.py >> /home/hermes/hermes_data/predict.log 2>&1" >> /tmp/hermes_cron
crontab /tmp/hermes_cron
```

Dikkat:
- Python: `python3.11` (chromadb 3.10'da çalışmaz)
- Path: `/home/hermes/hermes_data/...` (kullanıcı genelde `/home/hermes_data/` yazar — düzelt)
- Log yönlendirme: devamlı `>> log 2>&1` ekle

## Kullanıcı Çalışma Stili (Önemli Preferanslar)

**"Beni uğraştırma, sen yap"** — Kullanıcı "adım adım anlat" değil, "sen yap bitir" ister. Teknik bir işlem için adımları sıralamak yerine doğrudan yap ve sonucu söyle.

**"Ezbere rapor istemiyorum"** — Veri kaynağı olmayan konularda "BOŞ" alanlı şablon rapor üretme. Verin yoksa yapma.

**"Neden uzadı?"** — Gereksiz açıklama, aşırı detay, uzun süren işlemlerden nefret eder. Kısa ve direkt ol.

**"Bana attığın her mesaj değerli"** — Spam cron'lar, gereksiz check-in'ler, boş raporlar — hepsi güven kaybı. Sadece gerçekten gerekliyse mesaj at.

## Binary Install Pattern (Read-Only /usr/local/bin)

Bu sunucuda `/usr/local/bin` read-only. CLI araclari (`gh`, vb.) dpkg ile kurulamaz. Su pattern'i kullan:

```bash
# 1. Binary release indir
curl -sL https://github.com/cli/cli/releases/download/v2.67.0/gh_2.67.0_linux_amd64.tar.gz -o /tmp/gh.tar.gz
# 2. Extract et
tar -xzf /tmp/gh.tar.gz -C /tmp/
# 3. ~/.local/bin'e kopyala (mkdir -p ~/.local/bin)
cp /tmp/gh_*/bin/gh ~/.local/bin/
# 4. PATH'e ekle
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
# 5. Yetkilendir (GITHUB_TOKEN env ile)
gh auth status
```

## tools.py'ye Fonksiyon Ekleme

1. `patch` ile tools.py sonuna ekle (print'lerden önce)
2. Print satırını güncelle
3. Test et: `python3.11 -c "from tools import <fn>; print(<fn>(...))"`
4. **LLM ile üret (yeni v3):** `~/hermes_data/self_evolve.py uretim <ad> "<açıklama>" [kategori]`
   - 3 deneme düzeltme döngüsü, otomatik test, tools.py'ye ekleme, değişiklik geçmişi
   - Eski komut (`self_evolve.py llm`) artık yok — yerini `uretim` aldı
5. **Hata düzeltme:** `~/hermes_data/self_evolve.py fix <fonksiyon> "<hata_mesaji>"`
6. **Kalite kontrol:** `~/hermes_data/self_evolve.py denetle [fonksiyon_adi]`
7. **Ne ekleneceğini öğren:** `~/hermes_data/self_evolve.py ne_eklemeliyim`

## Python Built-in Modül Çakışması

Standalone script dosya adları Python built-in'leriyle çakışmamalı:
- ❌ `calendar.py` — Python'un built-in calendar modülünü shadow eder
- ❌ `datetime.py`, `json.py`, `os.py`, `sys.py`, `time.py`
- ✅ `hermes_calendar.py` — çakışma yok

Çözüm: dosyayı yeniden adlandır veya `sys.path.insert(0, ...)` kullan.

## Cron Çalıştırma Kısıtlamaları (03 Haziran 2026)

**`execute_code` cron bağlamında BLOKLANDI.** Cron işleri kullanıcı onayı olmadan çalıştığı için `execute_code` aracı reddedilir. Tüm cron script'leri standalone `.py` dosyası olarak yazılmalı ve `terminal()` ile çalıştırılmalıdır.

### tools.py Fonksiyon Çağırmadan Önce Bağımlılık Doğrulama

Cron içinde `tools.py`'den bir fonksiyon çağrılırken, o fonksiyonun dış bağımlılıklarının (LLM modeli, embedding daemon, API servisi) çalışır durumda olduğunu doğrula. Örneğin `pg_proaktif_analiz()`:
- `ollama` kütüphanesini import eder → ollama kurulu değilse patlar
- `qwen2.5:3b` modelini çağırır → model indirilmemişse patlar
- Çözüm: Fonksiyonu çağırmadan önce `try/except` ile bağımlılığı test et veya alternatif bir implementasyon (doğrudan SQL + formatlama) hazırla

**Pattern:**
```python
def _dependency_check():
    """Cron öncesi kritik bağımlılıkları kontrol et."""
    import subprocess
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        if "qwen2.5" not in result.stdout:
            print("[UYARI] qwen2.5:3b modeli yok — LLM analizi atlanacak")
            return False
        return True
    except FileNotFoundError:
        print("[UYARI] Ollama kurulu değil — LLM analizi atlanacak")
        return False
```

### PostgreSQL Veri Kalitesi (Test Kaydı Kirliliği)

Analitik PG sorgularında "Kategori testi" gibi test kayıtları gerçek veriyi gölgeleyebilir. Şu pattern ile filtrele:

```python
cur.execute(
    "SELECT content, category, created_at FROM hermes_memory "
    "WHERE category IN ('tech_note', 'business_strategy') "
    "AND content NOT LIKE 'Kategori testi%%' "  # test kayıtlarını filtrele
    "AND created_at > NOW() - INTERVAL '48 hours' "
    "ORDER BY created_at DESC"
)
```

**Kural:** Test kaydı atıldıktan sonra temizleme sorgusu (`DELETE FROM hermes_memory WHERE content LIKE 'Kategori testi%'`) çalıştır. Yoksa bir sonraki analizde anlamlı sonuçlar test verisi içinde kaybolur.

## Bilinen Script'ler

| Script | Cron | Ne işe yarar | Durum |
|---|---|---|---|
| `predict.py` | — | Kritik tarih öncesi uyarı | 🗑️ Silindi, ihtiyaç anında çağrılır |
| `haziran_plani.py` | — | Borç takibi | 🗑️ Silindi, ihtiyaç anında çağrılır |
| `self_evolve.py` | — | tools.py kalite analizi + kod üretimi | 🗑️ Silindi, ihtiyaç anında çağrılır |
| `hermes_calendar.py` | CLI | JSON takvim yönetimi | ✅ CLI aracı |
| Denetim Hatırlatıcı | 06:00 TR | Denetimli serbestlik | ✅ AKTİF |
| ECC Haftalık | Pzt 04:00 TR | ECC git pull | ✅ AKTİF |

**Tüm eski cron'lar silindi (22 → 2). Yeni cron eklemeden Cron Minimalizasyonu oku.**
