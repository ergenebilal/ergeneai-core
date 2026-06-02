# Voice Function & Advanced Test Patterns

## 1. Voice (TTS) Function Testing

### hermes_ses_dosyasi_uret

tools.py'deki ses fonksiyonu 3 farklı iç import kullanır:
- `from hermes_brain_core import build_tts_request, choose_tts_provider`
- `import requests` (lazy)
- `import edge_tts` (opsiyonel, iç try/except)

**Mock hiyerarşisi (en hızlıdan en yavaşa):**

#### A. build_tts_request fail — en hızlı, API'ye hiç gitmez
```python
def test_ses_dosyasi_uret_tts_request_fail(self):
    import tools
    with patch("hermes_brain_core.build_tts_request",
               return_value={"ok": False, "warnings": ["empty_text"]}):
        result = tools.hermes_ses_dosyasi_uret("")
        assert result["ok"] is False
        assert "warnings" in result
```

**Neden `hermes_brain_core.build_tts_request`?**  
Çünkü `hermes_ses_dosyasi_uret` içinde `from hermes_brain_core import build_tts_request` var. Bu, `tools.build_tts_request` attribute'u oluşturmaz — `build_tts_request` fonksiyon lokalinde kalır. O yüzden kaynak modülü patch'leriz.

#### B. Full chain mock — OpenAI API çağrısı
```python
def test_ses_dosyasi_uret_openai_api_400(self):
    import tools
    with patch("tools._hermes_env_secret", return_value="sk-test-key"), \
         patch("hermes_brain_core.choose_tts_provider",
               return_value={"ok": True, "provider": "openai"}), \
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
```

#### C. No API key — edge_tts fallback test
```python
def test_ses_dosyasi_uret_no_api_key(self):
    import tools
    with patch("tools._hermes_env_secret", return_value=""):
        result = tools.hermes_ses_dosyasi_uret("Test")
        assert isinstance(result, dict)
        # Ya edge_tts dener ya da hata döner — ikisi de geçerli
        if not result.get("ok"):
            assert "hata" in result or "warnings" in result
```

### telegram_ses_gonder

tools.py:
```python
def telegram_ses_gonder(dosya_yolu, baslik="Hermes sesli cevap"):
    import requests  # iç import!
    ...
    response = requests.post(url, data=..., files={"audio": audio})
```

Test:
```python
def test_telegram_ses_gonder_success_mock(self):
    import tools
    real_path = tempfile.mktemp(suffix=".mp3")
    try:
        with open(real_path, "wb") as f:
            f.write(b"fake_audio")
        with patch("requests.post") as mock_post:  # requests.post, tools.requests.post DEĞİL
            mock_post.return_value.json.return_value = {"ok": True}
            mock_post.return_value.status_code = 200
            result = tools.telegram_ses_gonder(real_path)
            assert result["ok"] is True
    finally:
        os.unlink(real_path)
```

### hermes_sesli_cevap (composite function)

İki alt fonksiyonu zincirler: `hermes_ses_dosyasi_uret` → `telegram_ses_gonder`.

```python
def test_hermes_sesli_cevap_no_telegram(self):
    import tools
    with patch("tools.hermes_ses_dosyasi_uret",
               return_value={"ok": True, "dosya_yolu": "/tmp/test.mp3", "bytes": 1024}):
        result = tools.hermes_sesli_cevap("Test", telegrama_gonder=False)
        assert result["ok"] is True

def test_hermes_sesli_cevap_ses_fail(self):
    import tools
    with patch("tools.hermes_ses_dosyasi_uret",
               return_value={"ok": False, "hata": "test_hatasi"}):
        result = tools.hermes_sesli_cevap("Test", telegrama_gonder=False)
        assert result["ok"] is False

def test_hermes_sesli_cevap_with_telegram_mock(self):
    import tools
    with patch("tools.hermes_ses_dosyasi_uret",
               return_value={"ok": True, "dosya_yolu": "/tmp/test.mp3", "bytes": 1024}), \
         patch("tools.telegram_ses_gonder",
               return_value={"ok": True, "status_code": 200}):
        result = tools.hermes_sesli_cevap("Test", telegrama_gonder=True)
        assert result["ok"] is True
        assert "telegram" in result
```

---

## 2. Context Manager Mock Pattern (`with conn.cursor() as cur:`)

PostgreSQL fonksiyonları genelde şu pattern'i kullanır:

```python
def pg_proaktif_analiz():
    conn = pg_baglan()
    with conn.cursor() as cur:
        cur.execute("SELECT ...")
        records = cur.fetchall()
    conn.close()
```

**Doğru mock:**

```python
def test_pg_proaktif_analiz_no_records(self):
    import tools
    with patch("tools.pg_baglan") as mock_baglan:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []  # boş sonuç
        # __enter__ döndüren context manager:
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_baglan.return_value = mock_conn
        result = tools.pg_proaktif_analiz()
        assert isinstance(result, dict)
        assert "ozet" in result
```

**Açıklama:**
- `conn.cursor()` → `mock_conn.cursor.return_value` (cursor objesi)
- `with ... as cur:` → `__enter__` çağırır → `mock_conn.cursor.return_value.__enter__.return_value`
- `cur.fetchall()` → `mock_cursor.fetchall.return_value`
- Bu sayede fonksiyon PG'ye hiç bağlanmaz, LLM/embedding/ollama dalına girmez

---

## 3. Brain Core Wrapper Testing

Hermes'teki birçok fonksiyon **thin wrapper**'dır — sadece `hermes_brain_core`'a delegasyon yapar:

```python
def hermes_durum() -> dict:
    from hermes_brain_core import run_strategic_status
    return run_strategic_status()
```

Test pattern'i:

```python
def test_hermes_durum_returns_dict(self):
    import tools
    try:
        result = tools.hermes_durum()
        assert isinstance(result, dict)
    except ImportError:
        pytest.skip("hermes_brain_core modülü import edilemedi — test atlandı")
```

Aynı pattern şu wrapper'lar için geçerli:
- `hermes_arac_guvenilirlik_raporu` → `inspect_tools_static()`
- `hermes_coo_cevap_kalite_raporu` → `run_coo_response_quality_report()`
- `hermes_durum` → `run_strategic_status()`
- `hermes_skor_karti` → `run_scorecard()`
- `hermes_hafiza_ameliyat_plani` → `build_memory_surgery_plan()`
- `hermes_arac_ameliyat_plani` → `build_tool_surgery_plan()`
- `hermes_yuzde_yuz_hazirlik_raporu` → `run_readiness_report()`
- `hermes_proaktif_brifing` → `generate_briefing()`
- `hermes_eylem_guvenlik_sinifi` → `classify_autonomy_action()`
- `hermes_gelisim_raporu` → `build_development_report()`
- `hermes_oncelik_analiz` → `rank_priorities()`
- `hermes_hafiza_kayit_hazirla` → `prepare_memory_entry()`
- `hermes_hafiza_kalite_raporu` → `run_memory_quality_report()`
- `hermes_karar_plani` → `make_decision_plan()`
- `hermes_oncelik_motoru` → `build_operational_priority()`

---

## 4. Internal Helper Testing Strategy

Helper fonksiyonları (`_get_embedding_model`, `_get_embedding`, `pg_baglan`, `_hermes_env_secret`) doğrudan test edilebilir:

| Helper | Test pattern |
|---|---|
| `_get_embedding_model` | `patch("sentence_transformers.SentenceTransformer")` — kaynak modülü patchle |
| `_get_embedding` | `patch.object(tools, "_embedding_model", mock_model)` — singleton'ı mock'la |
| `pg_baglan` | Gerçekten çağır, exception bekle (PG down) veya connection doğrula |
| `_hermes_env_secret` | `patch.dict(os.environ, ...)` veya `patch("builtins.open", ...)` |

**Not:** Bu helper'lar **dolaylı olarak** çağıran fonksiyonlar (pg_kaydet, pg_ara, hermes_ses_dosyasi_uret) test edilirken de test edilmiş olur. Direkt test eklemek opsiyoneldir ancak hatayı izole etmeyi kolaylaştırır.

---

## 5. Security Hardening Test Pattern

`hermes_guvenlik_sertlestirme_plani` karmaşık bağımlılıkları olan bir fonksiyondur:
- `subprocess.check_output(["sh", "-c", "ss -tulpen ..."])`
- `glob.glob(".env")`
- `from hermes_brain_core import build_security_hardening_plan, ...`

Test:
```python
def test_guvenlik_sertlestirme_plani_returns_dict(self):
    import tools
    try:
        result = tools.hermes_guvenlik_sertlestirme_plani()
        assert isinstance(result, dict)
        assert len(result) > 0
    except ImportError:
        pytest.skip("hermes_brain_core import edilemedi")
```

Subprocess çıktısı gerçek sistemden gelir — bu normaldir. Sadece tip ve minimal yapı doğrulanır.
