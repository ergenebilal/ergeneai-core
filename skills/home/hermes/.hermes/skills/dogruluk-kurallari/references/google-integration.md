# Google API Integration — TAMAM ✅

## Durum

- **OAuth:** Tamamlandı ✅ (2 Haziran 2026)
- **credentials.json:** `~/.google/credentials.json` (Web application tipi)
- **token.pickle:** `~/.google/token.pickle` (refresh token var, 6 ay geçerli)
- **Client ID:** `73125813038-ipk243n3mqb1v6ee8tp0vs6g9mcarjqj.apps.googleusercontent.com`
- **Client Secret:** Cloud Console'dan al (GOCSPX-... ile başlar)
- **Redirect URI:** `https://n8n.aiergene.xyz/webhook/google-oauth` (public webhook)
- **Servisler:** Gmail, Calendar, Drive, Sheets — 4'ü de hazır

## Kullanılabilir Fonksiyonlar (tools.py'de, python3.11)

```python
import sys; sys.path.insert(0, '/home/hermes/hermes_data')
from tools import *
```

### E-posta
- `gmail_gonder(alici, konu, icerik, html=False)` — HTML destekli e-posta gönder
- `gmail_oku(max_sonuc=5)` — Son e-postaları listele

### Takvim
- `takvim_etkinlik_ekle(baslik, baslangic, bitis, aciklama="")` — Etkinlik ekle (ISO format)
- `takvim_etkinlik_listele(max_sonuc=10)` — Gelecek etkinlikleri listele

### Drive
- `drive_dosya_listele(klasor_id="root", max_sonuc=10)` — Drive dosyalarını listele
- `drive_dosya_yukle(dosya_yolu, hedef_klasor="root")` — Dosya yükle

### Sheets
- `sheets_oku(sheet_id, sayfa="Sheet1", huc_bolge="A1:Z100")` — Veri oku (2D liste döndürür)
- `sheets_yaz(sheet_id, sayfa="Sheet1", huc_bolge="A1", veriler=None)` — Veri yaz
- `sheets_ekle(sheet_id, sayfa="Sheet1", veriler=None)` — Satır ekle (append)

## Auth Yenileme

Refresh token varsa otomatik yenilenir. Eğer token geçersiz olursa:
1. `google_auth_link()` ile yeni auth URL'si üret
2. Kullanıcıya tıklat, webhook'a code gelsin
3. Kodu manuel olarak exchange et:
```python
import urllib.request, urllib.parse, json
data = urllib.parse.urlencode({"code": CODE, "client_id": CID,
    "client_secret": SECRET, "redirect_uri": REDIRECT, "grant_type": "authorization_code"}).encode()
resp = urllib.request.urlopen("https://oauth2.googleapis.com/token", data=data)
result = json.loads(resp.read().decode())
```

## Pişmiş Pitfall'lar

- **credentials.json'ı kontrol et!** Önceki oturumda "yazıldı" dense bile diskte olmayabilir. Her zaman `read_file` ile doğrula.
- **n8n API credential verisini göstermez** — Secrets şifreli. Var olan Gmail OAuth credential'ından client_id/secret alamazsın. Kullanıcıdan Cloud Console'dan almasını iste.
- **Uzun süreli hafıza için ChromaDB kullan** — Sistem hafızası (memory tool) 4K limitli. Kullanıcı hakkında öğrendiklerini `beyin_kaydet()` ile hermes_beyin'e kaydet, sonra `beyin_ara()` ile sorgula.
- **python3.11** — chromadb, google kütüphaneleri 3.11'e kurulu. `python3` (3.10) çalışmaz.

## Detaylı Skill

`skill_view(name='google-oauth-headless')` — headless sunucuda OAuth2 kurulumu
`skill_view(name='google-api-server')` — n8n webhook detayları, SQLite injection
