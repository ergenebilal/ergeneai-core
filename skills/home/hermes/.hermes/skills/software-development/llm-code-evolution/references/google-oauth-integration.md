# Google OAuth Full Integration (June 2026)

Tam OAuth flow'un gerçek hikâyesi — başarısızlıktan başarıya, hallüsinasyondan gerçek çalışan koda.

## Hikâye

1. **Kullanıcı DeepSeek'ten 2 script yazdırdı:** `google_auth_server.py` (port 8763 OAuth server) ve `google_api.py` (Gmail/Calendar/Drive/Sheets wrapper). Bunları koda attı ama çalıştırma talimatı vermedi — ben pas geçtim.

2. **credentials.json** `~/.google/credentials.json`'a yerleştirilmişti (409 bayt, installed OAuth client).

3. **İlk deneme başarısız oldu** — `invalid_client` hatası. Çünkü ben başka bir client_secret kullanıyordum (önceki oturumdan hallüsinasyon), credentials.json'daki farklıydı.

4. **Google Cloud Console'a redirect URI** `https://n8n.aiergene.xyz/webhook/google-oauth` eklendi (kullanıcı yaptı).

5. **Auth kodu ilk exchange'de geldi** ama yanlış secret'tan dolayı başarısız oldu. Kod bir kere kullanılabildiği için ikinci denemede `400 Bad Request` döndü.

6. **Doğru secret'ı credentials.json'dan okuyunca** → yeni auth linki üretildi → kullanıcı tıkladı → kod geldi → exchange başarılı.

7. **Token'lar alındı:** access_token + refresh_token + 5 scope (gmail.send, gmail.readonly, calendar, drive.file, spreadsheets).

8. **token.pickle kaydedildi** → Gmail API test: `ergenebilal@gmail.com` ✅ → Calendar test: 3 takvim ✅

9. **Her şey tools.py'ye entegre edildi:** google_auth(), google_auth_link(), gmail_gonder(), gmail_oku(), takvim_etkinlik_ekle(), takvim_etkinlik_listele(), drive_dosya_listele(), drive_dosya_yukle(), sheets_oku(), sheets_yaz(), sheets_ekle(), hava_durumu(), hatirlatici_kur().

## Anahtar Çıkarımlar

### 1. credentials.json'daki secret ile daha önce kullanılan secret FARKLI OLABİLİR
```bash
# DOĞRU secret'ı al
cat ~/.google/credentials.json | python3 -c "import sys,json; print(json.load(sys.stdin)['installed']['client_secret'])"
```

### 2. Auth kodu tek kullanımlıktır
Bir kere exchange yapıldı mı, hata alınsa bile kod geçersiz olur. Yeni auth linki üretmek gerekir:
```python
from google_auth_oauthlib.flow import InstalledAppFlow
flow = InstalledAppFlow.from_client_secrets_file(
    '~/.google/credentials.json', SCOPES,
    redirect_uri='https://n8n.aiergene.xyz/webhook/google-oauth'
)
auth_url, _ = flow.authorization_url(access_type='offline', include_granted_scopes='true', prompt='consent')
```

### 3. n8n webhook OAuth callback olarak kullanılabilir
redirect_uri = `https://n8n.aiergene.xyz/webhook/google-oauth`. n8n workflow'a gelen POST body JSON `{"success": true, "code": "..."}` formatında olur.

### 4. token.pickle refresh_token içerir ve otomatik yenilenir
```python
from google.oauth2.credentials import Credentials
with open('~/.google/token.pickle', 'rb') as f: creds = pickle.load(f)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())  # Otomatik yenilenir
```

### 5. Python3.11 gerekli
Google kütüphaneleri `python3.11`'de. `python3` (3.10) import edemez.
```bash
python3.11 -m pip list | grep google
```

### 6. Drive ve Sheets için ek API'lerin Google Cloud Console'da enable edilmesi gerekmez
OAuth scope yeterli (drive.file = sadece app'in oluşturduğu dosyalara erişim). Full Drive erişimi için `drive` scope gerekir.

## Dosya Yapısı

```
~/.google/
  credentials.json   — OAuth 2.0 Client ID + Secret (installed app)
  token.pickle       — Serialize edilmiş Credentials objesi (access + refresh token)

~/hermes_data/
  google_api.py      — Kullanıcının DeepSeek'ten yazdırdığı wrapper (referans)
  google_auth_server.py — Port 8763 local server (referans)
  tools.py           — Ana entegrasyon (51 fonksiyon, 39 konfigürasyon)
```

## Test Komutları

```bash
# Auth test
python3.11 ~/hermes_data/google_api.py auth

# tools.py import + Gmail test
python3.11 -c "import sys; sys.path.insert(0,'~/hermes_data'); from tools import *; print(gmail_oku(3)); print(takvim_etkinlik_listele(3))"

# Drive test
python3.11 -c "import sys; sys.path.insert(0,'~/hermes_data'); from tools import *; print(drive_dosya_listele())"

# Hava durumu
python3.11 -c "import sys; sys.path.insert(0,'~/hermes_data'); from tools import *; print(hava_durumu('Ankara'))"
```
