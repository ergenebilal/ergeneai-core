# Beykapı Kebap — Reference Implementation

## URL
http://193.164.4.149:8769/beykapi/
(Server at /home/hermes/demo-menu/beykapi/)

## Source Data
Menu scraped from Yemeksepeti: https://www.yemeksepeti.com/restaurant/kli7/beykapi-kebap-kli7
Product images from: images.deliveryhero.io CDN + Unsplash stock

## What Was Delivered
- Real menu items with real prices (50+ items across 9 categories)
- Real food photography (download + stock fallback)
- Premium dark/gold design (Playfair Display + Inter fonts)
- Instagram CTA button (not WhatsApp)
- QR code for print
- Mobile-first, max-width 480px

## Pricing Delivered
- 4.500 TL teklif hazirlandi (Profesyonel paket)
- AI yemek fotograflari dahil
- 1 yil guncelleme garantili
- QR baski musteriden

## Key Lessons from This Session

### Critical Mistakes Made (DO NOT REPEAT)
1. **First version used emoji placeholders** → user raged ("dandik çalışma")
2. **First version had fake/invented menu items** → user raged harder
3. **Second version had CSS opacity bug** → images invisible because `/loading="lazy"/` with `opacity:0` had no JS to add `.loaded` class
4. **WhatsApp button was wrong** → user wanted Instagram
5. **Domain name (server.keyubu.com) was wrong** → user wanted raw IP
6. **"İmza" badges on food items** → user said remove all labels

### What User Wants (for future)
- "Profesyonel ajans işi" — agency quality, not amateur
- "Mimari kısımda kal, kodlamayı Claude Code halletsin" — Hermes plans, Claude builds
- Düşük fiyattan çok mekana sat (2.500-4.500 TL arası)
- Mudanya restoranları öncelikli
- Google yorumu yüksek ama dijitali kötü olan mekanlar

## Files
- /home/hermes/demo-menu/beykapi/index.html (menu HTML)
- /home/hermes/demo-menu/beykapi/images/ (food photos)
- /home/hermes/demo-menu/beykapi-qr.png (QR code)
- /home/hermes/beykapi-kebap-teklif.html (written proposal)

## Server Setup
- Serving on port 8769 from /home/hermes/demo-menu/
- Python http.server in background
- QR code at /home/hermes/demo-menu/beykapi-qr.png
