---
name: course-to-skill
version: 1.0.0
author: Hermes Agent
description: Extract valuable, actionable knowledge from paid online courses (Skool, Udemy, etc.) and convert into reusable Hermes skills. Covers login, navigation, content extraction, and skill structuring.
---

# Course-to-Skill: Educational Content Mining

Extract the gems from paid course platforms and turn them into reusable Hermes skills. For users who subscribe to educational content and want "cımbızla nokta atışı bilgi" — tweezer-picked knowledge.

## When to Use

- User subscribes to a paid course platform (Skool, Udemy, etc.) and wants you to extract value
- User says "cımbızla nokta atışı bilgi seç ve öğren"
- User wants a dense, actionable summary of a course module, not a full replay
- You need to convert course content into a reusable skill for future sessions

## Workflow

### Phase 1: Access & Authentication

1. **If credentials known** — Use browser to navigate to the course URL directly.
2. **If login required** — Click the LOG IN button, fill email + password fields, click LOG IN.
3. **Session persistence** — Skool sessions expire after inactivity. If you see the about page floating without login, re-login.
4. **URL structure** — Skool uses React Router. The classroom URL pattern is: `https://www.skool.com/<group>/classroom` with optional module params `?md=<32-char-hex>`.

### Phase 2: Module Navigation

1. Navigate to `https://www.skool.com/<group>/classroom` to see all modules.
2. Each module is a `<div role="button">` with:
   - A disabled main button (e.g., `button "🏁 Başlangıç Kampı ..." [disabled, ref=e1]`)
   - A clickable child generic inside it (e.g., `generic [ref=eXX] clickable [onclick]`)
3. Click the **child generic** (not the disabled parent) to open the module.
4. If click navigates, the URL changes to `.../classroom/8be0a507?md=<module-id>`.
5. Module IDs can also be extracted from React's `__NEXT_DATA__` state or DOM regex `md=[a-f0-9]{32}`.

### Phase 3: Content Extraction

1. **Lesson list** — Module shows a list of lessons/videos. Each is a clickable link.
2. **Lesson detail** — Click a lesson to see its description text and video length. Extract via:
   - `browser_console` with `document.body.innerText` for full page text
   - `browser_snapshot` for structured element access
3. **Description extraction** — The lesson description text appears below the video player area. Look for `<p>` / StaticText content after the video title.
4. **Content types** — Course modules typically have:
   - **Video lessons** (18-33min) with text descriptions
   - **System/tool archives** (like 6000+ Hazır Sistem) — different structure, may need alternative access
   - **Documents/templates** — sometimes linked via external URLs

### Phase 4: Knowledge Structuring

Structure extracted content into a Hermes skill:

```
Skill Name: <module-topic-in-turkish>
Category: gsd (or relevant)
Structure:
  - # Title (course module name)
  - ## Key Concepts (core principles)
  - ## Tools & Tech Stack (what tools are covered)
  - ## Practical Workflow (step-by-step)
  - ## Revenue Models (if applicable)
  - ## Quick Start (first 3 lessons to watch)
  - ## Practice Assignment (immediate action item)
```

### Phase 5: Add Supporting Files

- **References** — Add `references/<topic>.md` for session-specific detail (module contents, lesson lists, useful URLs)
- **Keep SKILL.md lean** — The main SKILL.md should be the actionable condensed version (8-14k chars). Detailed lesson lists go in references.

## Skool-Specific Pitfalls

- ❌ **Session expires** — After ~15min of inactivity, Skool logs you out. Re-login required.
- ❌ **Guardrails** — Repeated identical `browser_snapshot` calls trigger idempotent guardrails. After 3 identical results, change strategy (use console, different click, or navigate).
- ❌ **Vision disabled** — If no vision provider is configured (`hermes setup` needed), you cannot use `browser_vision`. Fall back to text extraction.
- ❌ **React dynamic content** — Module links are not `<a>` tags but React onClick handlers. The `browser_snapshot` accessibility tree shows them as `generic [ref=eXX] clickable [onclick]`.
- ❌ **Disabled buttons** — Main module button is `[disabled]`, you must click its child generic.
- ❌ **No direct module URLs** — Module `md` IDs are embedded in React state, not always visible in DOM. Extract via `__NEXT_DATA__` or DOM text search.
- ❌ **6000+ Systems module** — This is a systems archive (not video lessons). Access method may differ from regular video modules. Try clicking the module's child generic to see its structure.

## Common Pitfalls

1. **Over-capturing** — Don't transcribe every lesson title. Tweezer-pick: what's unique, actionable, and non-obvious.
2. **Missing the money** — Every module has revenue implications. Always extract: "how does this make money?" section.
3. **Skill too narrow** — Name the skill at the class level (e.g., `agentic-sistemler` not `antigravity-video-rehberi`).
4. **No references directory** — Session-specific detail (full lesson lists, URLs) belongs in `references/`, not bloating SKILL.md.

## Verification Checklist

- [ ] Skill covers the ESSENCE of the module (not every detail)
- [ ] Revenue/application angle extracted
- [ ] SKILL.md ≤ 15k chars, detail in `references/`
- [ ] Skill name is class-level, not session-specific
- [ ] Credentials saved to memory for next access
