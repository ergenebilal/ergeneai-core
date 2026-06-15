#!/usr/bin/env python3
"""
Google API entegrasyonu — Gmail, Calendar, Drive, Sheets
"""
import os
import pickle
import datetime
import threading
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from requests.exceptions import RequestException
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

CREDENTIALS_FILE = os.path.expanduser("~/.google/credentials.json")
TOKEN_FILE = os.path.expanduser("~/.google/token.pickle")

# Gerekli API scope'lar
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets",
]

# Token okuma/yazma icin thread-safe lock (race condition onleme)
_token_lock = threading.Lock()


def _auth():
    """Google API kimlik dogrulama — token varsa kullan, yoksa olustur."""
    creds = None

    with _token_lock:
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE, "rb") as f:
                    creds = pickle.load(f)
            except (pickle.UnpicklingError, EOFError, OSError) as e:
                creds = None
                import sys
                print(f"⚠️ Token dosyasi bozuk veya okunamadi, yeniden olusturulacak: {e}", file=sys.stderr)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except (RefreshError, RequestException) as e:
                # Refresh basarisiz — zorla yeniden auth
                import sys
                print(f"⚠️ Token refresh basarisiz, yeniden auth gerekiyor: {e}", file=sys.stderr)
                creds = None
        if not creds or not creds.valid:
            if not os.path.exists(CREDENTIALS_FILE):
                return None, "❌ Google credentials.json bulunamadi (~/.google/credentials.json)"
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES,
                redirect_uri="urn:ietf:wg:oauth:2.0:oob"
            )

            # Konsol tabanli auth akisi
            auth_url, _ = flow.authorization_url(
                access_type="offline", include_granted_scopes="true"
            )
            import sys
            print("\n═══════════════════════════════════════════", file=sys.stderr)
            print("  GOOGLE AUTH", file=sys.stderr)
            print("  Bu linki tarayicinda ac:", file=sys.stderr)
            print(f"  {auth_url}", file=sys.stderr)
            print("  Kodu alip buraya yapistir.", file=sys.stderr)
            print("═══════════════════════════════════════════\n", file=sys.stderr)

            kod = input("Kodu yapistir: ").strip()
            flow.fetch_token(code=kod)
            creds = flow.credentials

        with _token_lock:
            with open(TOKEN_FILE, "wb") as f:
                pickle.dump(creds, f)

    return creds, None


def gmail_gonder(alici, konu, icerik):
    """Gmail ile email gonderir."""
    try:
        creds, hata = _auth()
        if hata:
            return hata
        service = build("gmail", "v1", credentials=creds)

        import base64
        from email.mime.text import MIMEText

        mesaj = MIMEText(icerik, "html" if "<html" in icerik else "plain")
        mesaj["to"] = alici
        mesaj["subject"] = konu

        raw = base64.urlsafe_b64encode(mesaj.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return f"✅ E-posta gonderildi: {alici} -> {konu}"
    except Exception as e:
        return f"❌ Gmail hatasi: {str(e)}"


def gmail_oku(max_sonuc=5):
    """Gelen kutusundaki son epostalari okur."""
    try:
        creds, hata = _auth()
        if hata:
            return hata
        service = build("gmail", "v1", credentials=creds)

        sonuc = service.users().messages().list(userId="me", maxResults=max_sonuc).execute()
        mesajlar = sonuc.get("messages", [])
        liste = []
        for m in mesajlar:
            detay = service.users().messages().get(userId="me", id=m["id"]).execute()
            baslik = ""
            for h in detay.get("payload", {}).get("headers", []):
                if h["name"] == "Subject":
                    baslik = h["value"]
                    break
            liste.append({"id": m["id"], "baslik": baslik})
        return liste
    except Exception as e:
        return f"❌ Gmail okuma hatasi: {str(e)}"


def takvim_etkinlik_ekle(baslik, baslangic, bitis, aciklama=""):
    """Google Calendar'a etkinlik ekler."""
    try:
        creds, hata = _auth()
        if hata:
            return hata
        service = build("calendar", "v3", credentials=creds)

        etkinlik = {
            "summary": baslik,
            "description": aciklama,
            "start": {"dateTime": baslangic, "timeZone": "Europe/Istanbul"},
            "end": {"dateTime": bitis, "timeZone": "Europe/Istanbul"},
        }
        service.events().insert(calendarId="primary", body=etkinlik).execute()
        return f"✅ Takvim etkinligi eklendi: {baslik}"
    except Exception as e:
        return f"❌ Takvim hatasi: {str(e)}"


def takvim_etkinlik_listele(max_sonuc=10):
    """Onumuzdeki etkinlikleri listeler."""
    try:
        creds, hata = _auth()
        if hata:
            return hata
        service = build("calendar", "v3", credentials=creds)

        now = datetime.datetime.utcnow().isoformat() + "Z"
        sonuc = service.events().list(
            calendarId="primary", timeMin=now,
            maxResults=max_sonuc, singleEvents=True,
            orderBy="startTime"
        ).execute()
        return [
            {
                "baslik": e.get("summary", ""),
                "baslangic": e["start"].get("dateTime", e["start"].get("date")),
            }
            for e in sonuc.get("items", [])
        ]
    except Exception as e:
        return f"❌ Takvim listeleme hatasi: {str(e)}"


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "auth":
        creds, hata = _auth()
        print("✅ Google auth basarili!" if creds else hata)
    else:
        print("Kullanim: python3 google_api.py auth")
