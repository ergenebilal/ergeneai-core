# Google OAuth — 02 Haziran 2026 Gerçek Hikâye

Bu session'da Google OAuth baştan sona canlı olarak yapıldı. Yaşanan sorunlar ve çözümleri:

## 1. credentials.json Keşfi

Kullanıcı DeepSeek'ten `google_auth_server.py` ve `google_api.py` yazdırmış ve `~/.google/credentials.json`'ı yerleştirmişti. Ama önceki oturum özetinde "hallüsinasyon" olarak kaydedilmişti — dosya aslında vardı (`ls -la ~/.google/` ile bulundu).

**Ders:** Önce `ls`/`read_file` ile kontrol et. "Yok" denmesine güvenme.

## 2. Yanlış client_secret

İlk denemede farklı bir client_secret kullanıldı (GOCSPX-9TR...). credentials.json'daki gerçek secret GOCSPX-Y41...'dı. Sonuç: `invalid_client`.

**Ders:** client_secret'ı tahmin etme, credentials.json'dan oku.

## 3. Auth Kodu Tek Kullanımlık

İlk exchange doğru secret'la başarılı oldu ama terminal çıktısında token'lar truncated göründü. Token'ı pickle'a kaydetmek için kodu yeniden kullanmak gerektiğinde `400 Bad Request` (code already used).

**Ders:** Auth kodu tek kullanımlık. Exchange başarılı olur olmaz token'ı hemen pickle'a kaydet. Çıktıya güvenme.

## 4. python3.11 ile Çalıştırma

Google kütüphaneleri python3.11'e kuruluydu. python3 (3.10) `google.oauth2` import edemiyor.

**Ders:** Tüm Google işlemleri için python3.11 kullan.

## 5. Başarılı Token Yönetimi

```python
creds = Credentials(
    token=result["access_token"],
    refresh_token=result["refresh_token"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=..., client_secret=...,
    scopes=[...]
)
pickle.dump(creds, open("~/.google/token.pickle", "wb"))
```

Sonra:
- Gmail: `users().getProfile()` → ✅ ergenebilal@gmail.com
- Calendar: `calendarList().list()` → ✅ 3 takvim
- Drive: `files().list()` → ✅ boş (yeni hesap)
- Sheets: `values().get()` → ✅ 404 (beklenen, test sheet yok)
- Hava durumu: `wttr.in/Bursa` → ✅ Açık +16°C

## 6. tools.py Entegrasyonu

6 fonksiyon eklendi: `google_auth`, `google_auth_link`, `gmail_gonder`, `gmail_oku`, `takvim_etkinlik_ekle`, `takvim_etkinlik_listele`. Sonra genişletildi: `drive_dosya_listele`, `drive_dosya_yukle`, `sheets_oku`, `sheets_yaz`, `sheets_ekle`, `hava_durumu`, `hatirlatici_kur`, `beyin_ara`, `beyin_kaydet`.

tools.py: 44 → 53 fonksiyon. Kalite: 0.39 → 0.88.
