#!/usr/bin/env python3
"""
self_evolve.py — Hermes'in kendini geliştiren beyni

Seviye: EXPERT
====================
Yapabildikleri:
  1. SCA: tools.py'yi analiz et, eksikleri/hataları/iyileştirmeleri bul
  2. SUG: Ne eklenmesi gerektiğini öner ("şu eksik, bunu eklemeliyim")
  3. GEN: DeepSeek API ile kod üret + test et + tools.py'ye ekle
  4. FIX: Hatalı fonksiyonları oto-düzelt (3 deneme döngüsü)
  5. AUD: Kod kalitesi denetimi (docstring, try/except, type hints)
  6. CHG: Değişiklik geçmişi tut
  7. PRN: Kullanılmayan/eski fonksiyonları temizle
====================
"""
import sys, subprocess, os, re, json, datetime, importlib, textwrap, ast
sys.path.insert(0, os.path.expanduser("~/hermes_data"))

# ─────────────────────────────────────────────
# KONFİGÜRASYON
# ─────────────────────────────────────────────
TOOLS_PATH = os.path.expanduser("~/hermes_data/tools.py")
HATA_LOG = os.path.expanduser("~/hermes_hata_log.txt")
EVOLVE_LOG = os.path.expanduser("~/hermes_evolve_log.json")
ENV_PATH = os.path.expanduser("~/.hermes/.env")
MAX_FIX_ATTEMPTS = 3
SCORE_THRESHOLD = 0.6  # Kalite skoru altındaki fonksiyonları iyileştir


# ─────────────────────────────────────────────
# YARDIMCI FONKSİYONLAR
# ─────────────────────────────────────────────

def _api_key_al():
    """~/.hermes/.env dosyasından DEEPSEEK_API_KEY oku."""
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DEEPSEEK_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("DEEPSEEK_API_KEY")


def _telegram_gonder(mesaj):
    """Telegram'a mesaj gönder (tools import etmeden)."""
    try:
        import requests
        token_path = os.path.expanduser("~/.hermes/.env")
        token = None
        if os.path.exists(token_path):
            with open(token_path) as f:
                for line in f:
                    if line.startswith("TELEGRAM_BOT_TOKEN="):
                        token = line.split("=", 1)[1].strip().strip('"').strip("'")
        if token:
            chat_id = os.environ.get("TELEGRAM_CHAT_ID", "5506784207")
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": mesaj},
                timeout=10
            )
    except:
        pass


def _log_hata(hata_tipi, detay, dogru_davranis):
    """Hata loguna yaz."""
    with open(HATA_LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now().isoformat()} | HATA: {hata_tipi} | DETAY: {detay} | DOGRUSU: {dogru_davranis}\n")


def _evolve_log_ekle(entry):
    """Değişiklik geçmişine ekle."""
    log = []
    if os.path.exists(EVOLVE_LOG):
        try:
            with open(EVOLVE_LOG, "r") as f:
                log = json.load(f)
        except:
            log = []
    entry["timestamp"] = datetime.datetime.now().isoformat()
    log.append(entry)
    with open(EVOLVE_LOG, "w") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


def _tools_oku():
    """tools.py'nin tam içeriğini ve AST'sini döndür."""
    if not os.path.exists(TOOLS_PATH):
        return None, None
    with open(TOOLS_PATH, "r") as f:
        content = f.read()
    try:
        tree = ast.parse(content)
    except SyntaxError:
        tree = None
    return content, tree


def _tools_yaz(content):
    """tools.py'ye yaz (yedek alarak)."""
    yedek = TOOLS_PATH + ".bak"
    if os.path.exists(TOOLS_PATH):
        os.replace(TOOLS_PATH, yedek)
    with open(TOOLS_PATH, "w") as f:
        f.write(content)


def _tools_ekle(kod, kategori=None):
    """tools.py'nin sonuna, print'lerden önce kod ekle."""
    content, tree = _tools_oku()
    if not content:
        return False

    # Print satırlarını bul
    lines = content.split("\n")
    print_start = None
    for i, line in enumerate(lines):
        if 'print("✅ tools.py' in line or "print('✅ tools.py" in line:
            print_start = i
            break

    if print_start:
        # Kategori yorumu ekle
        if kategori:
            eklenecek = f"\n\n# === {kategori} ===\n{kod}"
        else:
            eklenecek = f"\n\n{kod}"
        lines.insert(print_start, eklenecek)
        _tools_yaz("\n".join(lines))
    else:
        with open(TOOLS_PATH, "a") as f:
            if kategori:
                f.write(f"\n\n# === {kategori} ===\n{kod}")
            else:
                f.write(f"\n\n{kod}")
    return True


# ─────────────────────────────────────────────
# 1. SCA: tools.py ANALİZ MOTORU
# ─────────────────────────────────────────────

def analiz_et():
    """
    tools.py'yi tarar, her fonksiyon için kalite skoru çıkarır,
    eksik kategorileri, hataları, iyileştirme fırsatlarını raporlar.

    Dönüş: {
        "fonksiyonlar": [{"ad", "satir", "kalite_skor", "docstring", "try_except", "tip_ipucu", "satir_sayisi", "sorunlar"}, ...],
        "kategoriler": {"var": [...], "eksik": [...]},
        "genel_skor": 0.0-1.0,
        "oneriler": [...]
    }
    """
    content, tree = _tools_oku()
    if not content:
        return {"hata": "tools.py bulunamadı"}

    sonuc = {
        "fonksiyonlar": [],
        "kategoriler": {"var": set(), "eksik": set()},
        "genel_skor": 0.0,
        "oneriler": []
    }

    lines = content.split("\n")

    if tree is None:
        sonuc["oneriler"].append("⚠️ tools.py'de syntax hatası var! Düzeltilmeli.")
        return sonuc

    # Mevcut kategorileri bul
    kategori_eklenecek = False
    for line in lines:
        m = re.match(r"# === (.+) ===", line)
        if m:
            sonuc["kategoriler"]["var"].add(m.group(1).strip())

    # AST ile fonksiyonları analiz et
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            fonk_adi = node.name
            if fonk_adi.startswith("_"):
                continue  # Private fonksiyonları atla

            fonk = {
                "ad": fonk_adi,
                "satir": node.lineno,
                "docstring": None,
                "try_except": False,
                "tip_ipucu": False,
                "param_sayisi": len(node.args.args),
                "satir_sayisi": (node.end_lineno - node.lineno + 1) if hasattr(node, 'end_lineno') else 0,
                "sorunlar": []
            }

            # Docstring kontrol
            if (node.body and isinstance(node.body[0], ast.Expr) and
                isinstance(node.body[0].value, ast.Constant) and
                isinstance(node.body[0].value.value, str) and
                len(node.body[0].value.value) > 20):
                fonk["docstring"] = node.body[0].value.value[:100]

            # try/except kontrol
            for n in ast.walk(node):
                if isinstance(n, ast.Try):
                    fonk["try_except"] = True
                    break

            # Type hints kontrol
            if node.returns or any(a.annotation for a in node.args.args if a.annotation):
                fonk["tip_ipucu"] = True

            # Kalite skoru hesapla
            skor = 0.0
            if fonk["docstring"]:
                skor += 0.35
            if fonk["try_except"]:
                skor += 0.35
            if fonk["tip_ipucu"]:
                skor += 0.15
            if fonk["satir_sayisi"] >= 8:
                skor += 0.15  # Yeterince uzun, gerçek iş yapıyor
            fonk["kalite_skor"] = round(skor, 2)

            # Sorunları tespit et
            if not fonk["docstring"]:
                fonk["sorunlar"].append("📄 Docstring yok")
            if not fonk["try_except"]:
                fonk["sorunlar"].append("⚠️ Hata yönetimi yok")
            if not fonk["tip_ipucu"]:
                fonk["sorunlar"].append("🔤 Tip ipucu yok")
            if fonk["satir_sayisi"] < 5 and fonk_adi not in ("suan",):
                fonk["sorunlar"].append("📏 Çok kısa, geliştirilebilir")

            sonuc["fonksiyonlar"].append(fonk)

    # Eksik kategorileri belirle
    tum_kategoriler = {
        "Google Gmail": ["gmail_gonder", "gmail_oku"],
        "Google Calendar": ["takvim_etkinlik_ekle", "takvim_etkinlik_listele"],
        "Google Drive": ["drive_dosya_ekle", "drive_dosya_listele"],
        "Google Sheets": ["sheets_oku", "sheets_yaz"],
        "ChromaDB": ["bilal_notes_ara", "dosya_ekle"],
        "Sistem": ["check_system_status", "terminal_calistir"],
        "Hata Yönetimi": ["log_hata", "get_hata_gecmisi"],
        "İletişim": ["telegram_mesaj_gonder"],
        "Analiz": ["analiz_et"],
        "Finans": ["hesap_hesapla"],
    }

    mevcut_isimler = {f["ad"] for f in sonuc["fonksiyonlar"]}

    # Mevcut fonksiyonlara göre kategorileri belirle
    for kat, fonklar in tum_kategoriler.items():
        var_mi = any(f in mevcut_isimler for f in fonklar)
        if var_mi:
            sonuc["kategoriler"]["var"].add(kat)
        else:
            sonuc["kategoriler"]["eksik"].add(kat)

    # Eksik fonksiyon önerileri
    if not any(f["ad"] == "drive_dosya_listele" for f in sonuc["fonksiyonlar"]):
        sonuc["oneriler"].append("📂 Google Drive fonksiyonları eksik — drive_dosya_listele() eklenebilir")
    if not any(f["ad"] == "sheets_oku" for f in sonuc["fonksiyonlar"]):
        sonuc["oneriler"].append("📊 Google Sheets fonksiyonları eksik — sheets_oku() eklenebilir")
    if not any(f["ad"] == "hava_durumu" for f in sonuc["fonksiyonlar"]):
        sonuc["oneriler"].append("🌤 Hava durumu sorgulama eklenebilir")
    if not any(f["ad"] == "hatirlatici_kur" for f in sonuc["fonksiyonlar"]):
        sonuc["oneriler"].append("⏰ Kalıcı hatırlatıcı sistemi kurulabilir")

    # Düşük kaliteli fonksiyonları tespit et
    dusuk_kalite = [f for f in sonuc["fonksiyonlar"] if f["kalite_skor"] < SCORE_THRESHOLD]
    for f in dusuk_kalite:
        sonuc["oneriler"].append(f"🔧 {f['ad']}() kalite skoru {f['kalite_skor']} — iyileştirilmeli")

    # Genel skor
    if sonuc["fonksiyonlar"]:
        ort = sum(f["kalite_skor"] for f in sonuc["fonksiyonlar"]) / len(sonuc["fonksiyonlar"])
        sonuc["genel_skor"] = round(ort, 2)

    # Set'leri list'e çevir
    sonuc["kategoriler"]["var"] = sorted(sonuc["kategoriler"]["var"])
    sonuc["kategoriler"]["eksik"] = sorted(sonuc["kategoriler"]["eksik"])

    return sonuc


# ─────────────────────────────────────────────
# 2. SUG: EKSİKLİK ÖNERİ MOTORU
# ─────────────────────────────────────────────

def ne_eklemeliyim():
    """
    Analiz + hata logu + kullanım desenlerine bakarak
    hangi fonksiyonların ekleneceğini veya iyileştirileceğini önerir.

    Dönüş: str — doğal dil öneri
    """
    analiz = analiz_et()
    if "hata" in analiz:
        return f"❌ Analiz hatası: {analiz['hata']}"

    # Hata logundan trend çıkar
    hata_trend = {}
    if os.path.exists(HATA_LOG):
        with open(HATA_LOG, "r") as f:
            for line in f.readlines()[-50:]:
                m = re.search(r"HATA: (\w+)", line)
                if m:
                    hata_trend[m.group(1)] = hata_trend.get(m.group(1), 0) + 1

    oneriler = []

    # Genel skor
    oneriler.append(f"📊 tools.py genel kalite skoru: {analiz['genel_skor']}/1.0")
    if analiz['genel_skor'] < 0.6:
        oneriler.append("   ⚠️ Düşük! İyileştirme gerekiyor.")

    # Eksik kategoriler
    if analiz['kategoriler']['eksik']:
        oneriler.append(f"\n📦 **Eksik Kategoriler:**")
        for kat in analiz['kategoriler']['eksik']:
            oneriler.append(f"   ➕ {kat}")

    # Düşük kaliteli fonksiyonlar
    dusuk = [f for f in analiz['fonksiyonlar'] if f['kalite_skor'] < SCORE_THRESHOLD]
    if dusuk:
        oneriler.append(f"\n🔧 **İyileştirilmesi Gerekenler:**")
        for f in dusuk[:5]:
            oneriler.append(f"   • {f['ad']}() — skor: {f['kalite_skor']} ({', '.join(f['sorunlar'])})")

    # Öneriler
    if analiz['oneriler']:
        oneriler.append(f"\n💡 **Öneriler:**")
        for o in analiz['oneriler'][:5]:
            oneriler.append(f"   • {o}")

    # Hata trendi
    if hata_trend:
        en_sik = max(hata_trend, key=hata_trend.get)
        oneriler.append(f"\n🔥 **En sık hata:** {en_sik} ({hata_trend[en_sik]} kez)")
        if en_sik == "self_evolve":
            oneriler.append("   → self_evolve hata veriyor, kontrol edilmeli!")

    # Kritik öneri
    oneriler.append(f"\n🎯 **Aciliyet:**")
    if analiz['genel_skor'] < 0.5:
        oneriler.append("   🔴 KRİTİK: tools.py'nin yarısından fazlası düşük kaliteli")
    elif analiz['genel_skor'] < 0.7:
        oneriler.append("   🟡 ORTA: Belirli fonksiyonlar iyileştirilmeli")
    else:
        oneriler.append("   🟢 İYİ: Genel durum sağlıklı")

    return "\n".join(oneriler)


# ─────────────────────────────────────────────
# 3. GEN: AKILLI KOD ÜRETİMİ
# ─────────────────────────────────────────────

def kod_uret(fonksiyon_adi, aciklama, kategori=None, ek_bilgi=""):
    """
    DeepSeek API ile kod üret → test et → tools.py'ye ekle.
    Hata varsa MAX_FIX_ATTEMPTS kadar düzeltme döngüsü.

    Parametreler:
        fonksiyon_adi: Oluşturulacak fonksiyon adı
        aciklama: Ne iş yapacağı (detaylı doğal dil)
        kategori: Hangi kategori altına eklenecek (opsiyonel)
        ek_bilgi: Kullanabileceği tools.py fonksiyonları, API'ler vb.

    Dönüş: {"durum": "ok"|"hata", "mesaj": "...", "kod": "..."}
    """
    api_key = _api_key_al()
    if not api_key:
        return {"durum": "hata", "mesaj": "❌ DEEPSEEK_API_KEY bulunamadı"}

    # tools.py içeriğini oku (bağlam için)
    content, tree = _tools_oku()
    mevcut_fonk_isimleri = []
    mevcut_importlar = []
    if tree:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                mevcut_fonk_isimleri.append(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    mevcut_importlar.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    mevcut_importlar.append(f"{node.module}.{alias.name}")

    # DeepSeek prompt'u
    prompt = f"""Sen Hermes Agent'in kod geliştiricisin. tools.py'ye eklenecek bir Python fonksiyonu yaz.

Fonksiyon adı: {fonksiyon_adi}
Açıklama: {aciklama}

MEVCUT İMPORTLAR (bunlar zaten tools.py'de, tekrar import etme):
{', '.join(sorted(set(mevcut_importlar)))}

MEVCUT FONKSİYONLAR (bunları çağırabilirsin):
{', '.join(sorted(set(mevcut_fonk_isimleri)))}

KURALLAR:
1. Sadece Python kodu yaz, açıklama yapma.
2. `def {fonksiyon_adi}(...):` ile başlasın.
3. Docstring ekle (parametreleri ve dönüş değerini açıkla).
4. Try/except hata yönetimi ekle.
5. Tip ipuçları ekle (mümkünse).
6. Parametreleri mantıklı ve esnek seç.
7. Dönüş değeri string veya dict olsun (JSON serileştirilebilir).
8. Mevcut fonksiyonları ÇAĞIRABİLİRSİN (yukarıda listelendi).
9. Mevcut importları TEKRAR IMPORT ETME.
10. Yeni bir import gerekiyorsa, fonksiyon içinde lokal import yap.
11. Fonksiyon anlamlı iş yapsın, boilerplate olmasın.
12. Hata mesajları Türkçe olsun.

{("EK BILGI: " + ek_bilgi) if ek_bilgi else ""}

Fonksiyon kodu:"""

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a Python code generator for Hermes Agent. Write clean, working, production-quality Python functions. Return ONLY the function code, no markdown, no explanations. The code must be syntactically valid Python."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 2048
    }

    deneme = 0
    while deneme < MAX_FIX_ATTEMPTS:
        deneme += 1
        try:
            import requests as req
            resp = req.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=90
            )
            resp.raise_for_status()
            data = resp.json()

            ham_kod = data["choices"][0]["message"]["content"].strip()

            # Markdown kod bloklarını temizle
            kod = ham_kod
            kod = re.sub(r"^```python\s*\n?", "", kod)
            kod = re.sub(r"^```\s*\n?", "", kod)
            kod = re.sub(r"\n?\s*```$", "", kod)
            kod = kod.strip()

            # def ile başlamıyorsa düzelt
            if not kod.startswith("def "):
                for satir in kod.split("\n"):
                    if satir.strip().startswith("def "):
                        idx = kod.split("\n").index(satir)
                        kod = "\n".join(kod.split("\n")[idx:])
                        break

            # Test et
            test_dosya = "/tmp/self_evolve_test.py"
            test_kod = kod + f"\n\nif __name__ == '__main__':\n    print({fonksiyon_adi}.__name__)\n    # Basit çağrı testi\n    try:\n        import inspect\n        sig = inspect.signature({fonksiyon_adi})\n        print(f'✅ {fonksiyon_adi}() imzasi: {{sig}}')\n    except Exception as e:\n        print(f'Test: {{e}}')\n"

            with open(test_dosya, "w") as f:
                f.write(test_kod)

            result = subprocess.run(
                ["python3.11", test_dosya],
                capture_output=True, text=True, timeout=15
            )

            if result.returncode == 0:
                # Kalite kontrol
                try:
                    tree2 = ast.parse(kod)
                    func_node = None
                    for n in ast.walk(tree2):
                        if isinstance(n, ast.FunctionDef) and n.name == fonksiyon_adi:
                            func_node = n
                            break

                    has_docstring = False
                    has_try = False
                    if func_node and func_node.body:
                        first = func_node.body[0]
                        if (isinstance(first, ast.Expr) and
                            isinstance(first.value, ast.Constant) and
                            isinstance(first.value.value, str) and
                            len(first.value.value) > 20):
                            has_docstring = True
                        for n in ast.walk(func_node):
                            if isinstance(n, ast.Try):
                                has_try = True
                                break

                    if not has_docstring:
                        # Docstring ekle
                        doc = f'    """{aciklama[:80]}\n\n    Parametreler: otomatik\n    Donus: dict veya str\n    """\n    '
                        lines = kod.split("\n")
                        # def satırından sonraki ilk satıra docstring ekle
                        for i, line in enumerate(lines):
                            if line.strip().startswith("def ") and ":" in line:
                                indent = len(line) - len(line.lstrip())
                                doc_indent = " " * (indent + 4)
                                doc_lines = f'"""{aciklama[:100]}"""'.split("\n")
                                insert_idx = i + 1
                                for dl in reversed(doc_lines):
                                    lines.insert(insert_idx, doc_indent + dl)
                                kod = "\n".join(lines)
                                break
                except:
                    pass

                # tools.py'ye ekle
                if _tools_ekle(kod, kategori):
                    mesaj = f"✅ Eklendi: {fonksiyon_adi}() — {aciklama[:60]}"
                    _evolve_log_ekle({
                        "tur": "ekleme",
                        "fonksiyon": fonksiyon_adi,
                        "aciklama": aciklama,
                        "kategori": kategori,
                        "deneme": deneme
                    })
                    _telegram_gonder(f"🧬 self_evolve: {mesaj}")
                    return {"durum": "ok", "mesaj": mesaj, "kod": kod}
                else:
                    return {"durum": "hata", "mesaj": "❌ tools.py'ye eklenemedi"}

            else:
                hata = result.stderr[:1000] or result.stdout[:1000]
                if deneme < MAX_FIX_ATTEMPTS:
                    # Düzeltme prompt'u
                    payload["messages"].append({"role": "assistant", "content": kod})
                    payload["messages"].append({
                        "role": "user",
                        "content": f"Yukarıdaki kod şu hatayı verdi:\n{hata}\n\nDüzeltilmiş kodu yaz (sadece kod, açıklama yok):"
                    })
                    payload["temperature"] = 0.2  # Daha konservatif
                else:
                    _log_hata("self_evolve", f"{fonksiyon_adi} başarısız ({deneme} deneme): {hata}",
                              "Manuel düzelt veya farklı bir yaklaşım dene")
                    return {"durum": "hata", "mesaj": f"❌ {fonksiyon_adi} başarısız ({MAX_FIX_ATTEMPTS} deneme)", "hata": hata}

        except Exception as e:
            return {"durum": "hata", "mesaj": f"❌ LLM hatası: {str(e)}"}

    return {"durum": "hata", "mesaj": "❌ Maksimum deneme aşıldı"}


# ─────────────────────────────────────────────
# 4. FIX: HATALI FONKSİYON DÜZELTME
# ─────────────────────────────────────────────

def hata_coz(fonksiyon_adi, hata_mesaji):
    """
    Hata veren bir fonksiyonu DeepSeek'e gönderip düzeltme dener.
    Eski kodu yedekler, düzeltilmiş kodu test edip tools.py'ye yazar.

    Parametreler:
        fonksiyon_adi: Düzeltilecek fonksiyon adı
        hata_mesaji: Alınan hata mesajı

    Dönüş: {"durum": "ok"|"hata", "mesaj": "..."}
    """
    content, tree = _tools_oku()
    if not content:
        return {"durum": "hata", "mesaj": "tools.py bulunamadı"}

    if tree is None:
        return {"durum": "hata", "mesaj": "tools.py syntax hatası var"}

    # AST'den fonksiyon kaynak kodunu bul
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == fonksiyon_adi:
            # Kaynak satırları al
            lines = content.split("\n")
            start = node.lineno - 1
            end = node.end_lineno
            eski_kod = "\n".join(lines[start:end])

            api_key = _api_key_al()
            if not api_key:
                return {"durum": "hata", "mesaj": "❌ API key yok"}

            prompt = f"""Şu Python fonksiyonu hata veriyor:

FONKSİYON:
{eski_kod}

HATA:
{hata_mesaji}

Düzeltilmiş fonksiyonu yaz. Sadece kod, açıklama yapma."""

            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Fix the Python function. Return ONLY the fixed code."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 2048
            }

            try:
                import requests as req
                resp = req.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json=payload,
                    timeout=90
                )
                data = resp.json()
                yeni_kod = data["choices"][0]["message"]["content"].strip()

                # Markdown temizle
                yeni_kod = re.sub(r"^```python\s*\n?", "", yeni_kod)
                yeni_kod = re.sub(r"^```\s*\n?", "", yeni_kod)
                yeni_kod = re.sub(r"\n?\s*```$", "", yeni_kod)
                yeni_kod = yeni_kod.strip()

                # Test et
                with open("/tmp/self_evolve_fix.py", "w") as f:
                    f.write(yeni_kod)

                result = subprocess.run(
                    ["python3.11", "-c", f"import ast; ast.parse('''{yeni_kod.replace(chr(39), chr(96))}''')"],
                    capture_output=True, text=True, timeout=10
                )

                if result.returncode == 0:
                    # tools.py'de eski kodu yenisiyle değiştir
                    yeni_lines = content.split("\n")
                    yeni_lines[start:end] = yeni_kod.split("\n")
                    _tools_yaz("\n".join(yeni_lines))

                    _evolve_log_ekle({
                        "tur": "duzeltme",
                        "fonksiyon": fonksiyon_adi,
                        "hata": hata_mesaji[:200]
                    })

                    mesaj = f"🔧 Düzeltildi: {fonksiyon_adi}() — hata giderildi"
                    _telegram_gonder(f"🧬 self_evolve: {mesaj}")
                    return {"durum": "ok", "mesaj": mesaj}
                else:
                    return {"durum": "hata", "mesaj": f"Düzeltme testi geçemedi: {result.stderr[:300]}"}

            except Exception as e:
                return {"durum": "hata", "mesaj": f"LLM hatası: {str(e)}"}

    return {"durum": "hata", "mesaj": f"{fonksiyon_adi} bulunamadı"}


# ─────────────────────────────────────────────
# 5. AUD: KOD KALİTE DENETİMİ
# ─────────────────────────────────────────────

def kod_denetle(fonksiyon_adi=None):
    """
    Belirli bir fonksiyonun veya tüm tools.py'nin kod kalitesini denetler.

    Parametreler:
        fonksiyon_adi: Sadece bu fonksiyonu denetle (None = tümü)

    Dönüş: str — insan okunabilir rapor
    """
    analiz = analiz_et()
    if "hata" in analiz:
        return f"❌ {analiz['hata']}"

    rapor = []
    rapor.append("═══════════════════════════════════════")
    rapor.append("  🔍 KOD KALİTE DENETİMİ")
    rapor.append(f"  Tarih: {datetime.datetime.now().strftime('%d %B %Y %H:%M')}")
    rapor.append(f"  Genel Skor: {analiz['genel_skor']}/1.0")
    rapor.append("═══════════════════════════════════════\n")

    # Kategoriler
    rapor.append(f"📦 Kategoriler: {len(analiz['kategoriler']['var'])} mevcut, {len(analiz['kategoriler']['eksik'])} eksik")
    if analiz['kategoriler']['eksik']:
        rapor.append(f"   Eksik: {', '.join(analiz['kategoriler']['eksik'])}")

    rapor.append("")
    rapor.append(f"{'Fonksiyon':<25} {'Skor':<8} {'Satır':<6} {'Durum':<15}")
    rapor.append("-" * 55)

    for f in analiz['fonksiyonlar']:
        if fonksiyon_adi and f['ad'] != fonksiyon_adi:
            continue

        skor = f['kalite_skor']
        if skor >= 0.8:
            durum = "✅ İYİ"
        elif skor >= 0.5:
            durum = "⚠️ ORTA"
        else:
            durum = "❌ KÖTÜ"

        rapor.append(f"{f['ad']:<25} {skor:<8} {f['satir_sayisi']:<6} {durum:<15}")

    # En kötü 3
    sirali = sorted(analiz['fonksiyonlar'], key=lambda x: x['kalite_skor'])
    kotuler = [f for f in sirali if f['kalite_skor'] < SCORE_THRESHOLD][:3]
    if kotuler:
        rapor.append("")
        rapor.append("🔧 İyileştirilmesi gerekenler:")
        for f in kotuler:
            rapor.append(f"   • {f['ad']}() — skor {f['kalite_skor']}: {', '.join(f['sorunlar'])}")

    return "\n".join(rapor)


# ─────────────────────────────────────────────
# 6. CHG: DEĞİŞİKLİK GEÇMİŞİ
# ─────────────────────────────────────────────

def degisiklik_gecmisi(limit=10):
    """Son N değişikliği gösterir."""
    if not os.path.exists(EVOLVE_LOG):
        return "Henüz değişiklik yok."

    try:
        with open(EVOLVE_LOG, "r") as f:
            log = json.load(f)
    except:
        return "Log okunamadı."

    if not log:
        return "Henüz değişiklik yok."

    rapor = []
    rapor.append("📜 **Değişiklik Geçmişi**\n")
    for entry in log[-limit:]:
        ts = entry.get("timestamp", "")[:16]
        tur = entry.get("tur", "?")
        fonk = entry.get("fonksiyon", "?")
        acik = entry.get("aciklama", entry.get("hata", ""))[:60]
        ikon = {"ekleme": "➕", "duzeltme": "🔧", "silme": "🗑️", "güncelleme": "🔄"}.get(tur, "•")
        rapor.append(f"{ikon} [{ts}] {fonk} — {acik}")

    return "\n".join(rapor)


# ─────────────────────────────────────────────
# 7. PRN: TEMİZLİK ÖNERİSİ
# ─────────────────────────────────────────────

def temizlik_oner():
    """
    Kullanılmayan, eski veya gereksiz fonksiyonları tespit eder.
    (Henüz kullanım analizi yok, AST tabanlı basit analiz)
    """
    analiz = analiz_et()
    if "hata" in analiz:
        return f"❌ {analiz['hata']}"

    oneriler = []

    # Çok kısa ve düşük kaliteli fonksiyonlar
    cok_kotu = [f for f in analiz['fonksiyonlar']
                if f['kalite_skor'] < 0.3 and f['satir_sayisi'] < 5]
    if cok_kotu:
        oneriler.append("🗑️ Silinebilir (çok kısa/düşük kalite):")
        for f in cok_kotu:
            oneriler.append(f"   • {f['ad']}() — {f['satir_sayisi']} satır, skor {f['kalite_skor']}")

    # Eksik kategoriler
    if analiz['kategoriler']['eksik']:
        oneriler.append("\n📦 Eklenmesi gereken kategoriler:")
        for kat in analiz['kategoriler']['eksik']:
            oneriler.append(f"   ➕ {kat}")

    if not oneriler:
        oneriler.append("✅ Temizlik gerektiren bir durum yok.")

    return "\n".join(oneriler)


# ─────────────────────────────────────────────
# ANA ÇALIŞTIRMA
# ─────────────────────────────────────────────

def otonom_taram():
    """
    Otomatik tarama — cron'dan çağrılır.
    1. tools.py'yi analiz et
    2. Eksik/hatalı bir şey varsa Telegram'a bildir
    3. Kritikse otomatik düzelt

    Dönüş: str — özet rapor
    """
    rapor = []
    rapor.append(f"🧬 self_evolve taraması — {datetime.datetime.now().strftime('%d %B %H:%M')}")
    rapor.append("")

    analiz = analiz_et()
    if "hata" in analiz:
        return f"❌ Analiz hatası: {analiz['hata']}"

    rapor.append(f"📊 Genel skor: {analiz['genel_skor']}/1.0 ({len(analiz['fonksiyonlar'])} fonksiyon)")

    # Düşük kalite kontrol
    dusuk = [f for f in analiz['fonksiyonlar'] if f['kalite_skor'] < SCORE_THRESHOLD]
    if dusuk:
        rapor.append(f"\n⚠️ {len(dusuk)} fonksiyon düşük kaliteli:")
        for f in dusuk[:3]:
            rapor.append(f"   • {f['ad']}() — skor {f['kalite_skor']}")
        if len(dusuk) > 3:
            rapor.append(f"   ... ve {len(dusuk)-3} daha")

    # Eksik kategoriler
    if analiz['kategoriler']['eksik']:
        rapor.append(f"\n📦 Eksik kategoriler: {', '.join(analiz['kategoriler']['eksik'])}")

    rapor.append("")
    if analiz['genel_skor'] < 0.5:
        rapor.append("🔴 KRİTİK: İyileştirme gerekli!")
        _telegram_gonder("🧬 self_evolve: KRİTİK — tools.py kalite skoru çok düşük!")
    elif analiz['genel_skor'] < 0.7:
        rapor.append("🟡 ORTA: Belirli fonksiyonlar iyileştirilmeli")
    else:
        rapor.append("🟢 İYİ: Genel durum sağlıklı")

    return "\n".join(rapor)


# ─────────────────────────────────────────────
# KOMMUT SATIRI
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    komutlar = {
        "analiz": lambda: print(json.dumps(analiz_et(), indent=2, ensure_ascii=False)),
        "ne_eklemeliyim": lambda: print(ne_eklemeliyim()),
        "uretim": lambda: print(json.dumps(
            kod_uret(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None),
            indent=2, ensure_ascii=False
        )),
        "fix": lambda: print(json.dumps(
            hata_coz(sys.argv[2], sys.argv[3]),
            indent=2, ensure_ascii=False
        )),
        "denetle": lambda: print(kod_denetle(sys.argv[2] if len(sys.argv) > 2 else None)),
        "gecmis": lambda: print(degisiklik_gecmisi()),
        "temizlik": lambda: print(temizlik_oner()),
        "oto": lambda: print(otonom_taram()),
    }

    if len(sys.argv) < 2:
        print("Kullanım: python3 self_evolve.py <komut> [args]")
        print("Komutlar:")
        for k in komutlar:
            print(f"  {k}")
        sys.exit(1)

    komut = sys.argv[1]
    if komut in komutlar:
        komutlar[komut]()
    else:
        print(f"Bilinmeyen komut: {komut}")
        print(f"Kullanılabilir: {', '.join(komutlar.keys())}")
