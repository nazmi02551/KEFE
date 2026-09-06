# KEFE AI Lessons Learned & Mistake Prevention

Bu belge, KEFE projesinde yapılmış olan hataları, nedenlerini ve bir daha tekrarlanmaması için alınan kesin önlemleri belgeler.

---

### Ders 1: Soyut Yönetişim Kurallarını Tüketici Mobil Kartı Zannetmek
- **Hata:** `capability-portfolio.v1.tsv` içindeki 128 yetenek (CAP-001 - CAP-128) için 79 adet bağımsız mobil vitrin kartı (`*_card.dart`) yazılıp Keşfet sayfasına yığıldı.
- **Neden Yanlış?:** Bu kuralların çoğu (kriz kararnamesi, lobi radarı, veri kasası, AI halüsinasyon denetimi) sistemin arka plan motoru ve denetim kurallarıdır.
- **Kalıcı Önlem:** Hiçbir mimari/güvenlik kuralı mobil ana sayfaya bağımsız kart olarak konulamaz. Özellikler doğrudan vaka akışına (`DILEMMA`, `DECIDE` simülatörü, `CALL`, `TODAY`) veya vaka içi "Kanıtlar ve Bağlam" sekmesine entegre edilir.

---

### Ders 2: Tipografi ve Dar Row Sıkışması (Dikey Harf Kırılması)
- **Hata:** Kart başlığı sol ikon ve sağ rozet ile aynı dar `Row` içine hapsedildi. Rozet geniş olunca başlığa 50px kaldı ve metin `K\nR\nİ\nZ...` şeklinde hece hece dikey şerit oldu.
- **Kalıcı Önlem:** Başlıklar her zaman tam satır genişliğinde olmalı; rozetler başlığın yanına değil üstüne veya alt bilgi satırına yerleştirilmelidir. Cihaz ekran görüntüsü ile tipografi doğrulanmadan UI işi tamamlanamaz.

---

### Ders 3: Keşfet (Explore) Feed'inin Bozulması
- **Hata:** Keşfet ekranının ortasına 961 satırlık yapay bir `KefeCapabilityShowcaseSection` bloğu sokuldu.
- **Neden Yanlış?:** Product Bible Bölüm 15'e göre Keşfet yalnızca vaka arama, kategori/format filtreleri, Günün Kefesi ve trend vakaları içerir.
- **Kalıcı Önlem:** Keşfet temiz tutulur. Kullanıcı formatları sadece arama barı altındaki format chip'leriyle (`[ Tümü ] [ İkilemler ] [ Simülatörler ] [ Güncel Olaylar ]`) filtreler.

---

### Ders 4: Kod Tabanındaki Değerli Altyapıyı Yok Saymak
- **Hata:** Arayüzdeki kart hatası yüzünden backend servislerini ve domain modellerini de çöpe atma yanılgısı.
- **Gerçek:** Kodda 100 yeteneğin Python backend servisleri, testleri ve Dart domain modelleri zaten yazılmıştır ve %100 değerlidir.
- **Kalıcı Önlem:** Bu modeller korunur, vaka karar akışına (Olay -> Tartım -> Sonuç -> Ortak Zemin / Ayrışma) entegre edilir.
