# Kritik Tarih Uyarı Sistemi

## Dosya
- Script: `~/hermes_data/kritik_uyari.py`
- Cron: `~/hermes_data/.hermes/scripts/kritik_uyari.py`
- Her gün 14:15'te sistem crontab'ından çalışır

## Mantık
- 3 gün kala: `⚠️ X işlemine N gün kaldı.`
- Son gün: `🔴 BUGÜN: X işlemini yap!`
- Geçtiyse: `❌ X işleminin tarihi geçti.`

## Şu anki kritik tarihler (Haziran 2026)
- Denizbank ticari kart: 11 Haziran
- Motor sigortası: 14 Haziran
- YK KMH: 15 Haziran

## Cron kurulumu
Hermes cron yerine sistem crontab'ı kullanılıyor (çünkü no_agent script job'ı olarak çalışır):
```
15 11 * * * /usr/bin/python3.11 /home/hermes/hermes_data/kritik_uyari.py >> /home/hermes/hermes_data/kritik_uyari.log 2>&1
```
Not: `crontab -l` boşsa "no crontab for hermes" yazdırır, doğrudan echo ile crontab dosyası oluştur.

## Telegram bildirimi
`tools.py`'deki `telegram_mesaj_gonder()` kullanılır. Nexus bot (token: tools.py içinde) üzerinden gönderilir.
