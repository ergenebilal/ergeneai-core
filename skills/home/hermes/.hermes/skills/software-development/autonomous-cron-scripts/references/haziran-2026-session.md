# Haziran 2026 — Session Reference

## Oluşturulan Script'ler

### predict.py
- **Amaç:** Kritik tarihlere 3 gün kala ChromaDB'de ilgili belge var mı kontrol et
- **Kritik konular:** Denizbank (11 Haz), Sigorta (14 Haz), KMH (15 Haz)
- **Kullandığı tools.py:** `bilal_notes_ara`, `telegram_mesaj_gonder`
- **Cron:** Her gün 11:20 TR
- **Özel durum:** `if name` bug'ı düzeltildi → `if __name__`

### haziran_plani.py
- **Amaç:** Ödeme tarihlerine 0-5 gün kala günlük finans hesaplaması + Telegram bildirimi
- **Kullandığı tools.py:** `telegram_mesaj_gonder`, `hesap_hesapla`, `analiz_et`, `log_hata`
- **Plan:** Denizbank 5.000₺ (11 Haz), Sigorta 3.500₺ (14 Haz), KMH 2.000₺ (15 Haz)
- **Cron:** 10:30 TR (crontab'a eklendi)
- **Özel durum:** `if name` bug'ı düzeltildi → `if __name__`
- **Durum:** Aktif ✅

### calendar.py
- **Amaç:** JSON tabanlı takvim yönetimi (ekle, bugün, sonraki, tamamla)
- **Kullandığı tools.py:** Yok (bağımsız)
- **Cron:** Henüz eklenmedi
- **Özel durum:** `calendar.py` adı Python built-in `calendar` modülü ile çakışır. `from calendar import takvim_ekle` çalışmaz çünkü Python /usr/lib/python3.11/calendar.py'yi bulur. Çözüm: `sys.path.insert(0, '~/hermes_data')` ile import et veya dosyayı `hermes_calendar.py` olarak yeniden adlandır.

### self_evolve.py
- **Amaç:** tools.py'ye LLM ile fonksiyon üretme
- **API Key:** `~/.hermes/.env` dosyasından okur (Hermes ortamı dışında çalıştığı için)
- **İki mod:** `template` (basit şablon) ve `llm` (DeepSeek API ile gerçek kod)
- **Detaylı referans:** `../llm-code-evolution/SKILL.md`

## tools.py'ye Eklenen Fonksiyonlar

### analiz_et(mesaj)
- Kelime bazlı duygu analizi
- Dönüş: `{"durum": "MUTLU|YORGUN|NOTR", "skor": -1..1, "tetikleyenler": []}`
- Olumlu kelimeler: teşekkür, harika, süper, iyi, başarılı, aferin, mükemmel (her biri +0.3)
- Olumsuz kelimeler: kötü, hata, yanlış, sinir, yorgun, bıktım, yeter, uğraşma (her biri -0.4)
- Skor > 0.2 → MUTLU, < -0.2 → YORGUN/SINIRLI, else → NÖTR

### hesap_hesapla(tur, miktar, gun_kaldi)
- `tur="gider"`: günlük ayırma miktarı (`"Günde ~818.18 TL ayır"`)
- `tur="gelir"`: günlük birikme miktarı (`"Günde ~666.67 TL birikecek"`)
- Dönüş: string (insan okunabilir)
- Test: `hesap_hesapla('gider', 9000, 11)` ✅

## Yeni Script: haziran_plani.py

Haziran ödeme takvimi script'i. Detay: main SKILL.md'deki "Bilinen Script'ler" tablosu.

## Karşılaşılan Hatalar ve Çözümleri

1. **Türkçe karakter değişken adları** (`satır` vs `satir`): Python'da farklı Unicode karakterler. Çözüm: İngilizce değişken adları kullan.
2. **`if name == "main"`**: 3 kez tekrarlandı. Çözüm: `if __name__ == "__main__":` kullan, her yeni script'te kontrol et.
3. **DeepSeek API key bulunamadı**: Standalone script Hermes ortamında koşmaz. Çözüm: `~/.hermes/.env` dosyasını oku.
4. **Cron path hatası**: Kullanıcı `/home/hermes_data/` yazıyor, doğrusu `/home/hermes/hermes_data/`. Çözüm: her cron eklemesinde path'i kontrol et.
5. **`python3` chromadb import edemez**: 3.10'da chromadb yok. Çözüm: tüm cron'larda `python3.11` kullan.
6. **tools.py'de duplicate print satırı**: Patch ile silindi.
7. **DeepSeek API 402 (exhausted)**: Log'larda görüldü, credential pool rotation var. API key'in geçerli olduğunu doğrula.
