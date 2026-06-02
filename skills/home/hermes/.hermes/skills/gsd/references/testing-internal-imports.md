# Testing Python Modules with Internal Imports

## The Core Problem

When a Python module imports dependencies **inside function bodies** (not at module level), `unittest.mock.patch("module.dependency")` fails with `AttributeError: module 'X' has no attribute 'Y'`.

### Why This Happens

```python
# tools.py — function-level import
def telegram_mesaj_gonder(mesaj):
    import requests  # ← NOT at module level!
    ...
```

```python
# ❌ THIS FAILS — 'requests' is not an attribute of 'tools'
with patch("tools.requests.post") as mock_post:
    tools.telegram_mesaj_gonder("test")
# → AttributeError: module 'tools' has no attribute 'requests'
```

## The Fix: Patch at Source

Patch the **canonical import path** — where the dependency lives in the package namespace, not where it's used:

### Pattern 1: Standard Library / PyPI package
```python
# tools.py: def telegram_mesaj_gonder(mesaj):
#     import requests  ← function-level import with bare 'import requests'

# ✅ PATCH AT SOURCE
with patch("requests.post") as mock_post:
    tools.telegram_mesaj_gonder("test")
```

### Pattern 2: Submodule import inside function
```python
# tools.py: def drive_dosya_yukle(dosya_yolu):
#     from googleapiclient.http import MediaFileUpload  ← internal import

# ✅ PATCH AT SOURCE
with patch("googleapiclient.http.MediaFileUpload", return_value=MagicMock()):
    tools.drive_dosya_yukle("/tmp/test.txt")
```

### Pattern 3: Cross-module import inside function
```python
# tools.py: def hermes_ses_dosyasi_uret(metin):
#     from hermes_brain_core import build_tts_request  ← cross-module import

# ✅ PATCH AT SOURCE
with patch("hermes_brain_core.build_tts_request", return_value={...}):
    tools.hermes_ses_dosyasi_uret("test")
```

### Pattern 4: Internal module function called by another
```python
# tools.py: def _get_embedding(text):
#     model = _get_embedding_model()  ← calls another module-level function

# ✅ PATCH AT MODULE LEVEL
with patch("tools._get_embedding_model", return_value=None):
    tools._get_embedding("test")
```

## Anti-Pattern: What NOT to Do

```python
# ❌ NEVER PATCH tools.submodule when submodule is imported inside a function
patch("tools.requests.post")      # ← tools.requests doesn't exist
patch("tools.MediaFileUpload")    # ← tools.MediaFileUpload doesn't exist  
patch("tools.build_tts_request")  # ← tools.build_tts_request doesn't exist

# These all fail with: AttributeError: module 'tools' has no attribute 'X'
```

## Quick Reference Table

| Function import style | Patch target |
|---|---|
| `import requests` inside function | `"requests.post"` |
| `from X import Y` inside function | `"X.Y"` |
| `from .X import Y` (relative) inside function | `"package.X.Y"` |
| Calls another module-level function `fn()` | `"module.fn"` |
| Uses `from X import Y` at module level | `"module.Y"` (module-level attribute exists) |

## How to Detect

Run the test. If you get:
```
AttributeError: <module 'tools' from '/path/to/tools.py'> does not have the attribute 'requests'
```

The dependency is imported inside a function body. Open the source and check whether the `import` statement is at the top of the file or nested inside a `def`.

## Phase-based Test Organization

For large modules (50+ functions), use a phase-based approach:

```
Phase 1: Core infrastructure (Gmail, Calendar, PG)
Phase 2: Business operations (Telegram, Drive, Sheets)
Phase 3: Deprecated code + wrappers
Phase 4: Internal helpers + voice
```

Each phase:
- Tests 8-18 functions
- Covers real behavior AND mock paths
- Ends with a **discovery test** (`test_phaseN_functions_exist`) that proves every tested function exists in the source
- Runs independently — parallel execution is safe

### Discovery Test Pattern
```python
def test_phaseN_functions_exist():
    """Phase N'de test edilen tüm fonksiyonlar var mı."""
    import ast
    tree = ast.parse(TOOLS_PATH.read_text(encoding="utf-8"))
    fnames = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }
    expected = {"fn1", "fn2", ...}
    missing = expected - fnames
    assert not missing, f"Eksik fonksiyonlar: {missing}"
```
