# Hesap Kitap Şablonu

Kullanıcı "hesap kitap yapalım" dediğinde izlenecek yapı.

## 1. Anlık Nakit Pozisyonu
- Bugün ne kadar nakit var? (TL)
- Karta yansımayı beklemede ne kadar var?
- Beklenen ödeme (Çarşamba?)
- Bugün kurye yapıldı mı / yapılacak mı?

## 2. Borç Öncelik Sırası
1. Motor sigortası (motorsuz gelir yok)
2. Kredi kartı asgari
3. KMH/kredili mevduat

## 3. Günlük Formül
Kullanıcı kafasında hesaplasın diye:
```
Bu hafta ödenecek toplam / Bu hafta kalan çalışma günü = Günlük hedef
```

## 4. Plan A / B / C
- Plan A: Sadece kurye (en düşük günlük × gün)
- Plan B: Kurye + AI satışı
- Plan C: Kurye + AI satışı + nakit akışı iyileştirme

## 5. Kod: Kritik Tarihler
```python
# ÖNCE stdlib import et (hermes_calendar.py çakışmasını önlemek için)
import calendar
# SONRA user modülü
import sys; sys.path.insert(0, '/home/hermes/hermes_data')
# NOT: takvim.py yerine hermes_calendar.py kullan (calendar.py stdlib çakışması)
from hermes_calendar import takvim_ekle, takvim_bugun
```

## 6. Uygulama Workflow (Kanıtlanmış — 3 Haziran 2026)

Kullanıcı "hesap kitap yapalım" dediğinde sırasıyla:

### 6a. Planı Oluştur
1. `tools.suan()` ile bugünün tarihini al
2. Hafızadaki borç/sigorta/gelir bilgilerini PG'den oku (`tools.pg_son()`)
3. Kritik tarihleri hesapla: "11 Haz = 8 gün kaldı"
4. Günlük hesaplamayı yap: 9.000₺ / 8 gün = ~1.125₺/gün ayırması gerekiyor
5. Çalışma programını çıkar (kurye saatleri + AI satış penceresi)
6. Haftalık aksiyon listesi oluştur (3-5 maddelik)

### 6b. Planı Kalıcı Hale Getir
1. Finansal planı `.md` dosyası olarak `/opt/hermes/` altına yaz
2. PG'ye kaydet: `tools.pg_kaydet(plan_ozeti, category="business_strategy")`
3. Embedding Daemon'a ekle: POST `http://localhost:8767/memory/save` (5 stratejik kayıt)
4. **Günlük check-in cron kur**: Her sabah 09:00 TR otomatik borç hatırlatma

### 6c. Cron'un Prompt Yapısı

```markdown
Bugünün finansal check-in'ini yap.
1. PostgreSQL'den son finansal kayıtları oku (pg_son ile)
2. suan() ile bugünün tarihini al
3. Borçlara kalan gün sayısını hesapla
4. Bugün kurye günü mü kontrol et
5. Kısa brifing ver: tarih, borç durumu, bugünkü odak, 1 net aksiyon önerisi
6. Brifingi tools.pg_kaydet ile business_strategy olarak kaydet
Dil: Türkçe, kısa, samimi
```

### 6d. Embedding Daemon Besleme Şablonu

```bash
curl -sf http://localhost:8767/memory/save -X POST \
  -H "Content-Type: application/json" \
  -d '{"content":"STRATEJIK BILGI","category":"business_strategy|genel|tech_note"}'
```

5 kayıtlık batch önerisi:
- İş modeli tanımı (business_strategy)
- Kullanıcı profili (genel)
- Borç durumu (business_strategy)
- Kurye programı (genel)
- Sistem/teknik not (tech_note)
