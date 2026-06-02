# Internal Import Mocking Pattern

## Problem

Birçok fonksiyon bağımlı kütüphaneleri **fonksiyon içinde** import eder (lazy import):

```python
def telegram_mesaj_gonder(mesaj):
    try:
        import requests                     # <-- fonksiyon içinde!
        url = f"https://api.telegram.org/..."
        data = {"chat_id": CHAT_ID, "text": mesaj}
        r = requests.post(url, json=data, timeout=10)
        return r.json().get("ok", False)
    except Exception:
        return False
```

Bu durumda `patch("tools.requests.post")` **çalışmaz** çünkü `tools.requests` diye bir attribute yoktur — `requests` sadece fonksiyon çağrıldığında lokal scope'a yüklenir.

## Çözüm: Modül Seviyesinde Patch

**YANLIŞ:**
```python
with patch("tools.requests.post") as mock_post:  # ❌ tools.requests yok!
```

**DOĞRU:**
```python
with patch("requests.post") as mock_post:  # ✅ doğrudan requests modülü
```

## Yaygın Örnekler

### 1. Telegram (requests.post — iç import)

tools.py:
```python
def telegram_mesaj_gonder(mesaj):
    import requests
    ...
    r = requests.post(url, json=data, timeout=10)
```

Test:
```python
with patch("requests.post") as mock_post:
    mock_post.return_value.json.return_value = {"ok": True}
    result = tools.telegram_mesaj_gonder("Test")
    assert result is True
    # Payload doğrulama:
    args, kwargs = mock_post.call_args
    assert "sendMessage" in args[0]
    assert kwargs["json"]["chat_id"] == "5506784207"
```

### 2. Google Drive (MediaFileUpload — iç import)

tools.py:
```python
def drive_dosya_yukle(dosya_yolu, hedef_klasor="root"):
    ...
    from googleapiclient.http import MediaFileUpload  # iç import!
    media = MediaFileUpload(dosya_yolu, resumable=True)
```

Test:
```python
@patch("tools.google_auth")
def test_drive_yukle_success(self, mock_auth):
    mock_auth.return_value = (MagicMock(), None)
    with patch("tools.build") as mock_build, \
         patch("googleapiclient.http.MediaFileUpload", return_value=MagicMock()):
        ...
```

### 3. Ollama (LLM çağrısı — iç import, timeout riski)

tools.py:
```python
def pg_proaktif_analiz():
    ...
    import ollama
    response = ollama.chat(model='qwen2.5:3b', ...)
```

Test (DB seviyesinde mock — en hızlısı):
```python
def test_pg_proaktif_analiz(self):
    import tools
    with patch("tools.pg_baglan") as mock_baglan:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []  # boş kayıt → "bulunamadı" dalı
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_baglan.return_value = mock_conn
        result = tools.pg_proaktif_analiz()
        assert isinstance(result, dict)
```

## Tespit Yöntemi

Bir modülde hangi import'ların içerde yapıldığını bulmak için:

```python
import ast

def find_internal_imports(path):
    """Bir dosyadaki fonksiyon içi import'ları bulur."""
    with open(path) as f:
        tree = ast.parse(f.read())
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for child in ast.walk(node):
                if isinstance(child, ast.Import) and child != node:
                    for alias in child.names:
                        print(f"  {node.name} → import {alias.name}")
                elif isinstance(child, ast.ImportFrom) and child != node:
                    print(f"  {node.name} → from {child.module} import {[a.name for a in child.names]}")
```

## Tüm İç Import Pattern'leri

| tools.py fonksiyonu | İç import | Test patch hedefi |
|---|---|---|
| telegram_mesaj_gonder | `import requests` | `requests.post` |
| web_cek | `import requests` | `requests.get` |
| drive_dosya_yukle | `from googleapiclient.http import MediaFileUpload` | `googleapiclient.http.MediaFileUpload` |
| pg_proaktif_analiz | `import ollama` | DB seviyesi: `tools.pg_baglan` |
| pg_proaktif_analiz | `import datetime` | (stdlib, patch gerekmez) |
| pg_proaktif_analiz | `import ollama` sonra `ollama.chat` | Boş kayıt döndürerek LLM dalına hiç girme |
