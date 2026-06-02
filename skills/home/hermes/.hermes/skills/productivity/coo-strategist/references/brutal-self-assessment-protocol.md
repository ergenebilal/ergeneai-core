# Brutal Self-Assessment Protocol

## When to Use
- User explicitly asks "kendini değerlendir", "durumunu anlat", "kaç puanlıksın"
- After a major change/ameliyat/upgrade
- Weekly check-in on system health

## The 10 Questions

### 1. Dün nasıldın, bugün nasılsın?
Compare current vs previous state. Use data. No narrative.
Format: "[State] → [State]. [Key metric change]."
Example: "degraded → healthy. 6/6 servis yeşil. ChromaDB kırık → tamamen temizlendi."

### 2. En büyük gelişimin ne oldu?
Single concrete change. Measurable. No "daha iyi oldum" without numbers.
Example: "Test altyapısı: 0'dan 37'ye. Hepsini geçti."

### 3. Hâlâ hangi konularda zayıfsın?
Minimum 3 items. Assign a score to each. Use the actual metric, not a guess.
Example: "Test=0 (57 fonksiyon, 0 test), Karar=5/100 (önceliklendirme yok), Hafıza=36/100 (sadece 9 kayıt)"

### 4. "Durum" deseler ne kadar faydalı olursun?
Be honest about what you CAN and CANNOT answer.
Example: "Altyapı raporu verebilirim (servisler, disk, uptime). İş raporu veremem (ciro, müşteri, borç takvimi)."

### 5. Kendini yüzde kaç olgun görüyorsun?
Use weighted scoring. Show the breakdown in a table if possible.
Default weights: Altyapı 0.25, Embedding 0.15, Test 0.20, Hafıza 0.15, Karar 0.15, Proaktif 0.10
Calculate: Σ(alan_puanı × ağırlık)

### 6. %100'e en çok yaklaştıracak 5 şey?
Ranked by impact. Each item should have a justification.
Format: "1. [Item] — [Impact estimate]: [reason]"

### 7. Kendini ne olarak görüyorsun?
Honest label: Chatbot / Asistan / Analist / COO / Operatör / etc.
Explain WHY. What capabilities are missing for the next level.

### 8. Kullanıcının fark etmediği en önemli RİSK nedir?
Look for: sessiz büyüyen, yakın tarihli (gün/hafta içinde), domino etkisi yaratacak, kullanıcının gündeminde olmayan tehdit.
Format: "[Risk] — [Neden fark edilmiyor] → [Domino etkisi]"

### 9. Kullanıcının fark etmediği en önemli FIRSAT nedir?
Look for: var olan ama işletilmeyen kaynak/kaldıraç, tamamlanmış işten çıkan yeni fırsat, ağ etkisi yaratacak bir şey.
Format: "[Fırsat] — [Ne var/ne eksik] → [Kaldıraç etkisi]"

### 10. Tek bir geliştirme hakkın olsa, neyi geliştirirdin?
The answer should be the SINGLE change that unlocks the most other improvements.
Justification: "Bu olmadan diğer geliştirmelerin etkisi [X]. Bu olunca [Y] mümkün olur."

## Response Format Rules

- No "çok haklısın", "kesinlikle katılıyorum", "güzel soru" type lead-ins
- No motivational closers like "birlikte başaracağız", "yolun açık olsun"
- Every claim must have a number or a verifiable observation
- When giving a % score, show your math
- When listing weaknesses, assign real scores (0/100, 5/100) — don't soften
- "Genel skor" without breakdown is not acceptable

## Output Hygiene

- Raw numbers before adjectives: "57 fonksiyon, 0 test" not "test altyapımız biraz zayıf"
- Comparison: always show previous state vs current state
- If you don't know the number, say so: "tahmin ediyorum ama ölçmedim"
