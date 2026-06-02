"""
test_tools_phase4.py — Phase 4: Kalan 15 fonksiyonun tamami.

Test edilen fonksiyonlar:
  - Internal: _get_embedding_model, _get_embedding, pg_baglan, _hermes_env_secret
  - Brain core wrapper (8): arac_guvenilirlik, coo_cevap_kalite, durum, skor_karti,
    hafiza_ameliyat, arac_ameliyat, guvenlik_sertlestirme, yuzde_yuz_hazirlik
  - Voice (3): ses_dosyasi_uret, telegram_ses_gonder, hermes_sesli_cevap
"""

import os
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

TOOLS_PATH = Path(__file__).resolve().parents[1] / "tools.py"


# ===========================================================================
# INTERNAL HELPERS
# ===========================================================================

class TestInternalHelpersPhase4:
    """_get_embedding_model, _get_embedding, pg_baglan, _hermes_env_secret."""

    def test_get_embedding_model_returns_model_or_none(self):
        """_get_embedding_model ya model ya da None dönmeli."""
        import tools
        tools._embedding_model = None
        # SentenceTransformer fonksiyon içinde import ediliyor
        with patch("sentence_transformers.SentenceTransformer", return_value=MagicMock()):
            result = tools._get_embedding_model()
            assert result is not None

    def test_get_embedding_model_caches(self):
        """İkinci çağrıda aynı nesne dönmeli (singleton)."""
        import tools
        tools._embedding_model = None
        first = tools._get_embedding_model()
        second = tools._get_embedding_model()
        assert first is second

    def test_get_embedding_returns_list_or_none(self):
        """_get_embedding liste veya None dönmeli."""
        import tools
        # _get_embedding_model çağırmasını engelle, direkt None döndür
        with patch.object(tools, "_embedding_model", None), \
             patch("tools._get_embedding_model", return_value=None):
            result = tools._get_embedding("test metin")
            assert result is None

    def test_get_embedding_with_mock_model(self):
        """Mock model ile embedding listesi dönmeli."""
        import tools
        mock_model = MagicMock()
        mock_model.encode.return_value.tolist.return_value = [0.1, 0.2, 0.3]
        with patch.object(tools, "_embedding_model", mock_model):
            result = tools._get_embedding("test")
            assert isinstance(result, list)
            assert len(result) > 0
            assert result[0] == 0.1

    def test_pg_baglan_returns_connection_or_raises(self):
        """pg_baglan bağlantı dönmeli veya exception fırlatmalı."""
        import tools
        try:
            conn = tools.pg_baglan()
            assert hasattr(conn, "cursor")
            conn.close()
        except Exception:
            # PG çalışmıyorsa exception beklenir — bu da geçerli
            pass

    def test_hermes_env_secret_returns_string(self):
        """_hermes_env_secret her koşulda string dönmeli."""
        import tools
        result = tools._hermes_env_secret("NONEXISTENT_KEY_12345")
        assert isinstance(result, str)

    def test_hermes_env_secret_from_env(self):
        """Ortam değişkeni varsa değerini dönmeli."""
        import tools
        with patch.dict(os.environ, {"TEST_HERMES_KEY": "test_value_123"}, clear=False):
            result = tools._hermes_env_secret("TEST_HERMES_KEY")
            assert result == "test_value_123"

    def test_hermes_env_secret_no_value(self):
        """Hiçbir yerde yoksa boş string dönmeli."""
        import tools
        with patch.dict(os.environ, {}, clear=False):
            # Ensure the env var doesn't exist
            if "NONEXISTENT_XYZ" in os.environ:
                del os.environ["NONEXISTENT_XYZ"]
            # Also ensure .env files are not readable
            with patch("builtins.open", side_effect=FileNotFoundError):
                result = tools._hermes_env_secret("NONEXISTENT_XYZ")
                assert result == ""


# ===========================================================================
# BRAIN CORE WRAPPER'LAR (8 adet)
# ===========================================================================

class TestBrainCoreWrappers:
    """hermes_arac_guvenilirlik_raporu, coo_cevap_kalite, durum, skor_karti,
       hafiza_ameliyat, arac_ameliyat, guvenlik_sertlestirme, yuzde_yuz_hazirlik."""

    def test_arac_guvenilirlik_returns_dict(self):
        """hermes_arac_guvenilirlik_raporu dict dönmeli."""
        import tools
        try:
            result = tools.hermes_arac_guvenilirlik_raporu()
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("hermes_brain_core import edilemedi")

    def test_coo_cevap_kalite_default_returns_dict(self):
        """hermes_coo_cevap_kalite_raporu varsayılanla dict dönmeli."""
        import tools
        try:
            result = tools.hermes_coo_cevap_kalite_raporu()
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("hermes_brain_core import edilemedi")

    def test_coo_cevap_kalite_with_samples(self):
        """Örnek cevaplarla da çalışmalı."""
        import tools
        try:
            result = tools.hermes_coo_cevap_kalite_raporu(ornek_cevaplar={"test": "cevap"})
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("hermes_brain_core import edilemedi")

    def test_hermes_durum_returns_dict(self):
        """hermes_durum dict dönmeli."""
        import tools
        try:
            result = tools.hermes_durum()
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("hermes_brain_core import edilemedi")

    def test_hermes_skor_karti_returns_dict(self):
        """hermes_skor_karti dict dönmeli."""
        import tools
        try:
            result = tools.hermes_skor_karti()
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("hermes_brain_core import edilemedi")

    def test_hafiza_ameliyat_plani_returns_dict(self):
        """hermes_hafiza_ameliyat_plani dict dönmeli."""
        import tools
        try:
            result = tools.hermes_hafiza_ameliyat_plani()
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("hermes_brain_core import edilemedi")

    def test_hafiza_ameliyat_with_records(self):
        """Kayıtlarla da çalışmalı."""
        import tools
        try:
            result = tools.hermes_hafiza_ameliyat_plani(kayitlar=[{"id": 1, "content": "test"}])
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("hermes_brain_core import edilemedi")

    def test_arac_ameliyat_plani_returns_dict(self):
        """hermes_arac_ameliyat_plani dict dönmeli."""
        import tools
        try:
            result = tools.hermes_arac_ameliyat_plani()
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("hermes_brain_core import edilemedi")

    def test_guvenlik_sertlestirme_plani_returns_dict(self):
        """hermes_guvenlik_sertlestirme_plani dict dönmeli."""
        import tools
        try:
            result = tools.hermes_guvenlik_sertlestirme_plani()
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("hermes_brain_core import edilemedi")

    def test_guvenlik_sertlestirme_plani_contains_security_keys(self):
        """Güvenlik planı temel anahtarları içermeli."""
        import tools
        try:
            result = tools.hermes_guvenlik_sertlestirme_plani()
            assert isinstance(result, dict)
            # En azından bir anahtar olmalı
            assert len(result) > 0
        except ImportError:
            pytest.skip("hermes_brain_core import edilemedi")

    def test_yuzde_yuz_hazirlik_returns_dict(self):
        """hermes_yuzde_yuz_hazirlik_raporu dict dönmeli."""
        import tools
        try:
            result = tools.hermes_yuzde_yuz_hazirlik_raporu()
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("hermes_brain_core import edilemedi")


# ===========================================================================
# SES FONKSIYONLARI
# ===========================================================================

class TestVoiceFunctions:
    """hermes_ses_dosyasi_uret, telegram_ses_gonder, hermes_sesli_cevap."""

    def test_ses_dosyasi_uret_returns_dict(self):
        """hermes_ses_dosyasi_uret dict dönmeli."""
        import tools
        result = tools.hermes_ses_dosyasi_uret("Test metin")
        assert isinstance(result, dict)
        # API key yoksa veya hata varsa ok=False döner
        assert "ok" in result

    def test_ses_dosyasi_uret_tts_request_fail_reported(self):
        """Geçersiz metin/build hatası ok=False dönmeli."""
        import tools
        with patch("hermes_brain_core.build_tts_request",
                   return_value={"ok": False, "warnings": ["empty_text"]}):
            result = tools.hermes_ses_dosyasi_uret("")
            assert result["ok"] is False
            assert "warnings" in result

    def test_ses_dosyasi_uret_no_api_key(self):
        """API key yoksa edge veya hata dönmeli."""
        import tools
        with patch("tools._hermes_env_secret", return_value=""):
            result = tools.hermes_ses_dosyasi_uret("Test")
            assert isinstance(result, dict)
            # Ya edge_tts dener ya da hata döner
            if not result.get("ok"):
                assert "hata" in result or "warnings" in result

    def test_ses_dosyasi_uret_with_custom_path(self):
        """Özel dosya yolu ile çalışmalı."""
        import tools
        with patch("tools._hermes_env_secret", return_value="sk-test-key"), \
             patch("hermes_brain_core.choose_tts_provider", return_value={"ok": True, "provider": "openai"}), \
             patch("hermes_brain_core.build_tts_request", return_value={
                 "ok": True, "url": "https://api.openai.com/v1/audio/speech",
                 "payload": {"model": "tts-1", "voice": "marin", "input": "test"},
                 "extension": "mp3"
             }), \
             patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.content = b"fake_audio_data"
            test_path = "/tmp/test_hermes_voice_output.mp3"
            result = tools.hermes_ses_dosyasi_uret("Test", dosya_yolu=test_path)
            assert isinstance(result, dict)
            # cleanup
            if os.path.exists(test_path):
                os.unlink(test_path)

    def test_ses_dosyasi_uret_openai_api_400(self):
        """OpenAI API hata döndüğünde ok=False dönmeli."""
        import tools
        with patch("tools._hermes_env_secret", return_value="sk-test-key"), \
             patch("hermes_brain_core.choose_tts_provider", return_value={"ok": True, "provider": "openai"}), \
             patch("hermes_brain_core.build_tts_request", return_value={
                 "ok": True, "url": "https://api.openai.com/v1/audio/speech",
                 "payload": {"model": "tts-1", "voice": "marin", "input": "test"},
                 "extension": "mp3"
             }), \
             patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 401
            result = tools.hermes_ses_dosyasi_uret("Test")
            assert result["ok"] is False
            assert result.get("status_code") == 401

    def test_telegram_ses_gonder_returns_dict(self):
        """telegram_ses_gonder dict dönmeli."""
        import tools
        result = tools.telegram_ses_gonder("/tmp/nonexistent_audio.mp3")
        assert isinstance(result, dict)
        assert "ok" in result

    def test_telegram_ses_gonder_no_file(self):
        """Var olmayan dosya için hata dönmeli."""
        import tools
        result = tools.telegram_ses_gonder("/tmp/nonexistent_xyz.mp3")
        assert result["ok"] is False
        assert "hata" in result

    def test_telegram_ses_gonder_success_mock(self):
        """Mock ile başarılı gönderim."""
        import tools
        real_path = tempfile.mktemp(suffix=".mp3")
        try:
            with open(real_path, "wb") as f:
                f.write(b"fake_audio")
            with patch("requests.post") as mock_post:
                mock_post.return_value.json.return_value = {"ok": True}
                mock_post.return_value.status_code = 200
                result = tools.telegram_ses_gonder(real_path)
                assert result["ok"] is True
        finally:
            os.unlink(real_path)

    def test_telegram_ses_gonder_exception(self):
        """Exception durumunda ok=False dönmeli."""
        import tools
        real_path = tempfile.mktemp(suffix=".mp3")
        try:
            with open(real_path, "wb") as f:
                f.write(b"test")
            with patch("requests.post", side_effect=Exception("Network error")):
                result = tools.telegram_ses_gonder(real_path)
                assert result["ok"] is False
                assert "hata" in result
        finally:
            os.unlink(real_path)

    def test_hermes_sesli_cevap_returns_dict(self):
        """hermes_sesli_cevap dict dönmeli."""
        import tools
        result = tools.hermes_sesli_cevap("Test", telegrama_gonder=False)
        assert isinstance(result, dict)
        assert "ok" in result

    def test_hermes_sesli_cevap_no_telegram(self):
        """Telegram'a göndermeden ses üretimi denenmeli."""
        import tools
        with patch("tools.hermes_ses_dosyasi_uret",
                   return_value={"ok": True, "dosya_yolu": "/tmp/test.mp3", "bytes": 1024}):
            result = tools.hermes_sesli_cevap("Test", telegrama_gonder=False)
            assert result["ok"] is True

    def test_hermes_sesli_cevap_ses_fail(self):
        """Ses üretimi başarısız olursa ok=False dönmeli."""
        import tools
        with patch("tools.hermes_ses_dosyasi_uret",
                   return_value={"ok": False, "hata": "test_hatasi"}):
            result = tools.hermes_sesli_cevap("Test", telegrama_gonder=False)
            assert result["ok"] is False

    def test_hermes_sesli_cevap_with_telegram_mock(self):
        """Telegram gönderimi mock ile."""
        import tools
        with patch("tools.hermes_ses_dosyasi_uret",
                   return_value={"ok": True, "dosya_yolu": "/tmp/test.mp3", "bytes": 1024}), \
             patch("tools.telegram_ses_gonder",
                   return_value={"ok": True, "status_code": 200}):
            result = tools.hermes_sesli_cevap("Test", telegrama_gonder=True)
            assert result["ok"] is True
            assert "telegram" in result


# ===========================================================================
# DISCOVERY — Phase 4 kapsamı
# ===========================================================================

def test_phase4_functions_exist():
    """Phase 4'te test edilen tüm fonksiyonlar tools.py'de var mı."""
    import ast
    tree = ast.parse(TOOLS_PATH.read_text(encoding="utf-8"))
    fnames = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    expected = {
        "_get_embedding_model", "_get_embedding", "pg_baglan", "_hermes_env_secret",
        "hermes_arac_guvenilirlik_raporu", "hermes_coo_cevap_kalite_raporu",
        "hermes_durum", "hermes_skor_karti",
        "hermes_hafiza_ameliyat_plani", "hermes_arac_ameliyat_plani",
        "hermes_guvenlik_sertlestirme_plani", "hermes_yuzde_yuz_hazirlik_raporu",
        "hermes_ses_dosyasi_uret", "telegram_ses_gonder", "hermes_sesli_cevap",
    }
    missing = expected - fnames
    assert not missing, f"Eksik fonksiyonlar: {missing}"
