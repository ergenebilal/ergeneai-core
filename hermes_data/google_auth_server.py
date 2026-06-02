#!/usr/bin/env python3
"""Google Auth via local web server - port 8080"""
import os, sys, json, socket
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

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
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
            self.wfile.write(b"Code not found")
        return

    def log_message(self, *a):
        pass  # sus

# Port musait mi kontrol
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('127.0.0.1', PORT))
sock.close()

if result == 0:
    print(f"❌ Port {PORT} kullanimda. server.py'yi durdur veya farkli port dene.")
    sys.exit(1)

# Server baslat
server = HTTPServer(('localhost', PORT), Handler)

flow = InstalledAppFlow.from_client_secrets_file(
    os.path.expanduser("~/.google/credentials.json"),
    SCOPES,
    redirect_uri=REDIRECT_URI
)

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
║  Izin ver, Google seni localhost:8080'a       ║
║  yonlendirecek. Ben kodu yakalayacagim.       ║
╚═══════════════════════════════════════════════╝
""")

# 120 saniye bekle
server.timeout = 120
while auth_code is None:
    server.handle_request()

# Kodu token ile degis
flow.fetch_token(code=auth_code)
creds = flow.credentials

import pickle
with open(TOKEN_FILE, "wb") as f:
    pickle.dump(creds, f)

print("✅ Google auth basarili! Token kaydedildi.")
print(f"   Token dosyasi: {TOKEN_FILE}")
