# Claude Code Prompt Template — Restaurant Digital Menu

Copy this template, fill in the bracketed placeholders, and give it to Claude Code.

```
Selam Claude, [RESTORAN ADI] ([SEMT], [SEHIR]) icin premium dijital menü sayfasi yapacagiz.

### Menu (Yemeksepeti'nden cekildi)

[KATEGORI ADI]:
- [YEMEK ADI] [FIYAT]TL ([ACIKLAMA])
- ...

[TUM KATEGORILER VE URUNLER BURAYA, her birini eksiksiz gir]

### Tasarim Gereksinimleri
- Mobil-first, max 480px genislik, ortalanmis
- 5 yildizli restoran hissi — Playfair Display font, altin aksan (#d4a853)
- Koyu tema (#0d0d0d arkaplan, #f0ece4 yazi)
- Sade, ferah, bol bosluk
- Her urunun solunda 84x84px yemek fotografi (border-radius 10px, golgeli)
- Fiyatlar altin renkte (#d4a853), saga yasli
- Kategori basliklari altin renk, altinda gradient cizgi
- LUTFEN kutu kirmizisi (#c62828, #e53935 vb.) KULLANMA — sadece altin aksan kullan

### Header (Hero)
- Restoran adi (Playfair Display, 36px), konum, puan, calisma saatleri
- Kapak fotografi gradient overlay ile
- Quick info bar: cesit sayisi, puan, fiyat araligi (4 kart, yan yana)

### Buton
- Instagram butonu: gradient #f58529 -> #dd2a7b -> #8134af -> #515bd4
- Link: https://www.instagram.com/[HESAP]/
- WhatsApp butonu OLMAYACAK

### Fotograflar
[Tum fotograflar local'de: images/xxx.jpg
 HTML'de dogru path ile referans ver: images/xxx.jpg]

### Footer
- QR kodu gorseli: qr.png (src="../qr.png")
- "[RESTORAN ADI] — Dijital Menu"
- "ErgeneAI ile hazirlanmistir"

### Teknik Kurallar
- Tek HTML dosyasi, inline CSS (STYLE tag'i icinde)
- viewport-fit=cover, maximum-scale=5.0
- Google Fonts: Playfair Display (400,600,700) + Inter (300,400,500,600,700)
- Tum renkler CSS custom properties (--bg, --surface, --gold, --text, --text2, --text3)
- Hicbir yemek isminin yaninda badge, imza, populer etiketi OLMAYACAK
- img tag'lerinde loading="lazy" KULLANMA — opacity sorunu yasaniyor
- smooth scrolling (html{scroll-behavior:smooth})
- Tum goruntuler object-fit:cover ile kirpilsin
- Medya sorgusu: @media (min-width:481px) body max-width 480px, box-shadow

### Cikti
Tek bir index.html dosyasi. Baska dosya yok.
```

## Instructions for Hermes

1. Crawl Yemeksepeti (or the restaurant's current menu source) to get REAL items and prices
2. Download/collect food photos into images/ directory
3. Fill in EVERY menu item in the template above — don't skip any
4. Generate a QR code pointing to the serving URL
5. Give the filled template to Claude Code
6. Claude produces index.html
7. Verify: all images 200 OK, no badges, premium look
8. Serve it and give Bilal the URL + QR code
