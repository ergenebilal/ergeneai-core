import subprocess
import time
import os
import pickle
import datetime
import chromadb
from chromadb.utils import embedding_functions
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# === KONFİGÜRASYON ===
CHROMA_HOST = "localhost"
CHROMA_PORT = 8001
HATA_LOG = os.path.expanduser("~/hermes_hata_log.txt")

# === LONGTRACER CACHE ===
_longtracer_model = None

def get_longtracer_model() -> object:
    """LongTracer modelini singleton olarak yukler ve dondurur.
    
    Returns:
        object: LongTracer model instance
    
    Ornek:
        lt = get_longtracer_model()
        result = lt.check(response="ornek", sources=["kaynak"])
    """
    global _longtracer_model
    if _longtracer_model is None:
        try:
            import longtracer
            _longtracer_model = longtracer
        except ImportError:
            _longtracer_model = None
    return _longtracer_model


def verify_claim(claim: str, source: str) -> dict:
    """Bir iddiayi LongTracer ile dogrular.
    
    Args:
        claim: Dogrulanacak iddia metni
        source: Kaynak referansi
    
    Returns:
        dict: {"verdict": "PASS"|"FAIL", "confidence": float|None}
    """
    try:
        lt = get_longtracer_model()
        if lt is None:
            return {"verdict": "UNKNOWN", "confidence": None}
        result = lt.check(response=claim, sources=[source])
        if hasattr(result, 'verdict'):
            return {"verdict": result.verdict, "confidence": getattr(result, 'confidence', None)}
        elif isinstance(result, dict):
            return result
        return {"verdict": "PASS" if result else "FAIL", "confidence": None}
    except Exception as e:
        return {"verdict": "ERROR", "confidence": None, "error": str(e)}

# === SİSTEM DURUMU ===
def check_system_status(service_name: str) -> dict:
    """Bir sistem servisinin calisip calismadigini kontrol eder.
    
    Args:
        service_name: Kontrol edilecek servis adi ("chroma", "docker")
    
    Returns:
        dict: {"status": "running"|"not_running", ...}
    """
    if service_name == "chroma":
        try:
            out = subprocess.check_output(["curl", "-sf", "http://localhost:8001/api/v2/heartbeat"], timeout=3, stderr=subprocess.DEVNULL).decode()
            return {"status": "running", "output": out} if out else {"status": "not_running"}
        except Exception:
            return {"status": "not_running", "error": "Bağlantı yok"}
    elif service_name == "docker":
        try:
            subprocess.check_output(["docker", "ps"], stderr=subprocess.DEVNULL)
            return {"status": "running"}
        except Exception:
            return {"status": "not_running"}
    return {"status": "unknown", "message": f"Bilinmeyen servis: {service_name}"}

# === HATA YÖNETİMİ ===
def log_hata(hata_tipi: str, detay: str, dogru_davranis: str) -> str:
    """Hata log dosyasina yeni bir kayit ekler.
    
    Args:
        hata_tipi: Hata kategorisi (ornek: "self_evolve", "chroma", "network")
        detay: Hata ile ilgili detayli aciklama
        dogru_davranis: Dogru davranis veya cozum onerisi
    
    Returns:
        str: Islem sonucu mesaji
    """
    try:
        with open(HATA_LOG, "a", encoding="utf-8") as f:
            f.write(f"{time.ctime()} | HATA: {hata_tipi} | DETAY: {detay} | DOGRUSU: {dogru_davranis}\n")
        return f"✅ Hata loglandi: {hata_tipi}"
    except Exception as e:
        return f"❌ Hata loglanamadi: {str(e)}"


def get_hata_gecmisi(limit: int = 5) -> list:
    """Son N hata kaydini getirir.
    
    Args:
        limit: Kac kayit getirilecegi (default: 5)
    
    Returns:
        list: Hata kayitlari listesi
    """
    try:
        if not os.path.exists(HATA_LOG):
            return []
        with open(HATA_LOG, "r", encoding="utf-8") as f:
            return f.readlines()[-limit:]
    except Exception as e:
        return [f"Hata okunamadi: {str(e)}"]

# === CHROMADB ARAMA ===
def bilal_notes_ara(soru: str, n_results: int = 3) -> list:
    """ChromaDB'de bilal_notes koleksiyonunda arama yapar.
    
    Args:
        soru: Aranacak sorgu metni
        n_results: Kac sonuc donecegi (default: 3)
    
    Returns:
        list: Bulunan dokumanlar listesi
    """
    try:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        collection = client.get_collection("bilal_notes")
        results = collection.query(query_texts=[soru], n_results=n_results)
        return results['documents'][0] if results['documents'] else []
    except Exception as e:
        return [f"Arama hatasi: {str(e)}"]


def dosya_ekle(dosya_yolu: str, koleksiyon: str = "bilal_notes") -> str:
    """Bir dosyayi ChromaDB koleksiyonuna ekler.
    
    Args:
        dosya_yolu: Eklenecek dosyanin yolu
        koleksiyon: Hedef koleksiyon adi (default: bilal_notes)
    
    Returns:
        str: Islem sonucu
    """
    try:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        collection = client.get_collection(koleksiyon)
        with open(dosya_yolu, 'r', encoding='utf-8') as f:
            content = f.read()
        doc_id = os.path.basename(dosya_yolu)
        collection.add(documents=[content], ids=[doc_id])
        return f"✅ {doc_id} eklendi."
    except Exception as e:
        return f"❌ Dosya ekleme hatasi: {str(e)}"

# === JARVIS SEVİYESİ YETENEKLER ===
_session_memory = []

def plan_hedef(hedef: str) -> dict:
    """Hedefe gore plan adimlarini dondurur.
    
    Args:
        hedef: Yapilacak isin tanimi
    
    Returns:
        dict: {"adimlar": [...], "aciklama": "..."}
    """
    plans = {
        "araştır": {
            "adimlar": ["bilal_notes_ara(hedef)", "verify_claim(sonuc, kaynak)"],
            "aciklama": "ChromaDB'de ara, sonra doğrula"
        },
        "kurulum": {
            "adimlar": ["check_system_status(servis)", "dosya_ekle(dosya)", "log_hata(...)"],
            "aciklama": "Sistem durumunu kontrol et, dosya ekle, hata logla"
        },
        "rapor": {
            "adimlar": ["get_hata_gecmisi()", "bilal_notes_ara(...)"],
            "aciklama": "Hata geçmişini al, ChromaDB'de ara"
        },
        "kod": {
            "adimlar": ["terminal_calistir('python3 kod.py')", "verify_claim(...)"],
            "aciklama": "Kodu çalıştır, sonucu doğrula"
        },
        "web": {
            "adimlar": ["web_cek(url)", "bilal_notes_ara(...)", "dosya_ekle(...)"],
            "aciklama": "Web'den veri çek, ara, kaydet"
        }
    }
    for anahtar, plan in plans.items():
        if anahtar in hedef.lower():
            return plan
    return {"adimlar": ["bilal_notes_ara(hedef)", "verify_claim(sonuc, kaynak)"], "aciklama": "Genel araştırma"}

def session_hatirla(mesaj: str) -> list:
    """Session hafizasina mesaj ekler, son 5 mesaji dondurur.
    
    Args:
        mesaj: Kaydedilecek mesaj
    
    Returns:
        list: Son 5 mesaj
    """
    try:
        _session_memory.append(mesaj)
        return _session_memory[-5:]
    except Exception as e:
        return [f"Hata: {str(e)}"]


def session_al() -> list:
    """Session hafizasinin tamamini dondurur.
    
    Returns:
        list: Tum session mesajlari
    """
    try:
        return _session_memory
    except Exception as e:
        return [f"Hata: {str(e)}"]

def terminal_calistir(komut: str, timeout: int = 30) -> str:
    """Shell komutu calistirir ve ciktisini dondurur.
    
    Args:
        komut: Calistirilacak komut
        timeout: Maksimum bekleme saniyesi (default: 30)
    
    Returns:
        str: Komut ciktisi veya hata mesaji
    """
    try:
        result = subprocess.check_output(komut.split(), text=True, stderr=subprocess.STDOUT, timeout=timeout)
        return result.strip()
    except subprocess.TimeoutExpired:
        return f"HATA: Komut {timeout} saniyede tamamlanamadı"
    except Exception as e:
        return f"HATA: {str(e)}"

def web_cek(url: str, max_karakter: int = 2000) -> str:
    """Web sayfasinin icerigini HTTP ile ceker.
    
    Args:
        url: Cekilecek web sayfasi URL'si
        max_karakter: Maksimum karakter sayisi (default: 2000)
    
    Returns:
        str: Sayfa icerigi veya hata mesaji
    """
    try:
        import requests
        r = requests.get(url, timeout=10, headers={"User-Agent": "Hermes-Agent"})
        r.raise_for_status()
        return r.text[:max_karakter]
    except Exception as e:
        return f"❌ Web hatasi: {str(e)}"

def self_repair(hata_mesaji: str, deneme: int = 1) -> str:
    """Hata mesajina gore cozum onerisi dondurur.
    
    Args:
        hata_mesaji: Alinan hata mesaji
        deneme: Kacinci deneme oldugu (default: 1)
    
    Returns:
        str: Cozum onerisi
    """
    try:
        if deneme >= 3:
            return "⚠️ Maksimum deneme (3) aşıldı. Manuel müdahale gerekli."
        hata = hata_mesaji.lower()
        if "chromadb" in hata or "chroma" in hata:
            return "🔄 ChromaDB yeniden başlatılıyor: chroma run --host 0.0.0.0 --port 8001 &"
        elif "dosya" in hata and "yok" in hata:
            return "📄 Dosya oluşturuluyor: touch yeni_dosya.txt"
        elif "bağlantı" in hata or "connection" in hata:
            return "🌐 Bağlantı kontrol ediliyor: curl -I https://httpbin.org"
        else:
            return f"🛠 Bilinmeyen hata, alternatif deneniyor (deneme {deneme + 1}): {hata_mesaji[:100]}"
    except Exception as e:
        return f"❌ self_repair hatasi: {str(e)}"

TELEGRAM_BOT_TOKEN = "8654902345:AAGqkOTA1QcDZ59T6h5jl7LCqZXhMxgNofQ"
TELEGRAM_CHAT_ID = "5506784207"

def telegram_mesaj_gonder(mesaj: str) -> bool:
    """Telegram'a mesaj gonderir.
    
    Args:
        mesaj: Gonderilecek mesaj metni
    
    Returns:
        bool: Basarili mi
    """
    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": mesaj}
        r = requests.post(url, json=data, timeout=10)
        return r.json().get("ok", False)
    except Exception:
        return False

def otonom_calistir(hedef):
    """
    Hedefi dogrudan ChromaDB'de ara, sonucu verify_claim ile dogrula.
    Donen: {'arama_sonucu': [...], 'dogrulama': {...}}
    """
    try:
        zaman = suan()
        print(f"Suan: {zaman['tarih']} {zaman['saat']}, {zaman['gun']}")

        # 1. ChromaDB'de ara
        arama_sonucu = bilal_notes_ara(hedef)
        if not arama_sonucu:
            return {"arama_sonucu": [], "dogrulama": "ChromaDB'de sonuc yok"}
        
        # 2. Ilk sonucu al (en alakali)
        ilk_sonuc = arama_sonucu[0]
        
        # 3. Dogrulama icin kaynak
        dogrulama = verify_claim(ilk_sonuc, "ChromaDB kaydi")
        
        return {
            "arama_sonucu": arama_sonucu,
            "dogrulama": dogrulama
        }
    except Exception as e:
        return {"hata": str(e)}


def analiz_et(mesaj):
    """
    Basit duygu analizi.
    Donus: {"durum": "MUTLU|YORGUN|NOTR", "skor": -1..1, "tetikleyenler": []}
    """
    olumlu_kelime = ["teşekkür", "harika", "süper", "iyi", "başarılı", "aferin", "mükemmel"]
    olumsuz_kelime = ["kötü", "hata", "yanlış", "sinir", "yorgun", "bıktım", "yeter", "uğraşma"]
    mesaj_lower = mesaj.lower()

    tetikleyenler = []
    skor = 0

    for k in olumlu_kelime:
        if k in mesaj_lower:
            tetikleyenler.append(k)
            skor += 0.3
    for k in olumsuz_kelime:
        if k in mesaj_lower:
            tetikleyenler.append(k)
            skor -= 0.4

    skor = max(-1.0, min(1.0, skor))

    if skor > 0.2:
        durum = "MUTLU"
    elif skor < -0.2:
        durum = "YORGUN/SINIRLI"
    else:
        durum = "NOTR"

    return {"durum": durum, "skor": skor, "tetikleyenler": tetikleyenler}


def hesap_hesapla(tur, miktar, gun_kaldi):
    """Basit finans hesaplama: gelir/gider gunluk karsilik"""
    if tur == "gider":
        gunluk = miktar / gun_kaldi if gun_kaldi > 0 else 0
        return f"Gider: {miktar} TL, {gun_kaldi} gun kaldi. Gunde ~{gunluk:.2f} TL ayir."
    elif tur == "gelir":
        gunluk = miktar / gun_kaldi if gun_kaldi > 0 else 0
        return f"Gelir: {miktar} TL, {gun_kaldi} gun kaldi. Gunde ~{gunluk:.2f} TL birikecek."
    else:
        return "Bilinmeyen islem turu"


def suan() -> dict:
    """Su anki tarih, saat ve gun bilgisini dondurur.
    
    Returns:
        dict: {"tarih": "2026-06-02", "saat": "03:47", "gun": "Tuesday", "timestamp": "2026-06-02T03:47:00"}
    """
    try:
        now = datetime.datetime.now()
        return {
            "tarih": now.strftime("%Y-%m-%d"),
            "saat": now.strftime("%H:%M"),
            "gun": now.strftime("%A"),
            "timestamp": now.isoformat()
        }
    except Exception as e:
        return {"hata": str(e)}


# === GOOGLE API ENTEGRASYONU ===
GOOGLE_CREDENTIALS = os.path.expanduser("~/.google/credentials.json")
GOOGLE_TOKEN = os.path.expanduser("~/.google/token.pickle")
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets",
]

def google_auth():
    """Google API kimlik dogrulama — token varsa kullan, yoksa hata don."""
    creds = None
    if os.path.exists(GOOGLE_TOKEN):
        with open(GOOGLE_TOKEN, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(GOOGLE_TOKEN, "wb") as f:
                pickle.dump(creds, f)
            return creds, None
        return None, "❌ Google token gecersiz. Yeniden auth yap: google_auth_link() ile link al."
    return creds, None

def google_auth_link():
    """Yeni auth linki olusturur (manuel tiklama icin)."""
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            GOOGLE_CREDENTIALS, GOOGLE_SCOPES,
            redirect_uri="https://n8n.aiergene.xyz/webhook/google-oauth"
        )
        auth_url, _ = flow.authorization_url(
            access_type='offline', include_granted_scopes='true', prompt='consent'
        )
        return auth_url
    except Exception as e:
        return f"❌ Auth linki olusturulamadi: {str(e)}"

def gmail_gonder(alici, konu, icerik, html=False):
    """Gmail ile e-posta gonderir.
    alici: e-posta adresi
    konu: konu basligi
    icerik: mesaj icerigi (duz metin veya HTML)
    html: True ise HTML formatinda gonder
    """
    try:
        creds, hata = google_auth()
        if hata:
            return hata
        service = build("gmail", "v1", credentials=creds)
        import base64
        from email.mime.text import MIMEText
        mesaj = MIMEText(icerik, "html" if html else "plain")
        mesaj["to"] = alici
        mesaj["subject"] = konu
        raw = base64.urlsafe_b64encode(mesaj.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return f"✅ E-posta gonderildi: {alici} -> {konu}"
    except Exception as e:
        return f"❌ Gmail hatasi: {str(e)}"

def gmail_oku(max_sonuc=5):
    """Gelen kutusundaki son epostalarin basliklarini getirir."""
    try:
        creds, hata = google_auth()
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
            liste.append({"id": m["id"][:8], "baslik": baslik})
        return liste
    except Exception as e:
        return f"❌ Gmail okuma hatasi: {str(e)}"

def takvim_etkinlik_ekle(baslik, baslangic, bitis, aciklama=""):
    """Google Calendar'a etkinlik ekler.
    baslik: etkinlik adi
    baslangic: ISO format baslangic (orn: \"2026-06-03T10:00:00\")
    bitis: ISO format bitis
    aciklama: opsiyonel aciklama
    """
    try:
        creds, hata = google_auth()
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
        creds, hata = google_auth()
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
            {"baslik": e.get("summary", ""),
             "baslangic": e["start"].get("dateTime", e["start"].get("date"))}
            for e in sonuc.get("items", [])
        ]
    except Exception as e:
        return f"❌ Takvim listeleme hatasi: {str(e)}"


# === Google Drive ===
def drive_dosya_listele(klasor_id="root", max_sonuc=10):
    """Google Drive'daki dosyalari listeler.
    klasor_id: Klasor ID'si (default: root)
    max_sonuc: Maksimum dosya sayisi
    Donus: dosya listesi veya hata mesaji
    """
    try:
        creds, hata = google_auth()
        if hata:
            return hata
        service = build("drive", "v3", credentials=creds)
        sonuc = service.files().list(
            q=f"'{klasor_id}' in parents and trashed=false",
            pageSize=max_sonuc,
            fields="files(id, name, mimeType, size, createdTime)"
        ).execute()
        dosyalar = sonuc.get("files", [])
        if not dosyalar:
            return "📂 Drive'da dosya bulunamadi."
        return [
            {
                "id": d["id"],
                "ad": d["name"],
                "tur": d["mimeType"].split(".")[-1] if "." in d["mimeType"] else d["mimeType"],
                "boyut": f"{int(d.get('size', 0)) / 1024:.1f} KB" if d.get("size") else "bilinmiyor"
            }
            for d in dosyalar
        ]
    except Exception as e:
        return f"❌ Drive listeleme hatasi: {str(e)}"


def drive_dosya_yukle(dosya_yolu, hedef_klasor="root"):
    """Yerel bir dosyayi Google Drive'a yukler.
    dosya_yolu: Yuklenecek dosyanin yolu
    hedef_klasor: Hedef klasor ID'si (default: root)
    Donus: basari veya hata mesaji
    """
    try:
        if not os.path.exists(dosya_yolu):
            return f"❌ Dosya bulunamadi: {dosya_yolu}"
        creds, hata = google_auth()
        if hata:
            return hata
        service = build("drive", "v3", credentials=creds)
        from googleapiclient.http import MediaFileUpload
        dosya_adi = os.path.basename(dosya_yolu)
        media = MediaFileUpload(dosya_yolu, resumable=True)
        metadata = {"name": dosya_adi, "parents": [hedef_klasor]}
        dosya = service.files().create(body=metadata, media_body=media, fields="id,name").execute()
        return f"✅ Drive'a yuklendi: {dosya['name']} (ID: {dosya['id'][:20]}...)"
    except Exception as e:
        return f"❌ Drive yukleme hatasi: {str(e)}"


# === Google Sheets ===
def sheets_oku(sheet_id, sayfa="Sheet1", huc_bolge="A1:Z100"):
    """Google Sheets'ten veri okur.
    sheet_id: Sheet'in ID'si (URL'deki uzun kod)
    sayfa: Sayfa adi (default: Sheet1)
    huc_bolge: Huc Bolge (default: A1:Z100)
    Donus: satir listesi veya hata mesaji
    """
    try:
        creds, hata = google_auth()
        if hata:
            return hata
        service = build("sheets", "v4", credentials=creds)
        range_name = f"{sayfa}!{huc_bolge}"
        sonuc = service.spreadsheets().values().get(
            spreadsheetId=sheet_id, range=range_name
        ).execute()
        degerler = sonuc.get("values", [])
        if not degerler:
            return "📊 Sheet'te veri bulunamadi."
        return degerler
    except Exception as e:
        return f"❌ Sheet okuma hatasi: {str(e)}"


def sheets_yaz(sheet_id, sayfa="Sheet1", huc_bolge="A1", veriler=None):
    """Google Sheets'e veri yazar.
    sheet_id: Sheet'in ID'si
    sayfa: Sayfa adi
    huc_bolge: Baslangic huc Bolge (default: A1)
    veriler: 2 boyutlu liste [[satir1_h1, satir1_h2], [satir2_h1, satir2_h2]]
    Donus: basari veya hata mesaji
    """
    if veriler is None:
        return "❌ Veri gerekli"
    try:
        creds, hata = google_auth()
        if hata:
            return hata
        service = build("sheets", "v4", credentials=creds)
        range_name = f"{sayfa}!{huc_bolge}"
        body = {"values": veriler}
        sonuc = service.spreadsheets().values().update(
            spreadsheetId=sheet_id, range=range_name,
            valueInputOption="USER_ENTERED", body=body
        ).execute()
        return f"✅ Sheet'e yazildi: {sonuc.get('updatedCells', 0)} hucBolge guncellendi"
    except Exception as e:
        return f"❌ Sheet yazma hatasi: {str(e)}"


def sheets_ekle(sheet_id, sayfa="Sheet1", veriler=None):
    """Google Sheets'e yeni satir ekler (append).
    sheet_id: Sheet'in ID'si
    sayfa: Sayfa adi
    veriler: 2 boyutlu liste [[h1, h2], [h3, h4]]
    Donus: basari veya hata mesaji
    """
    if veriler is None:
        return "❌ Veri gerekli"
    try:
        creds, hata = google_auth()
        if hata:
            return hata
        service = build("sheets", "v4", credentials=creds)
        range_name = f"{sayfa}!A1"
        body = {"values": veriler}
        sonuc = service.spreadsheets().values().append(
            spreadsheetId=sheet_id, range=range_name,
            valueInputOption="USER_ENTERED", insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
        return f"✅ Sheet'e eklendi: {sonuc.get('updates', {}).get('updatedRows', 0)} satir"
    except Exception as e:
        return f"❌ Sheet ekleme hatasi: {str(e)}"


# === HAVA DURUMU ===
def hava_durumu(sehir="Bursa"):
    """Belirtilen sehrin hava durumunu sorgular.
    sehir: Sehir adi (default: Bursa)
    Donus: hava bilgisi veya hata mesaji
    """
    try:
        import requests as req
        url = f"https://wttr.in/{sehir}?format=%C+%t+%h+%w&lang=tr"
        resp = req.get(url, timeout=10)
        if resp.status_code == 200:
            bilgi = resp.text.strip()
            return f"🌤 {sehir}: {bilgi}"
        return f"❌ Hava durumu alinamadi (HTTP {resp.status_code})"
    except Exception as e:
        return f"❌ Hava durumu hatasi: {str(e)}"


# === HATIRLATICI ===
def hatirlatici_kur(mesaj, dakika_sonra):
    """Kisa sureli hatirlatici kurar (dakika hassasiyetinde).
    mesaj: Hatirlatma mesaji
    dakika_sonra: Kac dakika sonra hatirlatilsin
    Donus: basari mesaji
    """
    try:
        import threading
        def _hatirlat():
            import time
            time.sleep(dakika_sonra * 60)
            try:
                telegram_mesaj_gonder(f"⏰ HATIRLATICI: {mesaj}")
            except:
                pass
        t = threading.Thread(target=_hatirlat, daemon=True)
        t.start()
        return f"⏰ Hatirlatici kuruldu: {dakika_sonra} dk sonra \"{mesaj}\""
    except Exception as e:
        return f"❌ Hatirlatici hatasi: {str(e)}"


# === HERMES BEYİN (ChromaDB Kalıcı Hafıza) ===
def beyin_ara(soru: str, n_results: int = 5) -> list:
    """Hermes'in kalici beyninde (ChromaDB) arama yapar.
    
    Args:
        soru: Aranacak sorgu
        n_results: Kac sonuc
    
    Returns:
        list: Bulunan dokumanlar
    """
    try:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        collection = client.get_collection("hermes_beyin")
        results = collection.query(query_texts=[soru], n_results=n_results)
        return results['documents'][0] if results['documents'] else []
    except Exception as e:
        # Koleksiyon yoksa olustur
        if "does not exist" in str(e):
            return ["🧠 Hermes beyni henuz olusturulmadi. 'beyin_kaydet' ile baslat."]
        return [f"Beyin hatasi: {str(e)}"]


def beyin_kaydet(bilgi: str, tur: str = "genel", etiket: str = "") -> str:
    """Hermes'in kalici beynine bilgi kaydeder.
    
    Args:
        bilgi: Kaydedilecek bilgi metni
        tur: Bilgi turu (genel, soz, hedef, ogrenme, hata)
        etiket: Opsiyonel etiket
    
    Returns:
        str: Islem sonucu
    """
    try:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        try:
            collection = client.get_collection("hermes_beyin")
        except:
            collection = client.create_collection(
                name="hermes_beyin",
                embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name='paraphrase-multilingual-MiniLM-L12-v2'
                )
            )
        
        import hashlib
        doc_id = hashlib.md5(bilgi.encode()).hexdigest()[:16]
        
        collection.add(
            documents=[bilgi],
            ids=[doc_id],
            metadatas=[{"tur": tur, "etiket": etiket, "tarih": datetime.datetime.now().isoformat()[:10]}]
        )
        return f"✅ Beyne kaydedildi ({tur})"
    except Exception as e:
        return f"❌ Beyin kayit hatasi: {str(e)}"


print("✅ tools.py yuklendi. Mevcut fonksiyonlar:")
print("   - bilal_notes_ara, dosya_ekle, plan_hedef, session_hatirla")
print("   - terminal_calistir, web_cek, self_repair, telegram_mesaj_gonder, otonom_calistir")
print("   - analiz_et, hesap_hesapla, suan")
print("   - google_auth, google_auth_link, gmail_gonder, gmail_oku")
print("   - takvim_etkinlik_ekle, takvim_etkinlik_listele")
print("   - drive_dosya_listele, drive_dosya_yukle")
print("   - sheets_oku, sheets_yaz, sheets_ekle")
print("   - hava_durumu, hatirlatici_kur")
print("   - beyin_ara, beyin_kaydet")