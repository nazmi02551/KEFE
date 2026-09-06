---
trigger: always
---

# KEFE Antigravity Rule: UI, Design System & Typography Guard

Bu kural, KEFE mobil uygulamasının görsel asaletini, tipografisini ve tasarım sistemi bütünlüğünü korur.

## 1. Tasarım Sistemi ve Renk Semantiği
- Ad-hoc, keyfi renk ve stil kullanımı YASAKTIR.
- Sadece `kefeVisual` semantik token'ları kullanılır:
  - **Kurallar / Hukuk / Haklar:** Cyan-Blue
  - **Empati / Vicdan / Merhamet:** Warm Gold / Coral
  - **İmza Vurgusu:** Gold Soft
  - **İkincil / Derinlik:** Burgundy
  - **Yüzeyler:** `surfaceRaised`, `surfaceSunken`, `surfaceStrong`

## 2. Tipografi ve Layout Sıkışma Kalkanı (Dikey Harf Hatası Yasağı)
- **Başlık Sıkıştırma Yasağı:** Kart başlıkları ASLA solundaki ikon ve sağındaki rozet/badge ile aynı dar `Row` içine hapsedilemez.
- Başlık alanı en az tam kart genişliğinde veya başlığın altına serbest akacak şekilde tasarlanmalıdır.
- Türkçe büyük harf kelimelerin (ör. "DEMOKRATİK GÜVENCE", "MEDYA TEKELLEŞMESİ") hece hece alt alta dikey kırılmasına (`K\nR\nİ\nZ...`) neden olan dar container yapıları YASAKTIR.
- Geniş rozetler (ör. "52 Emsal Karar", "Kriptografik Yerel Egemenlik") başlığın yanına değil, başlığın üstüne (eyebrow yanına) veya kartın alt bilgi alanına konulmalıdır.

## 3. 1 Thumb & Derinlik Bütçesi Kuralı
- Çekirdek tüketici akışı (Keşfet -> Vaka -> Tart -> Commit -> Reveal) tek elle (1 Thumb) tamamlanabilmelidir.
- Vaka 5 saniyede anlaşılmalı, 30 saniyede ilk karara varılabilmeli, isteyen 5 dakikada derin kanıtlara inebilmelidir.
- Erişilebilirlik ve Reduce Motion varsayılan olarak desteklenmelidir.
- Düşük donanımlı Android cihazlarda (Xiaomi vb.) sıfır frame-jank hedeflenir.
