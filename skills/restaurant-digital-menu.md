---
name: restaurant-digital-menu
description: Create premium digital menus for restaurants using real menu data, real food photography, and mobile-first design. Full workflow from scraping to client delivery.
category: software-development
---

# Restaurant Digital Menu

## Role Split (CRITICAL)

**Hermes (this agent) = Architecture, Strategy, Lead Gen, QA**
- Crawl4AI ile mekan tara, fırsatları bul
- Müşteri listesi çıkar, ön analiz yap
- Claude Code için prompt yaz (mimariyi sen belirle)
- Çıkan işi kontrol et, kaliteyi onayla
- **Kod YAZMA.** Claude Code'a bırak.

**Claude Code = Implementation**
- Prompt'u alır, index.html'i yazar
- Fotoğrafları yerleştirir, tasarımı uygular
- Sadece senin verdiğin prompt kadarını yapar

**Bilal = Sales & Delivery**
- Müşteriye WhatsApp/telefon atar
- Yüz yüze demo yapar
- QR kodu bastırır, teslim eder, parayı alır

## Core Principles

**NO FAKE DATA. EVER. PROFESSIONAL AGENCY QUALITY ONLY.**
The user will RAGE if you present fake data or emoji placeholders. This is the #1 rule. He said:
- "bu ne dandik bir çalışma amına koyayım senden bunu mu istedim ben!"
- "profesyonel ajans işi ile gel. böyle kıytırık işler çıkardığını bir daha görmeyeceğim."

Always:
- Get REAL menu items with REAL prices from Yemeksepeti or the restaurant's actual menu
- Use REAL food photos (from delivery service CDNs, Unsplash, or the restaurant's own images)
- NEVER use emoji placeholders instead of actual food photography
- NEVER invent menu items or prices
- NEVER present a half-finished demo — complete it before showing

**Premium quality is non-negotiable.** This must look like a 5-star restaurant menu on mobile:
- 5-star restaurant menu aesthetic — think fine dining, not fast food
- Dark/gold premium color scheme (not aggressive reds like #c62828 or #e53935)
- Playfair Display serif font for headers, Inter for body
- Clean, wide spacing, elegant typography
- Mobile-first (max-width 480px centered), smooth scrolling
- No clutter, no unnecessary badges, no "İmza" / "Popüler" labels

## Phase 0 — Lead Generation (Scanning)

Before any coding, scan for opportunities. This is the most important phase.

### Method

```bash
# 1. Web search for restaurants in target area
web_search(query="Bursa Mudanya restoran kebap cafe 2026")
web_search(query="Mudanya restoran en iyi yorumlar google mekanlar")

# 2. Crawl restaurant directories to find candidates
# menuburada.com has categorized restaurant lists per district
# menuler.com.tr has menu data
# Yemeksepeti has real menus with prices

# 3. For each candidate, assess digital presence:
python3.11 -c "
import asyncio
from crawl4ai import AsyncWebCrawler
async def analyze():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url='RESTAURANT_URL')
        if result.success:
            text = result.markdown
            print(f'Menu: {\"VAR\" if \"menu\" in text.lower() else \"YOK\"}')
            print(f'Photo: {\"VAR\" if \"foto\" in text.lower() else \"YOK\"}')
            print(f'Price: {\"VAR\" if \"tl\" in text.lower() else \"YOK\"}')
asyncio.run(analyze())
"
```

### Criteria — Good Prospect = Reviews HIGH + Digital LOW

| Signal | Target |
|---|---|
| Google/TripAdvisor puanı | 4.0+ (müşterisi bol) |
| Menüde yemek fotoğrafı | YOK (işte fırsat burada) |
| Mevcut QR menü varsa | İçerik bok gibi, sadece yazı + fiyat |
| Web sitesi | Zayıf veya hiç yok |

### Top Prospects (from this session)
- Mudanya: Yıldıztepe Cafe (fotoğraf yok), 21 Masa (fotoğraf yok)
- Nilüfer: Beykapı Kebap (fotoğraf yok), Mustafa Ciğer Kebap (fotoğraf yok)

### Output Format

For each prospect, prepare a 3-line summary:
```
📍 Mekan Adı — Semt
   ⭐ Google puanı: 4.X (N yorum)
   ⛔ Eksik: Fotoğrafsız menü / kötü web sitesi / QR var içerik yok
   💰 Teklif: 2.500₺ Başlangıç paketi
```

## Business Model & Pricing

### Paketler

| Paket | Fiyat | İçerik |
|---|---|---|
| 🔥 Başlangıç | 2.500₺ | QR menü + AI fotoğraflar + Instagram butonu |
| ⭐ Profesyonel | 4.500₺ | Yukarıdaki + 12 post/ay Instagram içerik takvimi |
| 👑 Kurumsal | 8.000₺ | Yukarıdaki + n8n sipariş otomasyonu + müşteri takip |

### Strateji
- Düşük fiyattan ver, çok mekana sat (volume play)
- 2.500₺'den 10 mekan = 25.000₺
- Haftada 2 mekan = ayda 8 mekan = ~20.000₺ ek gelir
- Tek seferlik işler — abonelik yok, basit, hızlı teslimat
- Her mekan için: Hermes tarama (20dk) + Claude Code montaj (1 saat) + Bilal teslimat (30dk)

### Satış Konuşması

```
Abi merhaba, [mekan adı] için dijital menü hazırladım.
Şu an menünüzde yemek fotoğrafı yok.
Aynı menünüzü aldım, sadece fotoğrafları ekledim.
QR koy masaya, müşteri okutur, görür.
2.500 TL tek seferlik, AI fotoğraflar dahil.
```

### Weekly Workflow Rhythm

| Gün | Hermes | Claude Code | Bilal |
|---|---|---|---|
| Pazartesi | 30 mekan tara + analiz | - | Motor full |
| Salı | 5 lead hazırla | 2 menü montajla | Motor + akşam 1 WhatsApp |
| Çarşamba | - | 2 menü montajla | Motor + akşam 1 WhatsApp |
| Perşembe | Yeni tarama | 1 menü montajla | Motor + teslimat |
| Cuma | Haftalık rapor | - | Motor + teslimat |
| Haftasonu | - | Batch hazırlık | Teslimat + yeni müşteri |

## Claude Code Prompt Template

Copy-paste for each new restaurant menu. Fill in the placeholders.

```
Selam Claude, [RESTORAN ADI] ([SEMT], [ŞEHIR]) icin premium dijital menü sayfasi yapacagiz.

### Menu (Yemeksepeti'nden cekildi)

[KATEGORI ADI]:
- [YEMEK ADI] [FIYAT]TL ([ACIKLAMA])
- ...

[TUM KATEGORILER VE ÜRÜNLER BURAYA]

### Tasarim Gereksinimleri
- Mobil-first, max 480px genislik
- 5 yildizli restoran hissi — Playfair Display font, altin aksan (#d4a853)
- Koyu tema (#0d0d0d arkaplan, #f0ece4 yazi)
- Sade, ferah, bol bosluk
- Her ürünün solunda 84x84px yemek fotografi (border-radius 10px, golgeli)
- Fiyatlar altin renkte (#d4a853)
- Lutfen kutup kirmizisi (#c62828 vs) KULLANMA, sadece altin aksan kullan

### Header
- Restoran adi (Playfair Display), konum, puan, calisma saatleri
- Quick info bar: cesit sayisi, puan, fiyat araligi

### Buton
- Instagram butonu: gradient #f58529→#dd2a7b→#8134af→#515bd4
- Link: https://www.instagram.com/[HESAP]/ (öğrenemediysen koyma)
- WhatsApp butonu OLMAYACAK

### Fotograflar
[FOTOGRAF DOSYALARINI BELIRT]
(resimler local'de, sadece HTML'de dogru path ile referans ver: images/xxx.jpg)

### Footer
- QR kodu (qr.png)
- "[RESTORAN ADI] — Dijital Menü"
- "ErgeneAI ile hazirlanmistir"

### Teknik
- Tek HTML dosyasi, inline CSS
- viewport-fit=cover, maximum-scale=5.0
- Google Fonts: Playfair Display (600,700) + Inter (300-700)
- Renk degiskenleri CSS custom properties kullan
- Tüm fotograflar local'den yüklenir (images/ klasörü)
- Hicbir yemek isminin yaninda badge/imza/popüler etiketi OLMAYACAK
- smooth scrolling

### Çikti
Tek bir index.html dosyasi olarak çikti ver.
```

## Workflow Steps

### 1. Research — Get REAL Menu Data

```bash
# Crawl Yemeksepeti for the restaurant's actual menu
python3.11 -c "
import asyncio
from crawl4ai import AsyncWebCrawler
async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url='https://www.yemeksepeti.com/restaurant/XXXXX/restaurant-name')
        if result.success:
            print(result.markdown)
asyncio.run(main())
"
```

Extract: category names, product names, prices, descriptions, and image URLs (from `images.deliveryhero.io`).

### 2. Collect REAL Food Photos

```bash
# From Yemeksepeti CDN (real product images)
curl -sL "https://images.deliveryhero.io/image/fd-tr/products/PRODUCT_ID.jpg?width=400&height=300" -o item.jpg

# From Unsplash (stock food photography as fallback)
curl -sL "https://images.unsplash.com/photo-XXXX?w=400&h=300&fit=crop" -o item.jpg
```

Always try Yemeksepeti CDN first for real product images. Fall back to Unsplash for items without CDN photos.

### 3. Design the Menu

CSS Variables to use:
```css
--bg: #0d0d0d;
--surface: #141414;
--gold: #d4a853;
--text: #f0ece4;
--text2: #a09888;
--text3: #605848;
```

- Header: Cinematic hero image with gradient overlay, Playfair Display title
- Info bar: Stats cards (çeşit, puan, fiyat aralığı)
- CTA: Instagram button (gradient #f58529 → #515bd4), NOT WhatsApp unless specified
- Menu items: Image (84x84px) + name + description + gold price
- Category headers: Gold text with subtle underline gradient
- Footer: QR code + branding

Pitfalls:
- ❌ Do NOT use `[loading="lazy"]` with `opacity: 0` CSS without JS to add a `.loaded` class — images stay invisible. Either use JS to handle load events, or skip the lazy-load fade-in entirely.
- ❌ Do NOT add "İmza", "Popüler", or any badge text next to food names unless the client explicitly asks for it.
- ❌ Do NOT use WhatsApp as the default CTA button. Ask or default to Instagram.
- ❌ Do NOT use a domain name unless the user explicitly says to. Default to IP address.
- ❌ Do NOT use emojis (🥩, 🥙, etc.) as food images. Only real photos.
- ✅ Always verify all images return HTTP 200 before presenting.

### 4. Serve the Demo

```bash
cd /path/to/demo/dir
python3 -m http.server PORT --bind 0.0.0.0
```

Generate QR code:
```bash
pip install qrcode[pil] -q
python3.11 -c "import qrcode; qrcode.make('http://IP:PORT/PATH/').save('qr.png')"
```

### 5. Client Pitch

Keep it simple. Show the live demo on your phone and say:
> *"Şu an menünüzde yemek fotoğrafı yok. Aynı menünüzü aldım, sadece fotoğrafları ekledim. QR koy masaya, müşteri okutur, görür."*

Pricing standard: 4,500 TL tek seferlik, AI fotoğraflar dahil, 1 yıl güncelleme bedava.

## Quality Gates (before presenting to user)

1. All images load (HTTP 200)
2. Menu items match Yemeksepeti exactly (same names, same prices)
3. No emoji placeholders
4. No fake/generated menu items
5. Mobile-responsive (max-width: 480px centered)
6. Premium feel (gold accents, serif fonts, proper spacing)

## Pitfalls

- The user will RAGE if you present fake data or emoji placeholders. This is the #1 rule.
- CSS opacity/loading animations can hide images if not implemented correctly. Always verify visually.
- Don't over-engineer with JS frameworks. Static HTML + CSS is sufficient.
- Keep the design dark + gold. No bright colors, no aggressive reds.
- Do NOT use domain names like server.keyubu.com unless user approves.
