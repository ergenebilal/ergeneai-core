---
name: n8n-workflow-automation
version: 1.2.0
description: Programmatic n8n workflow management — API auth troubleshooting, database-backed modifications, container filesystem isolation workarounds, and CLI-based export/import patterns
---

# n8n Workflow Automation

Programmatic management of n8n workflows when the REST API is unavailable or container isolation blocks file-based approaches.

## Prerequisites

- n8n running in Docker (Coolify or standalone)
- Docker access on the host (`sudo docker exec`)
- Know the container name (find via `sudo docker ps | grep n8n`)

## Discovery: Check n8n Infrastructure

```bash
# Find container
sudo docker ps --format "{{.Names}} {{.Ports}}" | grep n8n

# Check environment (API key, runner config, etc.)
sudo docker inspect <container-name> --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -i "API\|AUTH\|KEY\|TOKEN"

# Check n8n version and readiness
sudo docker logs <container-name> 2>&1 | grep "n8n ready"
```

## Approach 1: REST API (preferred)

### API Key Discovery
n8n API key can be set via environment variable `N8N_API_KEY` or generated through the UI.

```bash
# Try with existing key
curl -sk -H "X-N8N-API-KEY: <key>" https://n8n.example.com/api/v1/workflows

# If "unauthorized" — key may not exist. Check env:
sudo docker inspect <container> --format '{{range .Config.Env}}{{println .}}{{end}}' | grep N8N_API_KEY
```

### If No API Key Exists
- Option A: Set `N8N_API_KEY` env var and restart container
- Option B: Fall back to Approach 2

## Approach 2: Database + CLI (when API key fails)

### Step 1: Locate the n8n database
The SQLite database is mounted as a Docker volume:

```bash
# Find the volume
sudo docker inspect <container> --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'

# Location typically: /var/lib/docker/volumes/<volume-name>/_data/database.sqlite
```

### Step 2: Copy and query the database
The database is owned by `hermes` user in the volume but the volume directory requires `sudo`:

```bash
# Copy with sudo
sudo cp /var/lib/docker/volumes/<volume-name>/_data/database.sqlite /tmp/n8n_db.sqlite
sudo chown hermes:hermes /tmp/n8n_db.sqlite

# Query with Python 3.11 (has sqlite3 built-in)
python3.11 -c "
import sqlite3
conn = sqlite3.connect('/tmp/n8n_db.sqlite')
conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
cur = conn.cursor()

# List workflows
cur.execute('SELECT id, name, active, isArchived FROM workflow_entity ORDER BY createdAt')
for r in cur.fetchall():
    print(f'{r[0]}: {r[1]} (active={r[2]}, archived={r[3]})')
"

# Get full workflow JSON
cur.execute('SELECT nodes, connections FROM workflow_entity WHERE id=\"<workflow-id>\"')
```

### Step 3: Export workflow via n8n CLI
n8n container has the `n8n` CLI tool:

```bash
# Inside the container
sudo docker exec <container> sh -c "cd /home/node/.n8n && n8n export:workflow --id=<workflow-id> --output=/tmp/workflow.json"

# Copy to host
sudo docker cp <container>:/tmp/workflow.json /tmp/workflow.json
sudo chown hermes:hermes /tmp/workflow.json
```

### Step 4: Modify workflow JSON
Edit the exported JSON. Add new nodes with UUID IDs:

```python
import uuid, json

def uid():
    return str(uuid.uuid4())

# Node structure
new_node = {
    "parameters": {
        "jsCode": "return [{json: $json}];"
    },
    "id": uid(),
    "name": "New Node Name",
    "type": "n8n-nodes-base.code",  # or switch, httpRequest, etc.
    "typeVersion": 2,
    "position": [-960, 920]  # x, y coordinates in n8n canvas
}
```

**CRITICAL**: Understand the connection structure. n8n connections use node **names** as keys:

```json
{
  "Node Name": {
    "main": [
      [{"node": "Target Node", "type": "main", "index": 0}]
    ]
  }
}
```

Switch node routing rules example:
```json
{
  "parameters": {
    "dataType": "string",
    "value1": "={{ $json.field_name }}",
    "routingRules": [
      {"value2": "route1", "outputIndex": 0},
      {"value2": "route2", "outputIndex": 1}
    ],
    "fallback": {"outputIndex": 3, "fallbackOutput": {"value": 0}}
  }
}
```

### Step 5: Import modified workflow

```bash
# Copy modified file to container
sudo docker cp /tmp/workflow.json <container>:/tmp/workflow_modified.json

# Import (replaces existing workflow with same ID)
sudo docker exec <container> sh -c "cd /home/node/.n8n && n8n import:workflow --input=/tmp/workflow_modified.json --id=<workflow-id>"

# IMPORTANT: n8n says changes won't take effect until restart.
# Restart the container:
sudo docker restart <container>
```

### Step 6: Verify

```bash
# Export again and check node count
sudo docker exec <container> sh -c "n8n export:workflow --id=<workflow-id> --output=/tmp/verify.json"
sudo docker cp <container>:/tmp/verify.json /tmp/verify.json
python3.11 -c "
import json
with open('/tmp/verify.json') as f:
    wf = json.load(f)[0]
print(f'Active: {wf[\"active\"]}')
print(f'Nodes: {len(wf[\"nodes\"])}')
"
```

## Container Filesystem Isolation (CRITICAL PITFALL)

**n8n containers do NOT share the host `/tmp` directory.** Writing to `/tmp/n8n_input.json` from the host is invisible inside the n8n container.

**Workaround options:**
1. **HTTP API pattern (recommended)**: Run a local HTTP server on the host (e.g. embedding daemon on port 8767). n8n calls it via `http://host.docker.internal:<port>/endpoint` from an HTTP Request node. See `references/embedding-daemon-n8n-pattern.md` for a full implementation template.
2. **Mounted volume**: Write files to the n8n data volume at `/var/lib/docker/volumes/<volume-name>/_data/` which is mounted to `/home/node/.n8n/` inside the container.
3. **Execute Command node**: Avoid file-sharing; pass data via CLI args (but beware shell escaping issues).

## Node Type Reference

| Type String | Description | typeVersion |
|---|---|---|
| `n8n-nodes-base.code` | JavaScript/Node.js code node | 2 |
| `n8n-nodes-base.switch` | Router/switch node | 1 |
| `n8n-nodes-base.httpRequest` | HTTP request node | 4.2 |
| `n8n-nodes-base.merge` | Merge/join node | varies |
| `n8n-nodes-base.manualTrigger` | Manual trigger | 1 |
| `@n8n/n8n-nodes-langchain.agent` | AI Agent | latest |
| `@n8n/n8n-nodes-langchain.lmChatOpenAi` | OpenAI chat model | latest |
| `@n8n/n8n-nodes-langchain.memoryBufferWindow` | Memory buffer | latest |

## Pitfalls

- **API key timeout**: The key in `~/.n8n-api-key` may be outdated or never generated. Always verify with a test call first.
- **Container restart**: n8n must be restarted after CLI import for changes to take effect.
- **Node IDs**: Each node MUST have a unique UUID `id` field.
- **Connection keys**: Use node **names** (not IDs) as keys in the connections object.
- **Switch outputs**: Switch outputs are 0-indexed arrays. Fallback goes to the last index.
- **Workflow deactivation**: n8n `import:workflow` deactivates the workflow. Reactivate via `publish:workflow --id=<id>`.
- **Database WAL mode**: The SQLite database uses Write-Ahead Logging. Use `PRAGMA wal_checkpoint(TRUNCATE)` when copying to get a consistent snapshot.
- **host.docker.internal availability**: n8n HTTP Request nodes can reach host services via `http://host.docker.internal:<port>`. This works on Coolify's default Docker network and standard Docker setups with `--add-host host.docker.internal:host-gateway`. On bare Docker without this flag, use the gateway IP (`172.17.0.1`) instead.
- **Multiple outputs on existing nodes**: When adding a side branch, existing nodes may already have multiple output connections. For example, "01 Normalize" may route to both "03 Merge" (output 0) and "GET Memory" (output 1). Adding a third path means appending to the existing `main[0]` array — not creating a new output group. Always read the existing connections structure before modifying.
- **n8n import silently succeeds but needs restart**: `n8n import:workflow --id=X` prints "Successfully imported" and deactivates the workflow, but the running engine still uses the OLD version until container restart. Always restart the container after import-and-publish, then verify by re-exporting and checking node/connection count.
- **Python version mismatch**: System `python3` may be 3.10 while pip installed packages for 3.11. Always use `python3.11` explicitly for scripts that need psycopg2, sentence-transformers, chromadb. Check with: `python3.11 -c "import psycopg2; import sentence_transformers; print('OK')"`.
- **n8n import deactivates workflow**: After `n8n import:workflow --id=X`, the workflow is deactivated. You must run `n8n publish:workflow --id=X` AND restart the container for changes to take effect. Without restart, the n8n editor shows the changes but the active engine uses the old version.

## Reference Files

- `references/ergeneai-ig-workflow-switch.md` — Real-world example: Instagram AI Agent workflow modified from 12 to 17 nodes with Intent Check + Switch + HTTP Daemon integration. Contains exact JavaScript code and switch routing configuration.
- `references/embedding-daemon-n8n-pattern.md` — Reusable architecture: run a local HTTP server as n8n backend to avoid container filesystem isolation issues. Full implementation template and design decisions.
