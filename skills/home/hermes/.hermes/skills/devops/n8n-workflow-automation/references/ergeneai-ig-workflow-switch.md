# ErgeneAI Instagram AI Agent — Workflow Modification Reference

## Original Workflow (12 nodes, active, ID: 3ngLwcqxlAKWiuug)

### Flow
```
Instagram Trigger
  → 01 Normalize Instagram DM (Code)
      → [main 0] 03 Merge Original DM + AI Reply
      → [main 1] GET Conversation Memory (HTTP → memory server:8899)
GET Conversation Memory
  → Enrich Context with Memory (Code)
  → 02 AI Agent - ErgeneAI Assistant (LangChain Agent)
💭 Hafiza (Memory Buffer Window) → AI Agent (ai_memory)
OpenAI Chat Model (gpt-4o-mini) → AI Agent (ai_languageModel)
AI Agent
  → Score Lead Quality (Code)
  → Telegram Rapor Gonder (Code)
  → Save Conversation to Memory (Code)
  → [main 1] 03 Merge Original DM + AI Reply
03 Merge → Send direct message (Instagram API)
```

### AI Agent Configuration
- Model: gpt-4o-mini, temperature 0.4
- System message: Turkish, customer-facing, no technical terms. 3-message max conversation flow.
- Memory: Buffer window (session-based)

## Added: Intent Check + Switch + HTTP Daemon Pattern (5 new nodes)

### Trigger Condition
User message contains: "kaydet", "not et", "hatirla", "unutma" → save_memory
User message contains: "ara", "bul", "ne yaziyordu", "soylemistin" → search_memory

### Flow Addition
```
01 Normalize Instagram DM
  → [new main output 2] 04 Intent Check (Code)
  → 05 Switch (Intent Router)
      → Route 0 (save_memory): 06 HTTP Save → POST host.docker.internal:8767/memory/save
      → Route 1 (search_memory): 07 HTTP Search → POST host.docker.internal:8767/memory/search
      → Route 3 (fallback/casual_chat): 08 Passthrough
06/07 → 08 Passthrough
08 → Score Lead Quality (existing flow continues)
```

### Intent Check Code Node (04 Intent Check)
```javascript
const text = ($json.text || $json.body || $json.prompt || "").toLowerCase();
let intent = "casual_chat";
let payload = {};

if (text.includes("kaydet") || text.includes("not et") || text.includes("hatirla") || text.includes("unutma")) {
  intent = "save_memory";
  payload = { content: $json.text || $json.body || $json.prompt || "", category: "genel" };
} else if (text.includes("ara") || text.includes("bul") || text.includes("ne yaziyordu") || text.includes("soylemistin")) {
  intent = "search_memory";
  payload = { sorgu: $json.text || $json.body || $json.prompt || "", limit: 3 };
}

return [{ json: { ...$json, _hermes: { intent, payload } } }];
```

### Switch Node Details
- Property: `={{ $json._hermes.intent }}`
- Type: String
- Routing Rules: save_memory → output 0, search_memory → output 1
- Fallback: output 3 (casual_chat passthrough)

### Daemon Endpoints
- `POST http://host.docker.internal:8767/memory/save` — body: {content, category}
- `POST http://host.docker.internal:8767/memory/search` — body: {sorgu, limit, esik}
- Timeout: 5 seconds (non-blocking — if daemon is down, main flow continues)
