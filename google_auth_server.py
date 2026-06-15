#!/usr/bin/env python3
"""Google Auth via local web server"""
import os, sys, json, socket, signal
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/spreadsheets',
]

PORT = 8763
REDIRECT_URI = f"http://localhost:{PORT}"
TOKEN_FILE = os.path.expanduser("~/.google/token.pickle")

auth_code = None
server = None

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        try:
            qs = parse_qs(urlparse(self.path).query)
            if "code" in qs:
                auth_code = qs["code"][0]
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write("<h3>Auth alindi! Bu sekmeyi kapatabilirsin.</h3>".encode())
            else:
                self.send_response(400)
                self.end_headers()
                try:
                    self.wfile.write(b"Code not found")
                except OSError:
                    pass
        except Exception as e:
            try:
                self.send_response(500)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(f"Internal error: {e}".encode())
            except OSError:
                pass
        return

    def log_message(self, *a):
        pass  # sus

def _sigterm_handler(signum, frame):
    """SIGTERM handler — temiz kapanis."""
    print("\n⚠️ SIGTERM alindi, kapaniliyor...", file=sys.stderr)
    server.server_close()
    sys.exit(0)

def _sigint_handler(signum, frame):
    """SIGINT (Ctrl+C) handler — temiz kapanis."""
    print("\n⚠️ Kullanici tarafindan durduruldu.", file=sys.stderr)
    server.server_close()
    sys.exit(0)

# Sinyal handler'lari
signal.signal(signal.SIGTERM, _sigterm_handler)
signal.signal(signal.SIGINT, _sigint_handler)

# Port musait mi kontrol
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', PORT))
    sock.close()

    if result == 0:
        print(f"❌ Port {PORT} kullanimda. server.py'yi durdur veya farkli port dene.")
        sys.exit(1)
except OSError as e:
    print(f"❌ Port kontrol hatasi: {e}")
    sys.exit(1)

# Server baslat
try:
    server = HTTPServer(('localhost', PORT), Handler)
except OSError as e:
    print(f"❌ Server baslatilamadi (port {PORT}): {e}")
    sys.exit(1)

try:
    flow = InstalledAppFlow.from_client_secrets_file(
        os.path.expanduser("~/.google/credentials.json"),
        SCOPES,
        redirect_uri=REDIRECT_URI
    )
except Exception as e:
    print(f"❌ OAuth flow olusturulamadi: {e}")
    sys.exit(1)

auth_url, _ = flow.authorization_url(
    access_type='offline', include_granted_scopes='true'
)

print(f"""
╔═══════════════════════════════════════════════╗
║  GOOGLE AUTH                                  ║
║  Tarayicinda su linki ac:                     ║
║                                               ║
║  {auth_url}
║                                               ║
║  Izin ver, Google seni localhost:{PORT}'a       ║
║  yonlendirecek. Ben kodu yakalayacagim.       ║
╚═══════════════════════════════════════════════╝
""")

# 120 saniye bekle
server.timeout = 120
try:
    while auth_code is None:
        server.handle_request()
except KeyboardInterrupt:
    # SIGINT ile zaten yakalandi, bu da guvenlik
    print("\n⚠️ Auth iptal edildi.", file=sys.stderr)
    server.server_close()
    sys.exit(1)

# Kodu token ile degis
try:
    flow.fetch_token(code=auth_code)
    creds = flow.credentials
except Exception as e:
    print(f"❌ Token alinamadi: {e}")
    server.server_close()
    sys.exit(1)

import pickle
try:
    with open(TOKEN_FILE, "wb") as f:
        pickle.dump(creds, f)
except OSError as e:
    print(f"❌ Token dosyasi yazilamadi ({TOKEN_FILE}): {e}")
    sys.exit(1)

print("✅ Google auth basarili! Token kaydedildi.")
print(f"   Token dosyasi: {TOKEN_FILE}")
