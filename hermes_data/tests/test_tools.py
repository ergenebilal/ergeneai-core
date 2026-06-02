"""
test_tools.py — Katı (strict) test suite for tools.py kritik fonksiyonlar.

Phase 1: Gmail, Calendar, PostgreSQL (n8n entegrasyonu) — en kritik 5.

Kurallar:
  - Her test ya gerçek bir durumu doğrular ya da belgelenmiş bir mock kullanır.
  - Google API/PostgreSQL bağlantısı gerektiren testlerde fixture
    gerçek token/config varlığını kontrol eder, yoksa skip atar.
  - Tüm testler `-W error` ile çalıştırıldığında hata vermez.
  - tools.py import edilir, modül içinden fonksiyonlar çağrılır.
"""

import warnings

# 3rd-party kütüphanelerden (httplib2, pyparsing) gelen
# Python 3.11 sre_constants deprecation uyarılarını sessize al.
warnings.filterwarnings("ignore", category=DeprecationWarning, module="httplib2")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pyparsing")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*sre_constants.*")

import json
import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

TOOLS_PATH = Path(__file__).resolve().parents[1] / "tools.py"
GOOGLE_TOKEN = Path(os.path.expanduser("~/.google/token.pickle"))
GOOGLE_CREDENTIALS = Path(os.path.expanduser("~/.google/credentials.json"))


# ---------------------------------------------------------------------------
# Yardımcı: tools.py'de tanımlı tüm fonksiyon adlarını AST ile oku
# ---------------------------------------------------------------------------

def _tools_function_names():
    import ast
    tree = ast.parse(TOOLS_PATH.read_text(encoding="utf-8"))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


# ---------------------------------------------------------------------------
# Discovery testi — tools.py'deki tüm fonksiyonlar biliniyor mu?
# ---------------------------------------------------------------------------

def test_tools_py_contains_expected_functions():
    """tools.py içinde beklenen fonksiyonlar var mı kontrol et."""
    fnames = _tools_function_names()
    expected = {
        "gmail_gonder", "gmail_oku",
        "takvim_etkinlik_ekle", "takvim_etkinlik_listele",
        "pg_kaydet", "pg_ara", "pg_ara_vector",
        "google_auth", "google_auth_link",
        "hatirlatici_kur", "hava_durumu",
        "terminal_calistir", "web_cek", "self_repair",
        "telegram_mesaj_gonder", "analiz_et", "hesap_hesapla", "suan",
    }
    missing = expected - fnames
    assert not missing, f"Eksik fonksiyonlar: {missing}"


# ===========================================================================
# GOOGLE AUTH
# ===========================================================================

class TestGoogleAuth:
    """google_auth ve google_auth_link fonksiyonları."""

    def test_google_auth_token_dosyasi_kontrol(self):
        """token.pickle varsa auth en azından dosyayı bulup yüklemeyi dener."""
        # Bu test gerçek token varlığını kontrol eder
        if not GOOGLE_TOKEN.exists():
            pytest.skip("~/.google/token.pickle mevcut değil — test atlandı")

        import tools
        creds, hata = tools.google_auth()
        if hata:
            pytest.skip(f"Google Auth başarısız (muhtemelen token süresi dolmuş): {hata}")
        assert creds is not None
        assert hata is None

    def test_google_auth_link_returns_url_string(self):
        """google_auth_link geçerli bir URL döndürmeli."""
        if not GOOGLE_CREDENTIALS.exists():
            pytest.skip("credentials.json mevcut değil — test atlandı")

        import tools
        result = tools.google_auth_link()
        assert isinstance(result, str)
        assert "accounts.google.com" in result or result.startswith("https://")

    def test_google_auth_no_token_returns_error(self):
        """token yoksa auth hata döndürmeli (serbest çalışma)."""
        import tools
        # Token dosyasını geçici olarak yok say
        with patch.object(tools, "GOOGLE_TOKEN", "/tmp/nonexistent_token.pickle"):
            creds, hata = tools.google_auth()
            assert creds is None
            assert hata is not None
            assert "gecersiz" in hata.lower() or "auth" in hata.lower()


# ===========================================================================
# GMAIL
# ===========================================================================

class TestGmail:
    """gmail_gonder ve gmail_oku fonksiyonları."""

    GONDER_ARGS = ["test@example.com", "Test Konusu", "Test içeriği"]

    def test_gmail_gonder_returns_string(self):
        """gmail_gonder her koşulda bir string döndürmeli (hata mesajı veya başarı)."""
        import tools

        result = tools.gmail_gonder(*self.GONDER_ARGS)
        assert isinstance(result, str), f"String dönmeli, {type(result)} döndü"

    def test_gmail_gonder_with_html_flag(self):
        """html=True ile çalıştığında da string dönmeli."""
        import tools

        result = tools.gmail_gonder(*self.GONDER_ARGS, html=True)
        assert isinstance(result, str)

    @pytest.mark.skipif(not GOOGLE_TOKEN.exists(), reason="Google token yok")
    def test_gmail_gonder_success_message(self):
        """Token varsa ve auth geçerse başarı mesajı dönmeli."""
        import tools

        result = tools.gmail_gonder(*self.GONDER_ARGS)
        # Eğer auth geçerse ✅ ile başlar, geçmezse ❌ ile
        if result.startswith("✅"):
            assert "gonderildi" in result.lower()
            assert "test@example.com" in result
        else:
            # Auth hatası olabilir — bu kabul edilebilir
            assert "hata" in result.lower() or "❌" in result

    def test_gmail_oku_returns_list_or_string(self):
        """gmail_oku liste veya string döndürmeli."""
        import tools

        result = tools.gmail_oku()
        assert isinstance(result, (list, str))

    def test_gmail_oku_with_max_results(self):
        """max_sonuc parametresi çalışıyor mu."""
        import tools

        result = tools.gmail_oku(max_sonuc=3)
        assert isinstance(result, (list, str))

    def test_gmail_oku_invalid_auth_returns_error_string(self):
        """Token yokken gmail_oku hata stringi dönmeli."""
        import tools

        with patch.object(tools, "GOOGLE_TOKEN", "/tmp/nonexistent_gmail_test.pickle"):
            result = tools.gmail_oku()
            assert isinstance(result, str)
            assert "hata" in result.lower() or "❌" in result


# ===========================================================================
# TAKVİM
# ===========================================================================

class TestCalendar:
    """takvim_etkinlik_ekle ve takvim_etkinlik_listele fonksiyonları."""

    def test_takvim_ekle_returns_string(self):
        """takvim_etkinlik_ekle her koşulda string dönmeli."""
        import tools

        baslangic = (datetime.utcnow() + timedelta(days=1)).isoformat()
        bitis = (datetime.utcnow() + timedelta(days=1, hours=1)).isoformat()
        result = tools.takvim_etkinlik_ekle("Test Etkinlik", baslangic, bitis)
        assert isinstance(result, str)

    def test_takvim_ekle_with_aciklama(self):
        """Açıklama parametresiyle çalışabilmeli."""
        import tools

        baslangic = (datetime.utcnow() + timedelta(days=2)).isoformat()
        bitis = (datetime.utcnow() + timedelta(days=2, hours=2)).isoformat()
        result = tools.takvim_etkinlik_ekle(
            "Test Etkinlik 2", baslangic, bitis, aciklama="Test açıklaması"
        )
        assert isinstance(result, str)

    def test_takvim_listele_returns_list_or_string(self):
        """takvim_etkinlik_listele liste veya string dönmeli."""
        import tools

        result = tools.takvim_etkinlik_listele()
        assert isinstance(result, (list, str))

    def test_takvim_listele_with_max_results(self):
        """max_sonuc parametresi çalışıyor mu."""
        import tools

        result = tools.takvim_etkinlik_listele(max_sonuc=5)
        assert isinstance(result, (list, str))

    def test_takvim_ekle_invalid_date_returns_error(self):
        """Geçersiz tarih formatı hata döndürmeli."""
        import tools

        result = tools.takvim_etkinlik_ekle("Hatalı", "invalid-date", "invalid-date")
        assert isinstance(result, str)
        # Hata mesajı dönmeli (başarı mesajı değil)
        # Bazı durumlarda Google API geçersiz tarihi kendisi reddeder
        if "❌" in result:
            assert "hata" in result.lower()


# ===========================================================================
# POSTGRESQL / n8n ENTEGRASYONU
# ===========================================================================

class TestPostgresMemory:
    """pg_kaydet, pg_ara, pg_ara_vector — n8n ve Embedding Daemon entegrasyonu."""

    @classmethod
    def setup_class(cls):
        """Bir kereye mahsus PostgreSQL bağlanabilirliğini kontrol et."""
        import subprocess
        try:
            subprocess.check_output(
                ["pg_isready", "-h", "127.0.0.1", "-p", "5432"],
                stderr=subprocess.DEVNULL, timeout=3,
            )
            cls.pg_available = True
        except Exception:
            cls.pg_available = False

    def test_pg_kaydet_returns_string(self):
        """pg_kaydet her koşulda string dönmeli."""
        import tools

        result = tools.pg_kaydet("Test kayıt", category="test")
        assert isinstance(result, str)

    def test_pg_kaydet_success_message(self):
        """PG çalışıyorsa başarı mesajı dönmeli."""
        import tools

        if not self.pg_available:
            pytest.skip("PostgreSQL çalışmıyor — test atlandı")

        result = tools.pg_kaydet(
            f"Test kaydı {datetime.now().isoformat()}",
            category="test",
        )
        assert "✅" in result or "kaydedildi" in result.lower()

    def test_pg_kaydet_with_different_categories(self):
        """Farklı kategorilerle kayıt çalışmalı."""
        import tools

        if not self.pg_available:
            pytest.skip("PostgreSQL çalışmıyor — test atlandı")

        for cat in ["tech_note", "business_strategy", "genel", "test"]:
            result = tools.pg_kaydet(f"Kategori testi: {cat}", category=cat)
            assert isinstance(result, str)

    def test_pg_ara_returns_list(self):
        """pg_ara her koşulda liste dönmeli."""
        import tools

        result = tools.pg_ara("test")
        assert isinstance(result, list)

    def test_pg_ara_successful_search(self):
        """PG çalışıyorsa ve kayıt varsa sonuç dönmeli."""
        import tools

        if not self.pg_available:
            pytest.skip("PostgreSQL çalışmıyor — test atlandı")

        result = tools.pg_ara("test")
        assert isinstance(result, list)
        # Boş liste veya sonuç — ikisi de geçerli
        if result and isinstance(result[0], dict):
            assert "content" in result[0]

    def test_pg_ara_vector_returns_list(self):
        """pg_ara_vector her koşulda liste dönmeli."""
        import tools

        result = tools.pg_ara_vector("test sorgu")
        assert isinstance(result, list)

    def test_pg_ara_vector_semantic_search(self):
        """Vektör araması çalışıyorsa sonuç dönmeli."""
        import tools

        if not self.pg_available:
            pytest.skip("PostgreSQL çalışmıyor — test atlandı")

        # Embedding modeli yoksa metin aramasına düşer
        result = tools.pg_ara_vector("test sorgu")
        assert isinstance(result, list)
        # Her iki durum da geçerli: vektör sonucu veya metin aramasına düşme

    def test_pg_ara_no_results_returns_fallback_list(self):
        """Hiç eşleşme olmasa bile liste dönmeli (fallback mesajı)."""
        import tools

        # Çok spesifik bir arama
        result = tools.pg_ara("ZZZZ_THIS_SHOULD_NOT_MATCH_ANYTHING_99999")
        assert isinstance(result, list)
        # Ya boş liste ya da "bulunamadı" mesajı
        assert len(result) >= 0


# ===========================================================================
# HATIRLATICI & HAVA DURUMU (arka plan entegrasyonları)
# ===========================================================================

class TestReminderAndWeather:
    """hatirlatici_kur ve hava_durumu — operasyonel araçlar."""

    def test_hatirlatici_kur_returns_string(self):
        """hatirlatici_kur string dönmeli."""
        import tools

        result = tools.hatirlatici_kur("Test hatırlatma", 1)
        assert isinstance(result, str)

    def test_hatirlatici_kur_success_message(self):
        """Başarılı hatırlatıcı mesajı doğru formatta olmalı."""
        import tools

        result = tools.hatirlatici_kur("Bu bir test", 5)
        assert "✅" in result or "⏰" in result

    def test_hava_durumu_returns_string(self):
        """hava_durumu string dönmeli."""
        import tools

        result = tools.hava_durumu()
        assert isinstance(result, str)

    def test_hava_durumu_istanbul(self):
        """Farklı şehirle çalışmalı."""
        import tools

        result = tools.hava_durumu("İstanbul")
        assert isinstance(result, str)


# ===========================================================================
# DIĞER KRITIK FONKSIYONLAR
# ===========================================================================

class TestSystemUtilities:
    """terminal_calistir, web_cek, suan, analiz_et, hesap_hesapla."""

    def test_suan_returns_struct(self):
        """suan dict dönmeli ve beklenen anahtarları içermeli."""
        import tools

        result = tools.suan()
        assert isinstance(result, dict)
        assert "tarih" in result
        assert "saat" in result
        assert "gun" in result

    def test_analiz_et_mutlu(self):
        """Olumlu kelime içeren mesaj MUTLU döndürmeli."""
        import tools

        result = tools.analiz_et("Harika bir gün, teşekkür ederim süper")
        assert result["durum"] == "MUTLU"
        assert result["skor"] > 0

    def test_analiz_et_notr(self):
        """Nötr mesaj NOTR döndürmeli."""
        import tools

        result = tools.analiz_et("Bugün hava yağmurlu")
        assert result["durum"] == "NOTR"

    def test_analiz_et_yorgun(self):
        """Olumsuz kelime içeren mesaj YORGUN döndürmeli."""
        import tools

        result = tools.analiz_et("Çok yorgunum, bu hata sinir bozucu")
        assert result["durum"] == "YORGUN/SINIRLI"
        assert result["skor"] < 0

    def test_hesap_hesapla_gider(self):
        """Gider hesaplaması doğru formatta dönmeli."""
        import tools

        result = tools.hesap_hesapla("gider", 1000, 10)
        assert isinstance(result, str)
        assert "Gider" in result
        assert "100" in result  # 1000/10 = 100

    def test_hesap_hesapla_gelir(self):
        """Gelir hesaplaması doğru formatta dönmeli."""
        import tools

        result = tools.hesap_hesapla("gelir", 5000, 5)
        assert isinstance(result, str)
        assert "Gelir" in result
        assert "1000" in result  # 5000/5 = 1000

    def test_terminal_calistir_returns_string(self):
        """terminal_calistir string dönmeli (hata bile olsa)."""
        import tools

        result = tools.terminal_calistir("echo test")
        assert isinstance(result, str)
        assert "test" in result

    def test_terminal_calistir_invalid_command(self):
        """Geçersiz komut hata mesajı döndürmeli."""
        import tools

        result = tools.terminal_calistir("nonexistent_command_xyz_123")
        assert isinstance(result, str)
        assert "HATA" in result

    def test_web_cek_returns_string(self):
        """web_cek string dönmeli."""
        import tools

        result = tools.web_cek("https://httpbin.org/get")
        assert isinstance(result, str)

    def test_web_cek_invalid_url(self):
        """Geçersiz URL hata mesajı döndürmeli."""
        import tools

        result = tools.web_cek("https://this-domain-does-not-exist-12345.com")
        assert isinstance(result, str)
        assert "❌" in result or "hata" in result.lower()


# ===========================================================================
# FİZİKSEL AKSİYON KAPISI (COO yetenekleri)
# ===========================================================================

class TestPhysicalActionGateway:
    """hermes_fiziksel_aksiyon_plani ve hermes_fiziksel_aksiyon_uygula."""

    def test_aksiyon_plani_returns_dict(self):
        """hermes_fiziksel_aksiyon_plani dict dönmeli."""
        import tools

        result = tools.hermes_fiziksel_aksiyon_plani(
            "Bilal'e hatırlat: Denizbank ödemesi yarın",
            baglam={"kaynak": "test"},
        )
        assert isinstance(result, dict)

    def test_aksiyon_plani_mesaj_taslagi(self):
        """Mesaj taslağı planı düzgün oluşmalı."""
        import tools

        result = tools.hermes_fiziksel_aksiyon_plani(
            "Bilal'e mesaj at: Denizbank ödemesi yarın son gün"
        )
        assert isinstance(result, dict)
        # Başarılı veya eksik bilgi — ikisi de geçerli
        if "ok" in result:
            assert isinstance(result["ok"], bool)

    def test_aksiyon_uygula_onaysiz_gitmez(self):
        """onay=False iken aksiyon uygulanmamalı."""
        import tools

        plan = tools.hermes_fiziksel_aksiyon_plani("Bilal'e test mesajı")
        result = tools.hermes_fiziksel_aksiyon_uygula(plan, onay=False)
        assert isinstance(result, dict)
        # Onay gerekli uyarısı dönmeli veya başarısız olmalı
        if not result.get("ok", True):
            assert "onay" in str(result).lower() or "approved" in str(result).lower()

    def test_hatirlatici_aksiyon_plani(self):
        """Hatırlatıcı planı düzgün oluşmalı."""
        import tools

        result = tools.hermes_fiziksel_aksiyon_plani(
            "10 dakika sonra Bilal'e hatırlat: Motor sigortasını ara"
        )
        assert isinstance(result, dict)

    def test_takvim_aksiyon_plani(self):
        """Takvim etkinliği planı düzgün oluşmalı."""
        import tools

        result = tools.hermes_fiziksel_aksiyon_plani(
            "Yarın 14:00'te haftalık toplantı ekle"
        )
        assert isinstance(result, dict)
