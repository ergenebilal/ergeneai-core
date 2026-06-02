"""
test_tools_phase3.py — Phase 3: Chrome emekli, Session, Beyin Wrapper, Kalan Hermes.

Test edilen fonksiyonlar (14):
  - bilal_notes_ara / dosya_ekle / otonom_calistir  (ChromaDB emekli, graceful failure)
  - session_hatirla / session_al / plan_hedef         (session + plan motoru)
  - beyin_ara / beyin_kaydet                          (pg wrapper)
  - hermes_proaktif_brifing / hermes_hafiza_kalite_raporu
  - hermes_karar_plani / hermes_oncelik_motoru
  - get_longtracer_model                               (internal helper)
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

TOOLS_PATH = Path(__file__).resolve().parents[1] / "tools.py"


# ===========================================================================
# INTERNAL HELPERS
# ===========================================================================

class TestInternalHelpers:
    """get_longtracer_model — internal singleton helper."""

    def test_get_longtracer_model_returns_object_or_none(self):
        """get_longtracer_model ya model ya da None dönmeli."""
        import tools
        result = tools.get_longtracer_model()
        # Her iki durum da geçerli: longtracer kuruluysa model, değilse None
        assert result is None or hasattr(result, "check")

    def test_get_longtracer_model_caches_result(self):
        """İkinci çağrıda aynı nesneyi dönmeli (singleton)."""
        import tools
        # Reset
        tools._longtracer_model = None
        first = tools.get_longtracer_model()
        second = tools.get_longtracer_model()
        assert first is second or (first is None and second is None)


# ===========================================================================
# CHROMADB EMEKLİ — graceful failure testleri
# ===========================================================================

class TestChromaDeprecated:
    """ChromaDB emekli — fonksiyonlar hata mesajı dönmeli, çökmemeli."""

    def test_bilal_notes_ara_returns_list_on_failure(self):
        """Chroma çalışmıyorken bile liste dönmeli."""
        import tools
        result = tools.bilal_notes_ara("test")
        assert isinstance(result, list)
        # Chroma bağlantı hatası mesajı dönmeli
        if result and isinstance(result[0], str):
            assert "hata" in result[0].lower() or "Hata" in result[0]

    def test_bilal_notes_ara_connection_refused(self):
        """Port 8001 kapalıyken hata mesajı dönmeli."""
        import tools
        with patch("tools.chromadb.HttpClient", side_effect=Exception("Bağlantı reddedildi")):
            result = tools.bilal_notes_ara("test")
            assert isinstance(result, list)
            assert len(result) > 0
            assert "hata" in result[0].lower() or "Hata" in result[0]

    def test_bilal_notes_ara_collection_not_found(self):
        """Koleksiyon yoksa hata dönmeli."""
        import tools
        mock_client = MagicMock()
        mock_client.get_collection.side_effect = Exception("bulunamadı")
        with patch("tools.chromadb.HttpClient", return_value=mock_client):
            result = tools.bilal_notes_ara("test")
            assert isinstance(result, list)
            assert "hata" in result[0].lower() or "Hata" in result[0]

    def test_dosya_ekle_returns_string_on_failure(self):
        """Chroma çalışmıyorken string dönmeli (hata mesajı)."""
        import tools
        result = tools.dosya_ekle("/tmp/test.txt")
        assert isinstance(result, str)
        # Chroma bağlantı hatası ❌ ile başlamalı
        assert "❌" in result or "hata" in result.lower() or "Hata" in result

    def test_dosya_ekle_nonexistent_file(self):
        """Var olmayan dosya için hata dönmeli."""
        import tools
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_collection.return_value = mock_collection
        with patch("tools.chromadb.HttpClient", return_value=mock_client):
            result = tools.dosya_ekle("/tmp/nonexistent_file_xyz.txt")
            assert isinstance(result, str)
            assert "❌" in result or "hata" in result.lower()

    def test_otonom_calistir_returns_dict(self):
        """otonom_calistir her koşulda dict dönmeli (hata bile olsa)."""
        import tools
        result = tools.otonom_calistir("test hedef")
        assert isinstance(result, dict)

    def test_otonom_calistir_with_mock_fail(self):
        """bilal_notes_ara hata verince uygun dict dönmeli."""
        import tools
        with patch("tools.bilal_notes_ara", return_value=[]):
            result = tools.otonom_calistir("test")
            assert isinstance(result, dict)
            # Boş sonuç durumunda "sonuc yok" mesajı veya hata
            if "arama_sonucu" in result:
                assert result["arama_sonucu"] == []
            else:
                assert "hata" in str(result).lower() or "Hata" in str(result)

    def test_otonom_calistir_full_stack_mock(self):
        """Tüm zincir mock ile çalışmalı."""
        import tools
        with patch("tools.bilal_notes_ara", return_value=["sonuç 1"]), \
             patch("tools.verify_claim", return_value={"verdict": "PASS", "confidence": 0.9}), \
             patch("tools.suan", return_value={"tarih": "2026-06-02", "saat": "10:00", "gun": "Salı"}):
            result = tools.otonom_calistir("test")
            assert isinstance(result, dict)
            assert "arama_sonucu" in result
            assert "dogrulama" in result


# ===========================================================================
# SESSION & PLAN
# ===========================================================================

class TestSessionMemory:
    """session_hatirla ve session_al — geçici oturum hafızası."""

    def setup_method(self):
        """Her test öncesi session'ı temizle."""
        import tools
        tools._session_memory.clear()

    def test_session_hatirla_returns_list(self):
        """session_hatirla liste dönmeli."""
        import tools
        result = tools.session_hatirla("test mesaj")
        assert isinstance(result, list)

    def test_session_hatirla_adds_and_returns(self):
        """Mesaj eklenince listede görünmeli."""
        import tools
        result = tools.session_hatirla("ilk mesaj")
        assert "ilk mesaj" in result

    def test_session_hatirla_limits_to_last_5(self):
        """5'ten fazla mesajda son 5'i dönmeli."""
        import tools
        for i in range(10):
            tools.session_hatirla(f"Mesaj {i}")
        result = tools.session_hatirla("son mesaj")
        assert len(result) <= 5
        assert "son mesaj" in result
        assert "Mesaj 0" not in result  # ilk mesaj silinmiş olmalı

    def test_session_al_returns_list(self):
        """session_al liste dönmeli."""
        import tools
        result = tools.session_al()
        assert isinstance(result, list)

    def test_session_al_returns_all(self):
        """session_al tüm mesajları dönmeli."""
        import tools
        tools.session_hatirla("bir")
        tools.session_hatirla("iki")
        tools.session_hatirla("üç")
        result = tools.session_al()
        assert len(result) >= 3

    def test_session_empty_initially(self):
        """İlk açılışta session boş olmalı."""
        import tools
        with patch.object(tools, "_session_memory", []):
            result = tools.session_al()
            assert isinstance(result, list)
            assert len(result) == 0


class TestPlanHedef:
    """plan_hedef — hedef kelimesine göre plan döndürme."""

    def test_plan_hedef_returns_dict(self):
        """plan_hedef dict dönmeli."""
        import tools
        result = tools.plan_hedef("araştırma yap")
        assert isinstance(result, dict)

    def test_plan_hedef_arastirma(self):
        """'araştır' kelimesi içeren hedef araştırma planı dönmeli."""
        import tools
        result = tools.plan_hedef("piyasa araştırması")
        assert "adimlar" in result
        assert "bilal_notes_ara" in str(result["adimlar"])

    def test_plan_hedef_kurulum(self):
        """'kurulum' kelimesi kurulum planı dönmeli."""
        import tools
        result = tools.plan_hedef("sistem kurulumu yap")
        assert "adimlar" in result
        assert "check_system_status" in str(result["adimlar"])

    def test_plan_hedef_rapor(self):
        """'rapor' kelimesi rapor planı dönmeli."""
        import tools
        result = tools.plan_hedef("durum raporu hazırla")
        assert "adimlar" in result
        assert "get_hata_gecmisi" in str(result["adimlar"])

    def test_plan_hedef_kod(self):
        """'kod' kelimesi kod planı dönmeli."""
        import tools
        result = tools.plan_hedef("python kodu yaz")
        assert "adimlar" in result
        assert "terminal_calistir" in str(result["adimlar"])

    def test_plan_hedef_web(self):
        """'web' kelimesi web planı dönmeli."""
        import tools
        result = tools.plan_hedef("web sayfası çek")
        assert "adimlar" in result
        assert "web_cek" in str(result["adimlar"])

    def test_plan_hedef_default(self):
        """Bilinmeyen hedef genel plan dönmeli."""
        import tools
        result = tools.plan_hedef("bilinmeyen bir hedef")
        assert "adimlar" in result
        # Default: genel araştırma
        assert len(result["adimlar"]) >= 2

    def test_plan_hedef_case_insensitive(self):
        """Büyük/küçük harf duyarsız çalışmalı."""
        import tools
        result = tools.plan_hedef("KURULUM YAP")
        assert "check_system_status" in str(result["adimlar"])


# ===========================================================================
# BEYİN WRAPPER (pg wrapper'lar)
# ===========================================================================

class TestBrainWrappers:
    """beyin_ara ve beyin_kaydet — pg_ara_vector/pg_kaydet wrapper'ları."""

    def test_beyin_ara_returns_list(self):
        """beyin_ara liste dönmeli."""
        import tools
        result = tools.beyin_ara("test sorgu")
        assert isinstance(result, list)

    def test_beyin_ara_delegates_to_pg_ara_vector(self):
        """beyin_ara pg_ara_vector'ü çağırmalı."""
        import tools
        with patch("tools.pg_ara_vector", return_value=[{"content": "sonuç"}]) as mock:
            result = tools.beyin_ara("test")
            mock.assert_called_once()
            assert "sonuç" in result

    def test_beyin_ara_empty_results(self):
        """Hiç sonuç yoksa default mesaj dönmeli."""
        import tools
        with patch("tools.pg_ara_vector", return_value=[]):
            result = tools.beyin_ara("test")
            assert isinstance(result, list)
            # Boş sonuç veya fallback mesajı
            if len(result) == 0:
                assert True
            elif result[0]:
                assert "bulunamadı" in result[0].lower() or "sonuç" in result[0].lower()

    def test_beyin_ara_return_strings(self):
        """beyin_ara string listesi dönmeli."""
        import tools
        with patch("tools.pg_ara_vector", return_value=[
            {"content": "sonuç 1"}, {"content": "sonuç 2"}
        ]):
            result = tools.beyin_ara("test")
            assert isinstance(result, list)
            for r in result:
                assert isinstance(r, str)

    def test_beyin_kaydet_returns_string(self):
        """beyin_kaydet string dönmeli."""
        import tools
        result = tools.beyin_kaydet("test bilgi", tur="test")
        assert isinstance(result, str)

    def test_beyin_kaydet_delegates_to_pg_kaydet(self):
        """beyin_kaydet pg_kaydet'i çağırmalı."""
        import tools
        with patch("tools.pg_kaydet", return_value="✅ Kaydedildi") as mock:
            result = tools.beyin_kaydet("test", tur="genel")
            mock.assert_called_once_with("test", category="genel")

    def test_beyin_kaydet_with_etiket(self):
        """etiket parametresi çalışmalı (PG'de kullanılmaz ama hata vermemeli)."""
        import tools
        with patch("tools.pg_kaydet", return_value="✅ Kaydedildi"):
            result = tools.beyin_kaydet("test", tur="genel", etiket="önemli")
            assert isinstance(result, str)

    def test_beyin_kaydet_exception_returns_error_string(self):
        """PG hatasında hata stringi dönmeli."""
        import tools
        with patch("tools.pg_kaydet", side_effect=Exception("PG bağlantı hatası")):
            result = tools.beyin_kaydet("test")
            assert isinstance(result, str)
            assert "hata" in result.lower() or "Hata" in result


# ===========================================================================
# HERMES KALAN WRAPPER'LAR (hermes_brain_core delegasyonu)
# ===========================================================================

class TestHermesRemainingWrappers:
    """hermes_proaktif_brifing, hermes_hafiza_kalite_raporu, hermes_karar_plani, hermes_oncelik_motoru."""

    def test_hermes_proaktif_brifing_returns_dict(self):
        """hermes_proaktif_brifing dict dönmeli."""
        import tools
        try:
            result = tools.hermes_proaktif_brifing(mod="sabah")
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("hermes_brain_core modülü import edilemedi — test atlandı")

    def test_hermes_proaktif_brifing_aksam(self):
        """Akşam modu da çalışmalı."""
        import tools
        try:
            result = tools.hermes_proaktif_brifing(mod="aksam")
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("hermes_brain_core modülü import edilemedi — test atlandı")

    def test_hermes_hafiza_kalite_raporu_returns_dict(self):
        """hermes_hafiza_kalite_raporu dict dönmeli."""
        import tools
        try:
            result = tools.hermes_hafiza_kalite_raporu()
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("hermes_brain_core modülü import edilemedi — test atlandı")

    def test_hermes_hafiza_kalite_raporu_with_limit(self):
        """Limit parametresiyle çalışmalı."""
        import tools
        try:
            result = tools.hermes_hafiza_kalite_raporu(limit=50)
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("hermes_brain_core modülü import edilemedi — test atlandı")

    def test_hermes_karar_plani_returns_dict(self):
        """hermes_karar_plani dict dönmeli."""
        import tools
        try:
            result = tools.hermes_karar_plani(
                ["Denizbank ödemesi", "Müşteri ziyareti", "Demo hazırlığı"],
                baglam={"acil": "Denizbank"}
            )
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("hermes_brain_core modülü import edilemedi — test atlandı")

    def test_hermes_karar_plani_no_context(self):
        """Baglamsız da çalışmalı."""
        import tools
        try:
            result = tools.hermes_karar_plani(["A görevi", "B görevi"])
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("hermes_brain_core modülü import edilemedi — test atlandı")

    def test_hermes_oncelik_motoru_returns_dict(self):
        """hermes_oncelik_motoru dict dönmeli."""
        import tools
        try:
            result = tools.hermes_oncelik_motoru(
                {"gorevler": ["test1", "test2"]},
                baglam={"kaynak": "test"}
            )
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("hermes_brain_core modülü import edilemedi — test atlandı")

    def test_hermes_oncelik_motoru_with_date(self):
        """Tarih parametresiyle çalışmalı."""
        import tools
        try:
            result = tools.hermes_oncelik_motoru(
                {"gorevler": ["test"]},
                referans_tarih="2026-06-05",
                baglam={"kaynak": "test"}
            )
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("hermes_brain_core modülü import edilemedi — test atlandı")


# ===========================================================================
# DISCOVERY — Phase 3 kapsamı
# ===========================================================================

def test_phase3_functions_exist():
    """Phase 3'te test edilen tüm fonksiyonlar tools.py'de var mı."""
    import ast
    tree = ast.parse(TOOLS_PATH.read_text(encoding="utf-8"))
    fnames = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    expected = {
        "get_longtracer_model",
        "bilal_notes_ara", "dosya_ekle", "otonom_calistir",
        "session_hatirla", "session_al", "plan_hedef",
        "beyin_ara", "beyin_kaydet",
        "hermes_proaktif_brifing", "hermes_hafiza_kalite_raporu",
        "hermes_karar_plani", "hermes_oncelik_motoru",
    }
    missing = expected - fnames
    assert not missing, f"Eksik fonksiyonlar: {missing}"
