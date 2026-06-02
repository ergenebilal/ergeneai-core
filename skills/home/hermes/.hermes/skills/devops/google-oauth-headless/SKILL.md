---
name: google-oauth-headless
description: "Google OAuth2 authentication and API setup on headless servers — Gmail, Calendar, Drive, Sheets. Desktop credential file + console-based auth flow (tarayıcısız sunucuda)."
---

# Google OAuth2 — Headless Server Integration

## When to Use

When setting up Google API access (Gmail, Calendar, Drive, Sheets) on a server that has **no browser**. The standard `run_local_server()` flow hangs because there's no local browser to redirect to. This skill covers the **console-based auth flow** and the boilerplate you need every time.

## Setup

### 1. Get OAuth2 Client Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project or select existing
3. Enable the APIs you need: Gmail API, Google Calendar API, Google Drive API, Google Sheets API
4. Go to **APIs & Services → Credentials**
5. Create → **OAuth client ID** → **Desktop application**
6. Download the JSON → save as `~/.google/credentials.json`

### 2. Save Credentials

```bash
mkdir -p ~/.google
# paste credentials.json content or upload
chmod 600 ~/.google/credentials.json
```

### 3. Install Python Libraries

```bash
pip3 install google-auth-oauthlib google-api-python-client google-auth-httplib2
```

## The Auth Flow (Headless)

The standard `InstalledAppFlow.run_local_server()` starts a local HTTP server and opens the browser — fails on a headless server.

**Use this instead:**

```python
from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_secrets_file(
    "~/.google/credentials.json", SCOPES
)

# Step 1: Get the auth URL
auth_url, _ = flow.authorization_url(
    access_type="offline", include_granted_scopes="true"
)
print(f"Visit this URL: {auth_url}")  # User opens on their own machine

# Step 2: User visits URL, authorizes, gets a code
code = input("Paste the authorization code: ").strip()

# Step 3: Exchange code for credentials
flow.fetch_token(code=code)
creds = flow.credentials
```

### Scopes to Use

```python
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets",
]
```

### Token Persistence

```python
import pickle

TOKEN_FILE = os.path.expanduser("~/.google/token.pickle")

if os.path.exists(TOKEN_FILE):
    with open(TOKEN_FILE, "rb") as f:
        creds = pickle.load(f)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        # ... auth flow above ...
    with open(TOKEN_FILE, "wb") as f:
        pickle.dump(creds, f)
```

The token file stores the refresh token, so you only need to go through the console auth **once**.

## API Service Builders

```python
from googleapiclient.discovery import build

gmail = build("gmail", "v1", credentials=creds)
calendar = build("calendar", "v3", credentials=creds)
drive = build("drive", "v3", credentials=creds)
sheets = build("sheets", "v4", credentials=creds)
```

## Key Operations

### Send Email
```python
import base64
from email.mime.text import MIMEText

msg = MIMEText("content", "html" if "<html" in content else "plain")
msg["to"] = recipient
msg["subject"] = subject
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
gmail.users().messages().send(userId="me", body={"raw": raw}).execute()
```

### Read Inbox
```python
results = gmail.users().messages().list(userId="me", maxResults=5).execute()
for m in results.get("messages", []):
    detail = gmail.users().messages().get(userId="me", id=m["id"]).execute()
    # Extract subject from headers
```

### Add Calendar Event
```python
event = {
    "summary": "Title",
    "description": "Details",
    "start": {"dateTime": "2026-06-11T10:00:00", "timeZone": "Europe/Istanbul"},
    "end": {"dateTime": "2026-06-11T11:00:00", "timeZone": "Europe/Istanbul"},
}
calendar.events().insert(calendarId="primary", body=event).execute()
```

### List Upcoming Events
```python
now = datetime.datetime.utcnow().isoformat() + "Z"
results = calendar.events().list(
    calendarId="primary", timeMin=now,
    maxResults=10, singleEvents=True, orderBy="startTime"
).execute()
```

## Alternative: Webhook Redirect Pattern (Smoother)

Instead of the console-based flow where the user must copy-paste a code, use a **public webhook URL** as the OAuth redirect URI. The user just clicks a link, authorizes, and Google redirects to your webhook — you get the code server-side automatically.

### Setup

**1. Create an n8n webhook** (GET, path like `google-oauth`) that returns `{"success": true, "code": "{{$json.query.code}}"}`. The response body carries the code for your agent to read.

**2. In Google Cloud Console**, use **"Web application"** client type (not Desktop). Add `https://your-domain.com/webhook/google-oauth` to **Authorized redirect URIs**.

**3. Generate auth URL** with webhook redirect:
```python
flow = InstalledAppFlow.from_client_secrets_file(
    "~/.google/credentials.json", SCOPES,
    redirect_uri="https://your-domain.com/webhook/google-oauth"
)
auth_url, _ = flow.authorization_url(
    access_type='offline', include_granted_scopes='true', prompt='consent'
)
```

**4. Send link to user** → they click → Google redirects to webhook with `?code=...`

**5. Exchange code for token** (agent does this when webhook fires):
```python
data = urllib.parse.urlencode({"code": code, "client_id": "...",
    "client_secret": "...", "redirect_uri": "...", "grant_type": "authorization_code"}).encode()
req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
result = json.loads(urllib.request.urlopen(req).read().decode())
```

**6. Save token.pickle** with `google.oauth2.credentials.Credentials` + `pickle.dump()`.

### Console vs Webhook

| Console Flow | Webhook Redirect |
|---|---|
| User pastes code back | User clicks link — done |
| Two interactions | One click |
| Desktop client type works | Requires Web application type |
| Code visible to user | Handled server-side |

## Hermes tools.py Integration

Add these functions to `/home/hermes/hermes_data/tools.py` (53 functions, 0.88 quality):

### Email & Calendar
- `google_auth()` — returns (creds, None) or (None, error), auto-refreshes expired tokens
- `google_auth_link()` — generates new auth URL for re-auth
- `gmail_gonder(alici, konu, icerik, html=False)` — send email
- `gmail_oku(max_sonuc=5)` — read inbox subjects
- `takvim_etkinlik_ekle(baslik, baslangic, bitis, aciklama="")` — add calendar event
- `takvim_etkinlik_listele(max_sonuc=10)` — list upcoming events

### Drive
- `drive_dosya_listele(klasor_id="root", max_sonuc=10)` — list files
- `drive_dosya_yukle(dosya_yolu, hedef_klasor="root")` — upload file

### Sheets
- `sheets_oku(sheet_id, sayfa="Sheet1", huc_bolge="A1:Z100")` — read data
- `sheets_yaz(sheet_id, sayfa="Sheet1", huc_bolge="A1", veriler=None)` — write data
- `sheets_ekle(sheet_id, sayfa="Sheet1", veriler=None)` — append rows

Test: `python3.11 -c "import sys; sys.path.insert(0,'/home/hermes/hermes_data'); from tools import *; print(gmail_oku(3)); print(takvim_etkinlik_listele(3)); print(drive_dosya_listele()); print(hava_durumu('Bursa'))"`

## CRITICAL: OAuth Kullanmadan Önce credentials.json'ı Doğrula

Bu session'da kritik bir hata yakalandı: önceki oturumda "credentials.json yazıldı" denmesine rağmen diskte dosya yoktu. **Oturum özetine/hafızaya güvenme, her kullanım öncesi read_file/stat ile doğrula.**

```python
# KULLANMADAN ÖNCE:
import os
if not os.path.exists(os.path.expanduser("~/.google/credentials.json")):
    # Dosya yok — kullanıcıdan Cloud Console'dan almasını iste
    # client_id/client_secret'ı da credentials.json'dan oku
    # n8n API credential verisini göstermez (şifreli)
```

**Aynı şey token.pickle için de geçerli** — var mı yok mu kontrol etmeden `open(...)` yapma. google_auth() içinde bu kontrol var ama onu çağırmadan önce credentials.json varlığını kontrol et.

## Pitfalls (genişletilmiş)

Eklenen maddeler (önceki session'da yaşanan gerçek hatalar):

- **`run_local_server()` hangs on headless** — Don't use it. `console` flow (`input()` + `flow.fetch_token(code=...)`) is the correct pattern.
- **`run_console()` does NOT exist** — This method was removed from google-auth-oauthlib. Don't use it.
- **`urn:ietf:wg:oauth:2.0:oob` may be REJECTED by Google** — New OAuth clients in 2026 reject OOB redirect URIs with `invalid_request` or `redirect_uri_mismatch`. Fall back to a public domain webhook.
- **IP addresses also rejected** — Google requires a public top-level domain (`.com`, `.xyz`, etc.). `http://1.2.3.4:PORT` returns "must end with a public top-level domain".
- **Solution for both failures**: Use a public domain webhook as the OAuth redirect URI (e.g., `https://your-domain.com/webhook/google-oauth`). See the Turkish `google-api-server` skill for n8n SQLite injection details.
- **First auth is interactive** — Someone must visit the URL on a machine with a browser, copy the code, and paste it. Once the `token.pickle` is saved with the refresh token, subsequent runs are automatic.
- **Refresh tokens expire if unused for 6 months** — Run at least one API call every few months to keep the token alive.
- **timezone for Calendar** — Always pass `timeZone: "Europe/Istanbul"` (or the appropriate zone). Google defaults to UTC otherwise.
- **Credentials file is JSON** — The downloaded `client_secret_*.json` can be renamed to `credentials.json`. Keep the `installed` key structure intact.
- **Gmail send with HTML** — Set MIME type to `"html"` if content contains HTML tags, otherwise `"plain"`.
- **Gmail API quota** — 100 sends/day per user by default. Can request more in Cloud Console.
- **CRITICAL: `~/.google/credentials.json` varlığını her kullanım öncesi doğrula** — Önceki oturumda "write_file ile yazıldı" dense bile diskte olmayabilir. `google_auth()` veya `gmail_gonder()` çağırmadan ÖNCE `read_file('~/.google/credentials.json')` ile varlığını kontrol et. Session özetine güvenme.
- **n8n API credential verisini göstermez** — Secrets şifreli. Var olan bir Gmail OAuth credential'ından client_id/secret alamazsın. Kullanıcıya "Cloud Console'dan al" de.
- **Webhook code exchange için full token gerekir** — `access_token` ve `refresh_token` terminal çıktısında truncated görünebilir. Token'ları exchange ettikten sonra hemen `token.pickle`'a kaydet, çıktıya güvenme.
- **DOĞRU client_secret kullan** — credentials.json'daki secret farklı olabilir. Önce dosyayı oku, içindeki secret'ı kullan. Daha önce "biliyorum" sandığın secret yanlış çıkabilir.
- **Auth kodu tek kullanımlıktır** — Exchange başarısız olursa yeni auth URL'i üretmen gerekir.

## Related Files

- Server implementation: `/home/hermes/hermes_data/google_api.py`
- Auth test: `python3.11 -c "import sys; sys.path.append('/home/hermes/hermes_data'); from google_api import _auth; _auth()"`
