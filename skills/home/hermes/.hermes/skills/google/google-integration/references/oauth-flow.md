# Google OAuth Flow — Session Reference (2 Haz 2026)

## Setup
- credentials.json → ~/.google/credentials.json
- token.pickle → ~/.google/token.pickle
- Google Cloud Console Project: ergeneai-google
- Redirect URI: https://n8n.aiergene.xyz/webhook/google-oauth
- SCOPES: gmail.send, gmail.readonly, calendar, drive.file, spreadsheets

## Token Exchange
```python
import urllib.request, urllib.parse, json

data = urllib.parse.urlencode({
    "code": code,
    "client_id": client_id,
    "client_secret": client_secret,
    "redirect_uri": redirect_uri,
    "grant_type": "authorization_code"
}).encode()

req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data,
    headers={"Content-Type": "application/x-www-form-urlencoded"})
resp = urllib.request.urlopen(req)
result = json.loads(resp.read().decode())
```

## n8n Webhook
- n8n webhook `https://n8n.aiergene.xyz/webhook/google-oauth` auth kodu yakalar
- JSON body: `{"success": true, "code": "4/0Aeo..."}`
- Kod tek kullanımlık, hemen token'a çevir

## Save Token
```python
from google.oauth2.credentials import Credentials
import pickle

creds = Credentials(
    token=result["access_token"],
    refresh_token=result["refresh_token"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=client_id,
    client_secret=client_secret,
    scopes=result["scope"].split()
)
with open("~/.google/token.pickle", "wb") as f:
    pickle.dump(creds, f)
```

## Verify
```python
from googleapiclient.discovery import build

# Gmail
service = build("gmail", "v1", credentials=creds)
profile = service.users().getProfile(userId="me").execute()
# → emailAddress: ergenebilal@gmail.com

# Calendar
service = build("calendar", "v3", credentials=creds)
cal_list = service.calendarList().list().execute()
# → items: [{...}]
```
