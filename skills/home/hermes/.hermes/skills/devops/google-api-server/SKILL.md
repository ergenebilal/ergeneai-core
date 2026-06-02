---
name: google-api-server
version: 1.0.0
author: Hermes Agent
description: Headless server'da Google API (Gmail/Calendar/Drive/Sheets) entegrasyonu — OAuth2 credentials kurulumu, konsol tabanli auth akisi, token yonetimi
---

# Google API Server Integration

Headless (tarayicisiz) sunucuda Google API'leri ile calismak icin gereken auth altyapisi ve araclar.

## Kurulum

### 1. OAuth 2.0 Credentials

Google Cloud Console'dan `credentials.json` indir:

```bash
mkdir -p ~/.google
chmod 700 ~/.google
# credentials.json'i ~/.google/ dizinine koy
```

Format (installed app):
```json
{
  "installed": {
    "client_id": "...apps.googleusercontent.com",
    "project_id": "...",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_secret": "GOCSPX-...",
    "redirect_uris": ["http://localhost"]
  }
}
```

**Chmod 600** yap: `chmod 600 ~/.google/credentials.json`

### 2. Python Kutuphaneleri

```bash
pip3 install google-auth-oauthlib google-api-python-client google-auth-httplib2
```

### 3. Google Cloud Console'da Redirect URI Ekle

OAuth 2.0 Client ID'ye su URI'leri ekle:
- `http://localhost:8763` (server'da local web server ile auth)
- `urn:ietf:wg:oauth:2.0:oob` (ekran kodu yontemi, yedek — **C ALIŞMAYABILIR**, yeni OAuth client'larda Google reddediyor)
- `https://SENIN_DOMAININ.com/webhook/google-oauth` (public webhook, en guvenilir)

**Onerilen:** Client ID olustururken **Web application** sec, Desktop application secme. Web application ile explicit redirect URI eklemek daha guvenilir. Desktop application'un varsayilan `http://localhost` redirect'i cogu zaman yetmez.

## CRITICAL: `urn:ietf:wg:oauth:2.0:oob` ve IP Adresleri Calismayabilir

Google 2026'da yeni OAuth client'lar icin:
- **`urn:ietf:wg:oauth:2.0:oob`** — `Invalid Redirect: cannot contain whitespace` veya sessizce reddedilebilir
- **IP adresleri** (`http://1.2.3.4:8763`) — `Invalid Redirect: must end with a public top-level domain` hatasi verir
- **`localhost`** — sadece tarayici ile ayni makinedeysen calisir

Bu durumlarda **public domain uzerinden bir webhook** kullanmak tek cozumdur.

Guncellenmesi 1-5 dakika surebilir.

## Headless Auth Akisi

Sunucuda tarayici olmadigi icin iki yontem var:

### Yontem 1: Konsol Kodu (OOB)

```python
from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_secrets_file(
    "~/.google/credentials.json",
    SCOPES,
    redirect_uri="urn:ietf:wg:oauth:2.0:oob"
)

auth_url, _ = flow.authorization_url(
    access_type="offline", include_granted_scopes="true"
)
print(f"Linki tarayicinda ac: {auth_url}")
# Kullanici linki acar, izin verir, kodu kopyalar
kod = input("Kodu yapistir: ")
flow.fetch_token(code=kod)
creds = flow.credentials
```

### Yontem 3: Public Domain Webhook (En Guvenilir)

OOB ve localhost basarisiz oldugunda (Google yeni OAuth client'larda bunlari reddediyor). **Public domain'inizde bir webhook endpoint'i** kullanin.

**Sartlar:**
- Calisan bir webhook sunucunuz olsun (n8n, herhangi bir HTTP endpoint)
- Domain'iniz olsun (ornegin `n8n.aiergene.xyz`)
- Google Cloud Console'a `https://SENIN_DOMAININ.com/webhook/google-oauth` ekle

**n8n ile webhook olusturma (API calismiyorsa SQLite ile):**

n8n API'sine erisilemediginde dogrudan SQLite veritabanina workflow eklenebilir:

```bash
# 1. n8n Docker volume'unu bul
docker inspect n8n-container | grep -A5 Mounts

# 2. SQLite veritabanina baglan
DB="/var/lib/docker/volumes/...n8n-data/_data/database.sqlite"

# 3. Gerekli tablolar:
# - workflow_entity: id, name, active, nodes (JSON), connections (JSON), settings, versionId, activeVersionId
# - webhook_entity: workflowId, webhookPath, method, node, webhookId
# - shared_workflow: role, workflowId, projectId
# - workflow_history: versionId, workflowId, authors, nodes, connections, name
# - workflow_published_version: workflowId, publishedVersionId

# 4. Webhook node JSON ornegi:
# {"id": "webhook-id", "name": "Webhook", "type": "n8n-nodes-base.webhook",
#  "typeVersion": 1, "position": [200, 300],
#  "webhookId": "google-oauth",
#  "parameters": {"path": "google-oauth", "httpMethod": "GET",
#                 "responseMode": "lastNode", "options": {}}}

# 5. Kod node JSON ornegi:
# {"id": "code-id", "name": "Kodu Kaydet",
#  "type": "n8n-nodes-base.code", "typeVersion": 2,
#  "position": [500, 300],
#  "parameters": {"jsCode": "const items = $input.all();\n..."}}

# 6. En kritik: shared_workflow tablosuna kayit ekle
# INSERT INTO shared_workflow (role, workflowId, projectId, createdAt, updatedAt)
# VALUES ('workflow:owner', 'WORKFLOW_UUID', 'PROJECT_UUID', now, now);
```

**Onemli notlar:**
- `$input` shell'de bash degiskeni olarak yorumlanir — Python dosyasindan okuyarak gonder, inline komutta kullanma
- `fs` modulu n8n JavaScript runner'da YASAK — kod node'unda dosyaya yazamazsin, sadece return ile veri dondur
- Her workflow degisikliginden sonra n8n container'i restart et: `docker restart n8n-container`
- Webhook testi: `curl -s "https://domain.com/webhook/path?code=test123"`

Google redirect'i sunucuda calisan gecici bir web server'a yonlendirir:

```python
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = 8763  # 8080 dolu olabilir, alternatif port dene
REDIRECT_URI = f"http://localhost:{PORT}"
auth_code = None

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        qs = parse_qs(urlparse(self.path).query)
        if "code" in qs:
            auth_code = qs["code"][0]
            self.send_response(200)
            self.end_headers()
        self.log_message = lambda *a: None

server = HTTPServer(('localhost', PORT), Handler)
flow = InstalledAppFlow.from_client_secrets_file(
    "~/.google/credentials.json", SCOPES, redirect_uri=REDIRECT_URI
)
auth_url, _ = flow.authorization_url(access_type="offline")
print(f"Linki ac: {auth_url}")

server.timeout = 120
while auth_code is None:
    server.handle_request()

flow.fetch_token(code=auth_code)
creds = flow.credentials
```

### Token'i Kaydet

```python
import pickle
with open(os.path.expanduser("~/.google/token.pickle"), "wb") as f:
    pickle.dump(creds, f)
```

Sonraki calistirmalarda `_auth()` dogrudan token.pickle'i kullanir, refresh token varsa otomatik yeniler.

## API Kullanim Ornekleri

### Gmail Gonderme

```python
import base64
from email.mime.text import MIMEText

service = build("gmail", "v1", credentials=creds)
mesaj = MIMEText(icerik)
mesaj["to"] = alici
mesaj["subject"] = konu
raw = base64.urlsafe_b64encode(mesaj.as_bytes()).decode()
service.users().messages().send(userId="me", body={"raw": raw}).execute()
```

### Google Calendar Etkinlik Ekle

```python
service = build("calendar", "v3", credentials=creds)
etkinlik = {
    "summary": baslik,
    "description": aciklama,
    "start": {"dateTime": baslangic, "timeZone": "Europe/Istanbul"},
    "end": {"dateTime": bitis, "timeZone": "Europe/Istanbul"},
}
service.events().insert(calendarId="primary", body=etkinlik).execute()
```

## Scope'lar

```python
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets",
]
```

## Pitfall'lar

- **Port cakismasi**: `8080` cogu sunucuda dolu. Once kontrol et: `ss -tlnp | grep 8080`. `8763` guvenli alternatif.
- **Web application vs Desktop**: Desktop application tipi client'larin varsayilan redirect URI'lari (`http://localhost`) konsol auth icin yetersiz kalir. Web application tipi kullanip `http://localhost:PORT` eklemek daha guvenilir.
- **redirect_uri_mismatch**: Bu hatanin tek cozumu Cloud Console'da Authorized redirect URIs'e dogru URI'yi eklemektir. Yerel dosyayi degistirmek cozmez. Cloud Console'da guncelle, 1-5dk bekle.
- **input() cron'da calismaz**: Konsol kodu akisi sadece interaktif terminalde calisir. Cron icin local web server yontemini kullan.
- **Token.pickle**: `~/.google/token.pickle`'da saklanir. Silinirse yeniden auth gerekir.
- **Refresh token**: `access_type="offline"` ile refresh token alinir. Refresh token kaybolursa (`token.pickle` silinir) kullanici yeniden auth yapmali.
- **Veritabanı/auth dosyasını kullanmadan önce doğrula** — Önceki oturumda `~/.hermes/google_credentials.json` yazıldığı belirtilmişti ama diskte yoktu. **Kural:** `read_file` veya `ls -la` ile dosyanın varlığını kontrol etmeden kullanma. "Yazıldı" ifadesine oturum özetinden kalmış olsa bile güvenme.
- **n8n API credential verisini göstermez** — `/api/v1/credentials` credential listesini (ID, name, type) döndürür ama secrets'lar (client_id, secret, token) şifrelidir, API'den okunamaz. Var olan bir Gmail OAuth credential'ından client_id/secret almak mümkün değildir. Kullanıcıdan Cloud Console'dan almasını iste.
