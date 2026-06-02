# GSD Redux Integration Notes

## Integration Date
May 24, 2026 — Integrated into Hermes Agent (~/.hermes/gsd/)

## Source
Claude Code framework "Get Shit Done Redux" from `/opt/get-shit-done-redux/`.
The original source was removed after copying — only the Hermes copy survives.

## What Was Integrated

| Component | Count | Path |
|-----------|-------|------|
| Agents | 33 | `~/.hermes/gsd/agents/*.md` |
| Workflows | 88 | `~/.hermes/gsd/workflows/*.md` |
| Templates | 34 | `~/.hermes/gsd/templates/` |
| References | 62 | `~/.hermes/gsd/references/` |
| Contexts | 3 | `~/.hermes/gsd/contexts/` |
| Hooks | 13 | `~/.hermes/gsd/hooks/` |
| Commands | 67 | `~/.hermes/gsd/commands/` |

## Using GSD with Hermes

GSD was designed for Claude Code (agent `.md` files in `/root/.claude/agents/`). Hermes uses a different skill format (`SKILL.md` files), so the integration is as follows:

1. **Agents** → Stored as reference material. Load GSD agent patterns manually via `skill_view(name='gsd')` to see the catalog, then open specific agent files from `~/.hermes/gsd/agents/`.
2. **Workflows** → Structured process guides. Follow the workflow `.md` files step by step.
3. **Hooks** → JavaScript/Shell scripts. Not directly runnable in Hermes but contain useful logic patterns.
4. **Commands** → Claude Code CLI command definitions (e.g., `gsd plan-phase`). Not directly executable.

## Key GSD Agents for Hermes Users

| Agent | Best For | File |
|-------|----------|------|
| gsd-planner | Creating structured execution plans | `agents/gsd-planner.md` |
| gsd-executor | Systematic task execution | `agents/gsd-executor.md` |
| gsd-debugger | Root-cause debugging | `agents/gsd-debugger.md` |
| gsd-code-reviewer | Code quality review | `agents/gsd-code-reviewer.md` |
| gsd-verifier | Implementation verification | `agents/gsd-verifier.md` |
| gsd-research-synthesizer | Research synthesis | `agents/gsd-research-synthesizer.md` |
| gsd-health | System health check | `workflows/health.md` |

## GSD Workflow Example: AI Daily Newsletter

This session produced a working n8n workflow following GSD methodology:

1. **Phase 1 (Research)**: Checked available APIs (HN Algolia, GitHub, Gmail SMTP)
2. **Phase 2 (Plan)**: Designed 9-node workflow with triggers, API calls, AI formatting, email delivery
3. **Phase 3 (Build)**: Created the workflow JSON, pushed to n8n via API
4. **Phase 4 (Verify)**: Activated workflow (partial — emailSend node needs SMTP credential)

**Lesson:** GSD's plan-then-execute approach catches edge cases early (like missing SMTP credentials) that ad-hoc building misses.
