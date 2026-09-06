---
trigger: always
---

# KEFE Antigravity Rule: Verification, Cross-Window & Execution Discipline

Bu kural, projede yapılan geliştirmelerin test edilmesini, farklı pencereler/modeller arasında kesintisiz devamlılığı ve operasyonel disiplini garanti eder.

## 1. Çapraz Pencere ve Devamlılık Disiplini (Cross-Window Continuity)
- Yeni bir oturum açıldığında veya model değiştiğinde:
  1. `git status --short --branch` ve `git log -3 --oneline` çalıştırılarak mevcut durum doğrulanır.
  2. `.ai/STATUS.md` ve `docs/status/CURRENT.md` okunarak kalınan tam nokta belirlenir.
  3. Kullanıcıya "Geçmişte ne yaptık?" diye sorulmaz; doğrudan durable state'ten devam edilir.

## 2. Kanıt ve Doğrulama Zorunluluğu (Evidence Discipline)
- "Kod yazdım, bitti" demek KESİNLİKLE YASAKTIR.
- Her kod değişikliğinden sonra:
  - Python Backend: `py -m pytest services/api/tests/` hatasız geçmelidir.
  - Mobil UI: `flutter analyze` 0 hata vermeli ve canlı cihazda (Xiaomi Redmi Note 13) ADB üzerinden ekran görüntüsü alınarak doğrulanmalıdır.
  - Portföy: `py scripts/validate_capability_portfolio.py` PASS vermelidir.
- Test komutları başarıyla tamamlanmadan hiçbir iş "DONE" ilan edilemez.

## 3. Kod Koruma ve İlerleme Kuralı
- Kod tabanında geliştirilmiş olan 100 yeteneğe ait Python backend servisleri, testleri ve Dart domain modelleri çok değerlidir; ASLA silinmez.
- Eksik olan şey backend değil; bu modellerin vaka akışına (Case Flow) bağlanmasıdır.

## 4. Git Hijyeni
- Asla `git add .` kullanılmaz; yalnızca ilgili ve üzerinde çalışılan dosyalar stage edilir.
- Çalışma ağacı (working tree) asla varsayımsal olarak temiz kabul edilmez.
- Anlamlı her aşamadan sonra `.ai/STATUS.md` güncellenir.
