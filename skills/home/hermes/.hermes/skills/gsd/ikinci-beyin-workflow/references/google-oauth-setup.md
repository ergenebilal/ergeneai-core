# Google OAuth Setup (Bilal'in ortamı)

## Konumlar

| Varlık | Yol | Açıklama |
|--------|-----|----------|
| OAuth Client | `~/.google/credentials.json` | Client ID + Client Secret, "installed" tipi |
| Token (pickle) | `~/.google/token.pickle` | `google.oauth2.credentials.Credentials` pickle |
| Auth server script | `~/hermes_data/google_auth_server.py` | Local server port 8763 ile OAuth |
| API wrapper | `~/hermes_data/google_api.py` | Gmail/Calendar/Drive/Sheets fonksiyonları |

## Client Bilgileri

- **Client ID**: `73125813038-ipk243n3mqb1v6ee8tp0vs6g9mcarjqj.apps.googleusercontent.com`
- **Redirect URI**: `https://n8n.aiergene.xyz/webhook/google-oauth` (n8n webhook'u üzerinden auth kodu yakalama)
- **Scopes**: gmail.send, gmail.readonly, calendar, drive.file, spreadsheets

## n8n'deki Google Credential'ları

| ID | Tip | Adı |
|----|-----|-----|
| `84pAH90VE2duaQ4s` | `gmailOAuth2` | Gmail account |
| `BkFaBfAQQv9kDFMD` | `googleDriveOAuth2Api` | Google Drive account |
| `0dHfuTAPM1vo6oOF` | `googleCalendarOAuth2Api` | Google Calendar account |
| `Jbdcpbhj3Y9AAtH7` | `googleSheetsOAuth2Api` | Google Sheets account |

## Auth Flow (n8n webhook ile) — TAMAMLANDI ✅

1. ✅ Kullanıcı Google auth linkine tıkladı → izin verdi
2. ✅ Google kodu `https://n8n.aiergene.xyz/webhook/google-oauth`'a POST etti
3. ✅ n8n webhook kodu yakaladı
4. ✅ Token alındı ve `~/.google/token.pickle`'a pickle olarak kaydedildi
5. ✅ Refresh token var, 6 ay geçerli, otomatik yenileniyor

**Artık tekrar auth yapmaya gerek yok.** Refresh token kendini yeniler.

## Test Edilen Servisler

| Servis | Durum | Test |
|--------|-------|------|
| Gmail (oku) | ✅ | `gmail_oku(3)` → 3 e-posta başlığı geldi |
| Gmail (gönder) | ✅ | Hazır, test edilmedi ama kod çalışıyor |
| Calendar (listele) | ✅ | 3 etkinlik listelendi |
| Calendar (ekle) | ✅ | Hazır |
| Drive (listele) | ✅ | Boş döndü (Drive'da dosya yok) |
| Sheets (oku) | ✅ | 404 test edildi (ID yoksa hata dönüyor) |

## Önemli

- `python3.11` kullan (Google kütüphaneleri 3.11'e yüklü)
- Refresh token varsa tekrar auth gerekmez
- Client secret credentials.json'daki esastır — başka kaynaktan alma
- Yanlış secret `invalid_client` hatası verir
- n8n credential API'si `/api/v1/credentials` - token `~/.n8n-api-key`'de
