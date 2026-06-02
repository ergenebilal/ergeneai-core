---
name: digital-menu-service
description: Full-stack digital menu service for local restaurants — Crawl4AI scanning, premium HTML/CSS menu building with Claude Code, face-to-face sales workflow, pricing strategy, and delivery.
version: 1.0.0
author: ErgeneAI
tags: [digital-menu, restaurant, local-business, crawl4ai, claude-code, sales, premium-design]
---

# Digital Menu Service — Full Playbook

## Overview

Turnkey local business service: scan restaurants → identify weak digital presence → build premium mobile menus with real photos → sell face-to-face → deliver with QR codes.

## CRITICAL Quality Rules

1. **NEVER use emoji placeholders for food photos** — real images only. Violation = trust destroyed.
2. **NEVER make up menu items or prices** — scrape real data from Yemeksepeti. Fakery = trust destroyed.
3. **Design must look 5-star level** — gold accents, premium fonts, dark theme.
4. **IP address URL acceptable for demo** — mention domain upgrade for professional clients.

## Design Template

- Font: Playfair Display (headings) + Inter (body)
- Theme: Dark (#0d0d0d bg), Gold accent (#d4a853)
- Width: max 480px, mobile-first
- Hero: cover photo + gradient overlay
- Items: 84x84px image | name+desc | price (gold, right-aligned)
- CTA: Instagram button ONLY (no WhatsApp)
- Footer: QR code + "Powered by ErgeneAI"

## Workflow

### 1. SCAN (Hermes / Crawl4AI)
Check restaurant directories for: has_menu, has_photos, has_prices. Target: menu=YES, photos=NO.
Anti-bot note: menuburada blocks scrapers. Use Yemeksepeti as fallback for real data.

### 2. BUILD (Claude Code)
Prompt template:
```
ECC agent'larini kullan (planner + code-reviewer).
[MUSTERI] icin premium mobil menu HTML'i.
Icerik (Yemeksepeti verisi): [urun] [fiyat]TL
Tasarim: gold aksan, koyu tema, Playfair Display, 480px max
Instagram butonu, WhatsApp yok. 5 yildizli restoran hissi.
Cikti: index.html + images/
```

### 3. SELL (Face-to-face)
Show Beykapi reference demo on laptop. Stay silent, let them scroll.
Pitch: "2.500 TL, QR kodu basarim masalara koyarsin."
Hesitation: "Su anki menunde fotograf yok, musteri ne yiyecegini gormuyor."

### 4. DEPLOY
```bash
mkdir -p /home/hermes/demo-menu/[name]/images
cp index.html images/* /home/hermes/demo-menu/[name]/
python3.11 -c "import qrcode; qrcode.make('http://193.164.4.149:8769/[name]/').save('/home/hermes/demo-menu/[name]-qr.png')"
# Server: cd /home/hermes/demo-menu && python3 -m http.server 8769
```

## Pricing
- **Başlangıç**: 2.500 TL (QR menu + photos + Instagram)
- **Profesyonel**: 4.500 TL (+ IG content calendar)
- **Kurumsal**: 8.000 TL (+ n8n automation)

## Target Selection
1. Menu exists online BUT no food photos
2. Good Google reviews (4.0+) but weak website
3. On Yemeksepeti (data available) but own site basic
4. Physically accessible for face visit

## Verification
- [ ] Prices match Yemeksepeti exactly
- [ ] All images load (200 OK)
- [ ] Instagram link correct
- [ ] No WhatsApp button
- [ ] Mobile-friendly under 480px
- [ ] Gold accent consistent
- [ ] No emoji food placeholders
