---
name: google-integration
version: 1.0.0
description: Google OAuth setup, Gmail/Calendar/Drive/Sheets API integration for Hermes
trigger: user asks about Gmail, Calendar, Drive, Sheets, Google auth, sending email, or calendar events
---

# Google Services Integration

Set up and use Google APIs (Gmail, Calendar, Drive, Sheets) from Hermes/tools.py.

## Prerequisites (One-Time)
1. Google Cloud Console'da OAuth 2.0 Client ID oluştur (Web application type)
2. Redirect URI ekle: `https://n8n.aiergene.xyz/webhook/google-oauth`
3. `credentials.json`'ı `~/.google/credentials.json`'a kaydet
4. Google Python kütüphanelerini yükle: `pip install google-api-python-client google-auth-oauthlib google-auth-httplib2`

## OAuth Flow (Her 6 ayda bir)
1. `google_auth_link()` ile auth URL'i üret → kullanıcıya gönder
2. Kullanıcı tıklar, Google webhook'a yönlendirir → kodu yakala
3. Kodu token'a çevir: POST oauth2.googleapis.com/token
4. `token.pickle`'a kaydet: `~/.google/token.pickle`
5. Test: `gmail_oku(3)` veya `takvim_etkinlik_listele(3)` ile doğrula
6. Kullanıcıya bildir: ✅ Hangi servislerin çalıştığı

## Functions (tools.py'de)
```
google_auth()            → creds, hata
google_auth_link()       → yeni auth URL'i
gmail_gonder(alici, konu, icerik, html=False)
gmail_oku(max_sonuc=5)
takvim_etkinlik_ekle(baslik, baslangic, bitis, aciklama="")
takvim_etkinlik_listele(max_sonuc=10)
drive_dosya_listele(klasor_id="root", max_sonuc=10)
drive_dosya_yukle(dosya_yolu, hedef_klasor="root")
sheets_oku(sheet_id, sayfa="Sheet1", huc_bolge="A1:Z100")
sheets_yaz(sheet_id, sayfa="Sheet1", huc_bolge="A1", veriler=None)
sheets_ekle(sheet_id, sayfa="Sheet1", veriler=None)
```

## Pitfalls
- **Client secret hatalıysa** `invalid_client` hatası alırsın. `~/.google/credentials.json`'daki secret'ı kullan, ezberleme.
- **Auth kodu tek kullanımlık** — hata alırsan yeni link üret.
- **Refresh token 6 ayda expire olur** — prompt=consent ile yeni auth gerek.
- **SMTP bloklu sunucularda** Gmail API kullan (direkt HTTP, port gerekmez).
- **python3.11** kullan — Google kütüphaneleri 3.11'de kurulu.
- **Token.pickle**'ı GitHub'a pushlama — credentials içerir.

## Priority
En kritik: Gmail (e-posta gönderme). Calendar (randevu/takvim). Drive/Sheets daha düşük öncelik.