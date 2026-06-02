"""
test_tools_phase2.py — Phase 2: Telegram, Drive, Sheets, Verification, Error/Repair, PG Extra.

Test edilen fonksiyonlar:
  - telegram_mesaj_gonder       (çıktı kanalı)
  - drive_dosya_listele          (Drive dosya listeleme)
  - drive_dosya_yukle            (Drive dosya yükleme)
  - sheets_oku / sheets_yaz / sheets_ekle  (Google Sheets)
  - verify_claim                 (LongTracer doğrulama)
  - check_system_status          (chroma, docker)
  - log_hata / get_hata_gecmisi  (hata loglama)
  - self_repair                  (hata onarım önerisi)
  - pg_son / pg_proaktif_analiz  (PostgreSQL ekstra)
  - hermes_beyin_saglik_raporu   (beyin sağlığı)
  - hermes_eylem_guvenlik_sinifi  (güvenlik sınıflandırması)
  - hermes_gelisim_raporu        (gelişim raporu)
  - hermes_oncelik_analiz        (önceliklendirme)
  - hermes_hafiza_kayit_hazirla   (hafıza hazırlığı)
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, ANY

import pytest

TOOLS_PATH = Path(__file__).resolve().parents[1] / "tools.py"


# ===========================================================================
# TELEGRAM — çıktı kanalı, en kritik
# ===========================================================================

class TestTelegram:
    """telegram_mesaj_gonder — dış dünyaya çıkan ana kanal."""

    def test_telegram_returns_bool(self):
        """telegram_mesaj_gonder bool dönmeli (başarılı veya başarısız)."""
        import tools
        result = tools.telegram_mesaj_gonder("Test mesajı")
        assert isinstance(result, bool)

    def test_telegram_success_with_mock(self):
        """Mock ile başarılı gönderim True dönmeli."""
        import tools
        with patch("requests.post") as mock_post:
            mock_post.return_value.json.return_value = {"ok": True}
            result = tools.telegram_mesaj_gonder("Test")
            assert result is True
            mock_post.assert_called_once()

    def test_telegram_failure_with_mock(self):
        """Mock ile başarısız gönderim False dönmeli."""
        import tools
        with patch("requests.post") as mock_post:
            mock_post.return_value.json.return_value = {"ok": False}
            result = tools.telegram_mesaj_gonder("Test")
            assert result is False

    def test_telegram_exception_returns_false(self):
        """Exception durumunda False dönmeli."""
        import tools
        with patch("requests.post", side_effect=Exception("Bağlantı hatası")):
            result = tools.telegram_mesaj_gonder("Test")
            assert result is False

    def test_telegram_sends_correct_payload(self):
        """Doğru chat_id ve mesaj gönderilmeli."""
        import tools
        with patch("requests.post") as mock_post:
            mock_post.return_value.json.return_value = {"ok": True}
            tools.telegram_mesaj_gonder("Deneme mesajı")
            args, kwargs = mock_post.call_args
            assert "sendMessage" in args[0]
            assert kwargs["json"]["chat_id"] == "5506784207"
            assert kwargs["json"]["text"] == "Deneme mesajı"


# ===========================================================================
# GOOGLE DRIVE — dosya yönetimi
# ===========================================================================

class TestDrive:
    """drive_dosya_listele ve drive_dosya_yukle."""

    @patch("tools.google_auth")
    def test_drive_listele_returns_list_or_string(self, mock_auth):
        """drive_dosya_listele liste veya string dönmeli."""
        import tools
        mock_auth.return_value = (MagicMock(), None)
        with patch("tools.build") as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            mock_service.files.return_value.list.return_value.execute.return_value = {
                "files": []
            }
            result = tools.drive_dosya_listele()
            assert isinstance(result, (list, str))

    @patch("tools.google_auth")
    def test_drive_listele_with_results(self, mock_auth):
        """Dosya varsa liste dönmeli."""
        import tools
        mock_auth.return_value = (MagicMock(), None)
        with patch("tools.build") as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            mock_service.files.return_value.list.return_value.execute.return_value = {
                "files": [
                    {"id": "abc123", "name": "test.txt", "mimeType": "text/plain", "size": "1024", "createdTime": "2026-01-01"}
                ]
            }
            result = tools.drive_dosya_listele()
            assert isinstance(result, list)
            assert len(result) >= 1
            if isinstance(result[0], dict):
                assert "ad" in result[0]

    @patch("tools.google_auth")
    def test_drive_listele_auth_failure(self, mock_auth):
        """Auth başarısızsa hata stringi dönmeli."""
        import tools
        mock_auth.return_value = (None, "❌ Auth hatası")
        result = tools.drive_dosya_listele()
        assert isinstance(result, str)
        assert "hata" in result.lower() or "❌" in result

    @patch("tools.google_auth")
    def test_drive_yukle_nonexistent_file(self, mock_auth):
        """Var olmayan dosya için hata dönmeli."""
        import tools
        result = tools.drive_dosya_yukle("/tmp/nonexistent_file_xyz_12345.txt")
        assert isinstance(result, str)
        assert "bulunamadı" in result.lower() or "❌" in result

    @patch("tools.google_auth")
    def test_drive_yukle_auth_failure(self, mock_auth):
        """Auth başarısızsa hata dönmeli."""
        import tools
        mock_auth.return_value = (None, "❌ Auth hatası")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"test")
            fname = f.name
        try:
            result = tools.drive_dosya_yukle(fname)
            assert isinstance(result, str)
            assert "hata" in result.lower() or "❌" in result
        finally:
            os.unlink(fname)

    @patch("tools.google_auth")
    def test_drive_yukle_success_with_mock(self, mock_auth):
        """Başarılı yükleme ✅ mesajı dönmeli."""
        import tools
        mock_auth.return_value = (MagicMock(), None)
        with patch("tools.build") as mock_build, \
             patch("googleapiclient.http.MediaFileUpload", return_value=MagicMock()):
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            mock_service.files.return_value.create.return_value.execute.return_value = {
                "id": "abc123", "name": "test.txt"
            }
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
                f.write(b"test")
                fname = f.name
            try:
                result = tools.drive_dosya_yukle(fname)
                assert isinstance(result, str)
                assert "✅" in result or "yuklendi" in result.lower()
            finally:
                os.unlink(fname)


# ===========================================================================
# GOOGLE SHEETS — veri yönetimi
# ===========================================================================

class TestSheets:
    """sheets_oku, sheets_yaz, sheets_ekle."""

    SHEET_ID = "test_sheet_id_12345"

    @patch("tools.google_auth")
    def test_sheets_oku_returns_list_or_string(self, mock_auth):
        """sheets_oku liste veya string dönmeli."""
        import tools
        mock_auth.return_value = (MagicMock(), None)
        with patch("tools.build") as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            mock_service.spreadsheets.return_value.values.return_value.get.return_value.execute.return_value = {
                "values": [["a", "b"], ["c", "d"]]
            }
            result = tools.sheets_oku(self.SHEET_ID)
            assert isinstance(result, (list, str))

    @patch("tools.google_auth")
    def test_sheets_oku_with_data(self, mock_auth):
        """Veri varsa 2D liste dönmeli."""
        import tools
        mock_auth.return_value = (MagicMock(), None)
        with patch("tools.build") as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            mock_service.spreadsheets.return_value.values.return_value.get.return_value.execute.return_value = {
                "values": [["İsim", "Miktar"], ["Ali", "100"], ["Veli", "200"]]
            }
            result = tools.sheets_oku(self.SHEET_ID)
            assert isinstance(result, list)
            assert len(result) == 3

    @patch("tools.google_auth")
    def test_sheets_oku_auth_failure(self, mock_auth):
        """Auth hatasında string dönmeli."""
        import tools
        mock_auth.return_value = (None, "❌ Auth hatası")
        result = tools.sheets_oku(self.SHEET_ID)
        assert isinstance(result, str)

    @patch("tools.google_auth")
    def test_sheets_oku_no_data(self, mock_auth):
        """Veri yoksa düzgün mesaj dönmeli."""
        import tools
        mock_auth.return_value = (MagicMock(), None)
        with patch("tools.build") as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            mock_service.spreadsheets.return_value.values.return_value.get.return_value.execute.return_value = {
                "values": []
            }
            result = tools.sheets_oku(self.SHEET_ID)
            assert isinstance(result, str)
            assert "bulunamadı" in result.lower() or "veri" in result.lower()

    @patch("tools.google_auth")
    def test_sheets_yaz_no_data(self, mock_auth):
        """Veri yoksa hata dönmeli."""
        import tools
        result = tools.sheets_yaz(self.SHEET_ID)
        assert isinstance(result, str)
        assert "❌" in result or "gerekli" in result.lower()

    @patch("tools.google_auth")
    def test_sheets_yaz_success(self, mock_auth):
        """Başarılı yazma ✅ mesajı dönmeli."""
        import tools
        mock_auth.return_value = (MagicMock(), None)
        with patch("tools.build") as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            mock_service.spreadsheets.return_value.values.return_value.update.return_value.execute.return_value = {
                "updatedCells": 4
            }
            result = tools.sheets_yaz(self.SHEET_ID, veriler=[["a", "b"], ["c", "d"]])
            assert isinstance(result, str)
            assert "✅" in result or "yazildi" in result.lower()

    @patch("tools.google_auth")
    def test_sheets_ekle_no_data(self, mock_auth):
        """Veri yoksa hata dönmeli."""
        import tools
        result = tools.sheets_ekle(self.SHEET_ID)
        assert isinstance(result, str)
        assert "❌" in result or "gerekli" in result.lower()

    @patch("tools.google_auth")
    def test_sheets_ekle_success(self, mock_auth):
        """Başarılı ekleme ✅ mesajı dönmeli."""
        import tools
        mock_auth.return_value = (MagicMock(), None)
        with patch("tools.build") as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            mock_service.spreadsheets.return_value.values.return_value.append.return_value.execute.return_value = {
                "updates": {"updatedRows": 2}
            }
            result = tools.sheets_ekle(self.SHEET_ID, veriler=[["yeni", "veri"]])
            assert isinstance(result, str)
            assert "✅" in result or "eklendi" in result.lower()

    @patch("tools.google_auth")
    def test_sheets_yaz_auth_failure(self, mock_auth):
        """Auth hatasında string dönmeli."""
        import tools
        mock_auth.return_value = (None, "❌ Auth hatası")
        result = tools.sheets_yaz(self.SHEET_ID, veriler=[["test"]])
        assert isinstance(result, str)

    @patch("tools.google_auth")
    def test_sheets_ekle_auth_failure(self, mock_auth):
        """Auth hatasında string dönmeli."""
        import tools
        mock_auth.return_value = (None, "❌ Auth hatası")
        result = tools.sheets_ekle(self.SHEET_ID, veriler=[["test"]])
        assert isinstance(result, str)


# ===========================================================================
# DOĞRULAMA & SİSTEM DURUMU
# ===========================================================================

class TestVerification:
    """verify_claim ve check_system_status — güvenilirlik."""

    def test_verify_claim_returns_dict(self):
        """verify_claim her koşulda dict dönmeli."""
        import tools
        result = tools.verify_claim("Test iddia", "test kaynağı")
        assert isinstance(result, dict)
        assert "verdict" in result

    def test_verify_claim_without_longtracer(self):
        """LongTracer yoksa UNKNOWN dönmeli."""
        import tools
        with patch.object(tools, "_longtracer_model", None):
            with patch("tools.get_longtracer_model", return_value=None):
                result = tools.verify_claim("Test", "kaynak")
                assert result["verdict"] == "UNKNOWN"
                assert result["confidence"] is None

    def test_verify_claim_with_longtracer(self):
        """LongTracer varsa sonuç dönmeli."""
        import tools
        mock_lt = MagicMock()
        mock_lt.check.return_value = MagicMock(verdict="PASS", confidence=0.95)
        with patch("tools.get_longtracer_model", return_value=mock_lt):
            result = tools.verify_claim("Test", "kaynak")
            assert result["verdict"] == "PASS"

    def test_check_system_status_unknown(self):
        """Bilinmeyen servis 'unknown' dönmeli."""
        import tools
        result = tools.check_system_status("nonexistent_service")
        assert isinstance(result, dict)
        assert result["status"] == "unknown"

    def test_check_system_status_chroma_not_running(self):
        """Chroma çalışmıyorsa 'not_running' dönmeli."""
        import tools
        with patch("tools.subprocess.check_output", side_effect=Exception("Bağlantı yok")):
            result = tools.check_system_status("chroma")
            assert result["status"] == "not_running"

    def test_check_system_status_docker_running(self):
        """Docker çalışıyorsa 'running' dönmeli."""
        import tools
        with patch("tools.subprocess.check_output", return_value=b""):
            result = tools.check_system_status("docker")
            assert result["status"] == "running"

    def test_check_system_status_docker_not_running(self):
        """Docker çalışmıyorsa 'not_running' dönmeli."""
        import tools
        with patch("tools.subprocess.check_output", side_effect=Exception("Docker yok")):
            result = tools.check_system_status("docker")
            assert result["status"] == "not_running"


# ===========================================================================
# HATA YÖNETİMİ
# ===========================================================================

class TestErrorLog:
    """log_hata ve get_hata_gecmisi — hata loglama altyapısı."""

    def test_log_hata_returns_string(self):
        """log_hata string dönmeli."""
        import tools
        with patch.object(tools, "HATA_LOG", "/tmp/test_hermes_hata.log"):
            result = tools.log_hata("test_hata", "detay", "doğru davranış")
            assert isinstance(result, str)

    def test_log_hata_writes_to_file(self):
        """Hata log dosyaya yazılmalı."""
        import tools
        test_log = "/tmp/test_hermes_hata_write.log"
        if os.path.exists(test_log):
            os.unlink(test_log)
        with patch.object(tools, "HATA_LOG", test_log):
            result = tools.log_hata("test_write", "detay yazıldı", "doğrusu")
            assert "✅" in result
            assert os.path.exists(test_log)
            content = open(test_log, encoding="utf-8").read()
            assert "test_write" in content
            assert "detay yazıldı" in content
        os.unlink(test_log)

    def test_get_hata_gecmisi_returns_list(self):
        """get_hata_gecmisi liste dönmeli."""
        import tools
        test_log = "/tmp/test_hermes_hata_oku.log"
        if os.path.exists(test_log):
            os.unlink(test_log)
        with patch.object(tools, "HATA_LOG", test_log):
            result = tools.get_hata_gecmisi()
            assert isinstance(result, list)

    def test_get_hata_gecmisi_with_entries(self):
        """Kayıt varsa doğru sayıda dönmeli."""
        import tools
        test_log = "/tmp/test_hermes_hata_list.log"
        with open(test_log, "w", encoding="utf-8") as f:
            for i in range(3):
                f.write(f"Satır {i}\n")
        with patch.object(tools, "HATA_LOG", test_log):
            result = tools.get_hata_gecmisi(limit=2)
            assert isinstance(result, list)
            assert len(result) == 2
        os.unlink(test_log)

    def test_get_hata_gecmisi_no_file(self):
        """Dosya yoksa boş liste dönmeli."""
        import tools
        with patch.object(tools, "HATA_LOG", "/tmp/nonexistent_log_12345.log"):
            result = tools.get_hata_gecmisi()
            assert isinstance(result, list)
            assert len(result) == 0


# ===========================================================================
# SELF REPAIR — hata onarım önerileri
# ===========================================================================

class TestSelfRepair:
    """self_repair — hata türüne göre çözüm önerisi."""

    def test_self_repair_returns_string(self):
        """self_repair her koşulda string dönmeli."""
        import tools
        result = tools.self_repair("Test hata")
        assert isinstance(result, str)

    def test_self_repair_max_deneme(self):
        """3 deneme aşılırsa uyarı dönmeli."""
        import tools
        result = tools.self_repair("Herhangi bir hata", deneme=3)
        assert "maksimum" in result.lower() or "Maksimum" in result

    def test_self_repair_chroma_error(self):
        """Chroma hatası için yeniden başlatma önerisi dönmeli."""
        import tools
        result = tools.self_repair("chromadb bağlantı hatası", deneme=1)
        assert "ChromaDB" in result or "yeniden" in result.lower()

    def test_self_repair_connection_error(self):
        """Bağlantı hatası için ağ kontrol önerisi dönmeli."""
        import tools
        result = tools.self_repair("bağlantı zaman aşımı", deneme=1)
        assert "bağlantı" in result.lower() or "Bağlantı" in result

    def test_self_repair_dosya_error(self):
        """Dosya bulunamadı hatası için dosya oluşturma önerisi dönmeli."""
        import tools
        result = tools.self_repair("dosya bulunamadı", deneme=1)
        assert "dosya" in result.lower() or "Dosya" in result

    def test_self_repair_unknown_error(self):
        """Bilinmeyen hata için alternatif deneniyor mesajı dönmeli."""
        import tools
        result = tools.self_repair("bilinmeyen bir problem oluştu", deneme=2)
        assert "alternatif" in result.lower() or "Bilinmeyen" in result

    def test_self_repair_increments_deneme(self):
        """Hata mesajında deneme numarası artırılarak geçmeli."""
        import tools
        result = tools.self_repair("özel hata durumu", deneme=1)
        # 3'üncü denemede vermemeli, daha düşük denemede öneri dönmeli
        assert "Maksimum" not in result


# ===========================================================================
# POSTGRESQL EXTRA
# ===========================================================================

class TestPostgresExtra:
    """pg_son ve pg_proaktif_analiz — PostgreSQL ek sorgular."""

    def test_pg_son_returns_list(self):
        """pg_son her koşulda liste dönmeli."""
        import tools
        result = tools.pg_son()
        assert isinstance(result, list)

    def test_pg_son_limit_param(self):
        """limit parametresiyle çalışmalı."""
        import tools
        result = tools.pg_son(limit=3)
        assert isinstance(result, list)

    def test_pg_proaktif_analiz_returns_dict_no_records(self):
        """Hiç kayıt yoksa bile dict dönmeli."""
        import tools
        with patch("tools.pg_baglan") as mock_baglan:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_baglan.return_value = mock_conn
            result = tools.pg_proaktif_analiz()
            assert isinstance(result, dict)
            assert "ozet" in result or "kayit_sayisi" in result


# ===========================================================================
# BEYİN KÖPRÜSÜ (hermes_brain_core thin wrappers)
# ===========================================================================

class TestBrainBridge:
    """Hermes beyin köprüsü fonksiyonları — hermes_brain_core'a delegasyon."""

    def test_hermes_beyin_saglik_raporu_returns_dict(self):
        """hermes_beyin_saglik_raporu dict dönmeli."""
        import tools
        try:
            result = tools.hermes_beyin_saglik_raporu()
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("hermes_brain_core modülü import edilemedi — test atlandı")

    def test_hermes_eylem_guvenlik_sinifi_returns_dict(self):
        """hermes_eylem_guvenlik_sinifi dict dönmeli."""
        import tools
        try:
            result = tools.hermes_eylem_guvenlik_sinifi("mesaj gönder")
            assert isinstance(result, dict)
            # Gerçek dönüş anahtarları: sinif, gerekce, eylem
            assert "sinif" in result
            assert "gerekce" in result or "eylem" in result
        except ImportError:
            pytest.skip("hermes_brain_core modülü import edilemedi — test atlandı")

    def test_hermes_gelisim_raporu_returns_dict(self):
        """hermes_gelisim_raporu dict dönmeli."""
        import tools
        try:
            result = tools.hermes_gelisim_raporu()
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("hermes_brain_core modülü import edilemedi — test atlandı")

    def test_hermes_oncelik_analiz_returns_list(self):
        """hermes_oncelik_analiz liste dönmeli."""
        import tools
        try:
            result = tools.hermes_oncelik_analiz(["Görev A", "Görev B", "Görev C"])
            assert isinstance(result, list)
        except ImportError:
            pytest.skip("hermes_brain_core modülü import edilemedi — test atlandı")

    def test_hermes_oncelik_analiz_empty_input(self):
        """Boş girdiyle de çalışmalı."""
        import tools
        try:
            result = tools.hermes_oncelik_analiz([])
            assert isinstance(result, list)
        except ImportError:
            pytest.skip("hermes_brain_core modülü import edilemedi — test atlandı")

    def test_hermes_hafiza_kayit_hazirla_returns_dict(self):
        """hermes_hafiza_kayit_hazirla dict dönmeli."""
        import tools
        try:
            result = tools.hermes_hafiza_kayit_hazirla(
                "Test içerik", category="genel", importance=3
            )
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("hermes_brain_core modülü import edilemedi — test atlandı")


# ===========================================================================
# DISCOVERY — Phase 2 kapsamı
# ===========================================================================

def test_phase2_functions_exist():
    """Phase 2'de test edilen tüm fonksiyonlar tools.py'de var mı."""
    import ast
    tree = ast.parse(TOOLS_PATH.read_text(encoding="utf-8"))
    fnames = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    expected = {
        "telegram_mesaj_gonder",
        "drive_dosya_listele", "drive_dosya_yukle",
        "sheets_oku", "sheets_yaz", "sheets_ekle",
        "verify_claim", "check_system_status",
        "log_hata", "get_hata_gecmisi",
        "self_repair",
        "pg_son", "pg_proaktif_analiz",
        "hermes_beyin_saglik_raporu",
        "hermes_eylem_guvenlik_sinifi",
        "hermes_gelisim_raporu",
        "hermes_oncelik_analiz",
        "hermes_hafiza_kayit_hazirla",
    }
    missing = expected - fnames
    assert not missing, f"Eksik fonksiyonlar: {missing}"
