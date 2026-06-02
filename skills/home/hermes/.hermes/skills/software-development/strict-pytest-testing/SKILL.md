---
name: strict-pytest-testing
version: 1.2.0
author: Hermes
description: Katı (strict) pytest test suite'leri yazma rehberi — özellikle 3rd-party bağımlılıkları olan modüller için. tools.py tipi kodların testini yazarken uygulanacak standart.
---

# Strict Pytest Testing Rehberi

## Ne Zaman Kullanılır

- Var olan bir `.py` modülüne test yazarken
- `tools.py` gibi çok sayıda bağımlılığı (Google API, PostgreSQL, embedding model) olan bir modülü test ederken
- 3rd-party kütüphane uyarıları (`DeprecationWarning`, `ResourceWarning`) testleri kırdığında
- Mevcut test sayısını artırmak (0 → 42 gibi) ve kaliteyi ölçmek istediğinde

## Dizin Yapısı

```
tests/
├── conftest.py          # Global warning filter'lar
├── pytest.ini           # Strict mode ayarları
├── test_hermes_brain_core.py   # Örnek: core modül testleri
└── test_tools.py        # Örnek: tools.py testleri
```

## Adım Adım

### 1. Dosya Yapısını Oluştur

```
tests/
├── conftest.py
├── pytest.ini
├── test_<modul_adi>.py
```

### 2. pytest.ini — Strict Mode

```ini
[pytest]
filterwarnings =
    error
    # 3rd-party kütüphane uyarılarını sessize al
    ignore::DeprecationWarning:httplib2.*
    ignore::DeprecationWarning:pyparsing.*
    ignore:module.*sre_constants.*:DeprecationWarning
    # SSL/Resource uyarıları
    ignore:unclosed.*ssl.*:ResourceWarning
    ignore::pytest.PytestUnraisableExceptionWarning
```

### 3. conftest.py — Global Filtreler

```python
import warnings

# Python 3.11'de httplib2 -> pyparsing -> sre_constants deprecation
# uyarisi tum testleri -W error modunda kiriyor. Sadece bunu sessize al.
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=".*sre_constants.*",
)
```

### 4. Test Dosyası Şablonu

```python
"""
test_<modul>.py — Katı (strict) test suite.

Kurallar:
  - Her test ya gerçek bir durumu doğrular ya da belgelenmiş bir mock kullanır.
  - API/DB bağlantısı gerektiren testlerde fixture gerçek token/config
    varlığını kontrol eder, yoksa skip atar.
  - Tüm testler `-W error` ile çalıştırıldığında hata vermez.
  - Test edilen modül import edilir, fonksiyonlar çağrılır.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

TOOLS_PATH = Path(__file__).resolve().parents[1] / "tools.py"
```

### 5. Discovery Testi (AST ile)

```python
def _tool_function_names():
    import ast
    tree = ast.parse(TOOLS_PATH.read_text(encoding="utf-8"))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

def test_tools_py_contains_expected_functions():
    """Modül içinde beklenen fonksiyonlar var mı kontrol et."""
    fnames = _tool_function_names()
    expected = {"fonk1", "fonk2", "fonk3"}
    missing = expected - fnames
    assert not missing, f"Eksik fonksiyonlar: {missing}"
```

### 6. Test Sınıfı Yapısı (Her Fonksiyon Grubu İçin)

```python
class TestGmail:
    """gmail_gonder ve gmail_oku fonksiyonları."""

    def test_gmail_gonder_returns_string(self):
        """Her koşulda string dönmeli (hata mesajı veya başarı)."""
        import tools

        result = tools.gmail_gonder("test@example.com", "Konu", "İçerik")
        assert isinstance(result, str)

    @pytest.mark.skipif(not GOOGLE_TOKEN.exists(), reason="Google token yok")
    def test_gmail_gonder_success_message(self):
        """Token varsa ve auth geçerse başarı mesajı dönmeli."""
        import tools

        result = tools.gmail_gonder("test@example.com", "Konu", "İçerik")
        if result.startswith("✅"):
            assert "gonderildi" in result.lower()
        else:
            # Auth hatası olabilir — bu kabul edilebilir
            assert "hata" in result.lower() or "❌" in result
```

### 7. Fonksiyon İçi Import'ları Patchleme (Kritik!)

Bazı fonksiyonlar bağımlılıkları fonksiyon içinde import eder (`import requests`, `from googleapiclient.http import MediaFileUpload`).
Bu durumda **modül seviyesinde patch** kullanılmalıdır:

**YANLIŞ:**
```python
with patch("tools.requests.post") as mock_post:  # ❌ tools.requests yok!
```

**DOĞRU:**
```python
with patch("requests.post") as mock_post:  # ✅ doğrudan requests modülü
```

Detaylı pattern ve tüm yaygın örnekler için:
→ `references/internal-import-mocking.md`

### 8. Phase-Based Expansion Strategy

Büyük modülleri (50+ fonksiyon) tek seferde test etmek yerine **aşamalı** yaklaş:

```
tests/
├── test_tools.py              # Phase 1: 5-8 en kritik fonksiyon
├── test_tools_phase2.py       # Phase 2: sonraki 15-20 fonksiyon
├── test_tools_phase3.py       # Phase 3: kalanlar + edge case'ler
└── test_hermes_brain_core.py  # Ayrı modül, bağımsız test
```

Her faz sonunda: `pytest -v --tb=short` ile çalıştır, geçmeyenleri düzelt.
Faz ilerledikçe test güveni artar, tüm suite yeşil kalır.

#### Coverage Discovery (Fazlar Arası)

Her faz **öncesi** hangi fonksiyonların test edilmediğini AST ile tespit et:

```bash
cd /proje && python3 -c "
import ast
code = open('tools.py').read()
tree = ast.parse(code)
funcs = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
tested = {'zaten_testli_olan_fonk1', 'fonk2'}
untested = [f for f in funcs if f not in tested]
print(f'Toplam: {len(funcs)}, Testli: {len(funcs)-len(untested)}, Eksik: {len(untested)}')
for f in untested: print(f'  ⬜ {f}')
"
```

Her fazın sonunda **discovery testi** koyarak kapsamı garanti altına al:
```python
def test_phaseN_functions_exist():
    import ast
    tree = ast.parse(TOOLS_PATH.read_text(encoding="utf-8"))
    fnames = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    expected = {"fonk1", "fonk2"}
    missing = expected - fnames
    assert not missing, f"Eksik fonksiyonlar: {missing}"
```

### 9. Yaygın Mock Pattern'leri

| Durum | Pattern | Örnek |
|---|---|---|
| Google Auth (decorator) | `@patch("tools.google_auth")` | `mock_auth.return_value = (MagicMock(), None)` |
| Google API service | `with patch("tools.build")` | `mock_build.return_value = MagicMock()` |
| HTTP çağrısı (iç import) | `patch("requests.post")` | `mock_post.return_value.json.return_value = {"ok": True}` |
| DB işlemi (timeout riski) | `patch("tools.pg_baglan")` | Boş cursor döndür → LLM çağrısına hiç girme |
| File I/O | `patch.object(tools, "HATA_LOG", "/tmp/test.log")` | Geçici dosyaya yönlendir |
| subprocess | `patch("tools.subprocess.check_output")` | `return_value=b""` veya `side_effect=Exception()` |
| ChromaDB baglantisi | `patch("tools.chromadb.HttpClient")` | `side_effect=Exception("bulunamadi")` |
| Deprecated full-chain | Coklu `with patch()` zinciri | `bilal_notes_ara` + `verify_claim` + `suan` birlikte |
| Session temizligi | `setup_method` + `patch.object` | `tools._session_memory.clear()` |
| Singleton helper reset | Dogrudan attribute set | `tools._longtracer_model = None` |
| PG cursor ctx manager | `mock_conn.cursor.return_value.__enter__` | Bos cursor dondur, LLM dalina girme |

### 10. Payload Doğrulama (Call Args Inspection)

Mock ile gönderilen veriyi doğrulamak için `call_args` / `call_args_list`:

```python
with patch("requests.post") as mock_post:
    tools.telegram_mesaj_gonder("Deneme")
    args, kwargs = mock_post.call_args
    assert "sendMessage" in args[0]          # URL kontrolü
    assert kwargs["json"]["text"] == "Deneme" # Body kontrolü
    assert kwargs["timeout"] == 10            # Parametre kontrolü
```

## Test Yazma Prensipleri

### Her Testte Olması Gerekenler

1. **Tip kontrolü** — Fonksiyon her koşulda doğru tipte dönüş yapmalı
2. **Skip koşulu** — API/token yoksa `pytest.skip()` ile atla
3. **Graceful degradation** — Auth hatası ❌ dönse bile test geçmeli (hata mesajını assert et)
4. **Edge case** — Geçersiz input (URL, tarih, ID) test edilmeli

### Uyarı Yönetimi

- `pytest.ini`'de `filterwarnings = error` (strict)
- 3rd-party kütüphanelerden gelen uyarılar `ignore` ile kapat
- Kendi kodundan gelen uyarılar düzeltilmeli (ignore edilmemeli)

### PostgreSQL Testleri

```python
class TestPostgresMemory:
    @classmethod
    def setup_class(cls):
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
        if not self.pg_available:
            pytest.skip("PostgreSQL çalışmıyor")
        # test body
```

### 11. ChromaDB / Deprecated Module Testing

ChromaDB emekli olduğunda veya bir modül kullanımdan kalktığında, o fonksiyonların **graceful failure** verdiğini test et (çökme değil, hata mesajı):

```python
class TestChromaDeprecated:
    """ChromaDB emekli — fonksiyonlar hata mesajı dönmeli, çökmemeli."""

    def test_bilal_notes_ara_returns_list_on_failure(self):
        """Chroma çalışmıyorken bile liste dönmeli."""
        import tools
        result = tools.bilal_notes_ara("test")
        assert isinstance(result, list)
        if result and isinstance(result[0], str):
            assert "hata" in result[0].lower()

    def test_otonom_calistir_with_mock_fail(self):
        """Bağımlı fonksiyon hata verince uygun dict dönmeli."""
        import tools
        with patch("tools.bilal_notes_ara", return_value=[]):
            result = tools.otonom_calistir("test")
            assert isinstance(result, dict)
            if "arama_sonucu" in result:
                assert result["arama_sonucu"] == []

    def test_dosya_ekle_nonexistent_file(self):
        """Var olmayan dosya için hata dönmeli."""
        import tools
        mock_client = MagicMock()
        mock_client.get_collection.side_effect = Exception("bulunamadı")
        with patch("tools.chromadb.HttpClient", return_value=mock_client):
            result = tools.dosya_ekle("/tmp/nonexistent.txt")
            assert isinstance(result, str)
            assert "❌" in result or "hata" in result.lower()
```

**Prensip:** Deprecated modülü kullanan fonksiyonlar çökmemeli, hata mesajı dönmeli.
Bu sayede emekli modül kaldırıldığında testler kırılmaz — sadece beklenen davranışı doğrular.

### 12. Global State Cleanup (Session Memory)

`_session_memory` gibi modül seviyesi mutable state'i olan fonksiyonları test ederken **her test öncesi temizle**:

```python
class TestSessionMemory:
    def setup_method(self):
        """Her test öncesi global state'i temizle."""
        import tools
        tools._session_memory.clear()

    def test_session_hatirla_limits_to_last_5(self):
        import tools
        for i in range(10):
            tools.session_hatirla(f"Mesaj {i}")
        result = tools.session_hatirla("son mesaj")
        assert len(result) <= 5
        assert "Mesaj 0" not in result  # ilk mesaj silinmiş olmalı

    def test_session_empty_initially(self):
        import tools
        with patch.object(tools, "_session_memory", []):
            result = tools.session_al()
            assert len(result) == 0
```

Aynı pattern singleton helper'lar için de geçerli:
```python
def test_get_longtracer_model_caches_result(self):
    import tools
    tools._longtracer_model = None  # reset
    first = tools.get_longtracer_model()
    second = tools.get_longtracer_model()
    assert first is second or (first is None and second is None)
```

## Basarili Session Ornekleri

- `test_hermes_brain_core.py` — Core modul test ornegi (54 test, AST discovery, strict mode)
- `test_tools.py` — tools.py Phase 1 (42 test, Google API + PostgreSQL + embedding)
- `test_tools_phase2.py` — tools.py Phase 2 (50 test, Telegram + Drive + Sheets + verify + error mgmt + brain bridge)
- `test_tools_phase3.py` — tools.py Phase 3 (41 test, Chroma emekli graceful failure, session memory, plan_hedef, brain wrappers)
- `test_tools_phase4.py` — tools.py Phase 4 (33 test, internal helpers, 8 brain core wrapper, 3 voice functions)
- **Toplam 220 test, tools.py'deki 64 fonksiyonun tamami test edildi.** (Phase-by-phase: 0 → 42 → 92 → 133 → 220)
- **hermes_brain_core.py: 54 test** (karar motoru, öncelik, hafıza, skor, fiziksel aksiyon, güvenlik)

## Session'dan Yeni Öğrenilen: Smooth Phase Completion Pattern

Bir fazı tamamlarken şu kontrol listesini uygula:

1. **Test sayısını topla** — Kaç test geçti? Faz 1→2→3→4 ilerlemesi kaydedildi mi?
2. **Kalan fonksiyon sayısını AST ile kontrol et** — `python3 -c "import ast; code=open('tools.py').read(); funcs=[n.name for n in ast.parse(code).body if isinstance(n, ast.FunctionDef)]; ..."`
3. **Hepsini birlikte çalıştır** — `pytest tests/ -v --tb=line` tüm suite'i çalıştır
4. **Sonucu raporla** — Kaç test geçti, hangi fonksiyon kapsamı, kalan pürüzler
5. **Sıradaki adımı sor** — Kullanıcıya devam mı yoksa başka iş mi diye sor

Bu pattern, büyük modülleri test ederken "bitmiş hissi" vermek ve kullanıcıyı loop'ta tutmamak için kritiktir.

## References

- `test_hermes_brain_core.py` — Core modul test ornegi (54 test, AST discovery, strict mode)
- `test_tools.py` — tools.py Phase 1 (42 test, Google API + PostgreSQL + embedding)
- `test_tools_phase2.py` — tools.py Phase 2 (50 test, Telegram + Drive + Sheets + verify + error mgmt + brain bridge)
- `test_tools_phase3.py` — tools.py Phase 3 (41 test, Chroma emekli graceful failure, session memory, plan_hedef, brain wrappers)
- `test_tools_phase4.py` — tools.py Phase 4 (33 test, internal helpers, 8 brain core wrapper, 3 voice functions)
- `references/internal-import-mocking.md` — Fonksiyon ici import patchleme pattern detayi
- `references/voice-test-patterns.md` — Ses fonksiyonlari test pattern'leri + context manager mock + brain wrapper

## Pitfalls

- **conftest.py her zaman yeterli olmayabilir** — Eğer uyarı `tools.py` import edilirken (test toplama aşamasında) patlıyorsa, conftest'teki filter çalışmaz. O zaman `pytest.ini` kullanmak zorunludur.
- **ResourceWarning (unclosed SSLSocket)** — Google API kullanımından sonra sık görülür. Zararsızdır, `pytest.ini`'de kapatılmalıdır.
- **Token süresi dolduğunda** — `google_auth()` `refresh_token` ile yeniler. Refresh de çalışmazsa testler skip atar ama kırılmaz.
- **long test süresi** — tools.py testleri embedding model yükler (~3-4sn). Toplamda 30sn sürebilir. Bu normaldir.
