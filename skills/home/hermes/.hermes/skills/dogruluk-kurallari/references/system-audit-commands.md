# Sistem Denetim Komutları

1 Haziran 2026'da kullanılan ve doğrulanan sistem denetim komutları.

## Process Kontrolü
```bash
ps aux | grep [servis_adi]
ps aux | grep -i hermes
ps aux | grep -i n8n
```

## Port Dinleme
```bash
ss -tlnp | grep [PORT]
ss -tlnp | grep -E "8642|8644|8765|8001"
lsof -i :[PORT]
```

## Docker
```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
docker ps --format '{{.Names}} {{.Status}} {{.Ports}}'
ls -la /var/run/docker.sock
```

## HTTP Health Check
```bash
curl -s http://localhost:[PORT]/health
curl -s http://localhost:[PORT]/api/v1/health
curl -s http://localhost:[PORT]/
```

## Paket Kontrolü
```bash
pip show [paket_adi]
pip list | grep [paket]
npm list -g [paket]
which [komut_adi]
```

## Dosya Sistemi
```bash
ls -la /path/to/dir
find / -name "[pattern]" 2>/dev/null | head -5
cat /proc/[PID]/cmdline | tr '\0' ' '
cat /proc/[PID]/environ | tr '\0' '\n' | grep -i [keyword]
```

## ChromaDB Özel
```bash
curl -s http://localhost:8001/api/v1/heartbeat
curl -s http://localhost:8001/api/v2/collections
python3.11 -c "import chromadb; c=chromadb.HttpClient(host='localhost', port=8001); print(c.heartbeat())"
```

## n8n Özel

n8n Docker/Coolify içinde çalışıyor. Host'ta port görünmez.
```bash
# Healtcheck
curl -sk https://n8n.aiergene.xyz/healthz
# → {"status":"ok"}

# API (auth gerekli)
cat ~/.n8n-api-key | xargs -I {} curl -sk "https://n8n.aiergene.xyz/api/v1/workflows" -H "X-N8N-API-KEY: {}"

# Process kontrol
ps aux | grep n8n
# PID 2560037, node /usr/local/bin/n8n

# MCP uzerinden erisim (tools ile)
# mcp_n8n_list_resources, mcp_n8n_get_node, mcp_n8n_search_nodes
```

## Python 3.11 Özel

ChromaDB + sentence-transformers **sadece Python 3.11'de** kurulu.
```bash
# DOĞRU
python3.11 -c "import chromadb; import sentence_transformers; ..."
```

## 1 Haziran 2026 Denetim Sonuçları

### Çalışan Servisler (doğrulandı)
- Hermes Gateway: 8642/8644 ✅
- Hermes MCP Server: 8765 ✅
- n8n: Docker/Coolify ✅ (API erişilemez)
- ChromaDB: 8001 ✅
- Crawl4AI: Python 3.11 ✅
- Hyperframes: npm global 0.6.65 ✅
- Ollama: 11434 ✅ (qwen2.5:3b + nomic-embed-text)
- Browser-Use: pip 0.12.9 ✅
- Insta Memory Server: 8899 ✅
- Nanobot Gateway: 18790/8766 ✅
- Demo Menu: 8769 ✅
- Coolify: 8000 ✅
- Cron jobs: ~12 adet ✅

### Çalışmayan / Eksik (hallüsinasyon)
- PilotDeck: port 18789/3001 ❌
- Kabine Chat: port 8767 ❌
- Gemini web2api: klasör yok, 8080 boş ❌
- model_switch.sh: bulunamadı ❌

### Skill Durumu

- 212 skills kayıtlı (skills_list)
- 9 Hermes skill (SKILL.md var)
- 199 ECC skill (sembolik link, kullanılabilir)
- 4 boş/ulaşılamaz

**ECC Skill Erişimi:**
ECC skill'leri `~/.hermes/skills/ecc/ → ~/.claude/skills/ecc/` sembolik link ile bağlı.
`skill_view(name)` ile doğrudan yüklenebilir. Test et: `skill_view(name='blueprint')`

**Permission Kontrolü:**
~/.hermes/skills/ altında SKILL.md kontrol ederken:
```bash
# YANLIŞ — permission denied'ı "yok" sayar
[ ! -f "SKILL.md" ]

# DOĞRU
sudo ls -la "SKILL.md" 2>/dev/null
find /home/hermes/.hermes/skills -name "SKILL.md" 2>/dev/null | wc -l
```
