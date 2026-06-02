# External Code Discovery Pattern

When the user generates code via an external LLM (DeepSeek, ChatGPT, etc.) and places it on the filesystem, the agent must discover and integrate it — the user won't always announce it.

## Detection

When the user says things like "seni geliştirmeye çalıştım" or "DeepSeek'ten kod yazdırdım", find what changed:

```bash
# Son 24 saatte değişen .py dosyaları
find /home/hermes /opt/hermes -name "*.py" -mmin -1440 2>/dev/null | head -20
```

**Önemli:** Kullanıcı kodları genelde `~/hermes_data/` altına koyar, ama `~/.google/` gibi dizinlerde de config dosyaları olabilir. Geniş tarama yap.

## Integration

1. **Read the files** — Understand what they do
2. **Check credentials/config** — Files may reference paths like `~/.google/credentials.json` — verify those exist
3. **CRITICAL: credentials.json içindeki client_secret farklı olabilir!** Agent'ın daha önce kullandığı secret ile credentials.json'daki secret aynı DEĞİLDİR. Gerçek dosyayı oku, doğru secret'ı kullan.
4. **Check dependency libraries** — `pip3 list | grep` the needed packages
5. **Determine Python version** — Test with `python3.11` first (chromadb, google kütüphaneleri 3.11'de). `python3` (3.10) çoğu özel kütüphaneyi import edemez.
6. **Test standalone** — `python3.11 script.py` to verify syntax and basic functionality
7. **Integrate into tools.py** — Add imports (top) + functions (before print statements at bottom), test with `python3.11 -c "from tools import *"`

## Common Cases

- **Google API scripts** → `google_api.py`, `google_auth_server.py` → integrate into tools.py under `# === GOOGLE API ENTEGRASYONU ===` section. Don't forget the `token.pickle` file path.
- **New OAuth credentials** → Check `~/.google/credentials.json` — the client_secret may differ from what the agent assumed. Verify with `cat ~/.google/credentials.json | jq .installed.client_secret` or `cat ~/.google/credentials.json | python3 -c "import sys,json; print(json.load(sys.stdin)['installed']['client_secret'])"`
- **Existing token** → If `~/.google/token.pickle` exists, the auth is already done. Skip OAuth flow.
