# KEFE Kapsamlı Sistem Mimarisi, Mantık Çerçevesi ve Katman Ayrım Raporu

**Tarih:** 7 Eylül 2026  
**Otorite Belgeleri:** `docs/ecosystem_v3.3/.../ACTIVE/` altındaki 18 Onaylı Baseline Dokümanı:
- `KEFE_Master_Product_Document_v1.2.0_Approved_Canonical`
- `KEFE_Product_Bible_v1.4.0_Working_Baseline`
- `KEFE_AI_Architecture_v1.1.0_Approved_Baseline`
- `KEFE_Admin_Studio_Specification_v1.2.0_Approved_Baseline`
- `KEFE_Design_System_v1.1.0_Approved_Baseline`
- `KEFE_Engineering_Blueprint_v0.6.0_Implementation_Contract_Baseline`
- `KEFE_Content_Question_Design_Bible_v1.1.0_Approved_Baseline`
- `KEFE_Trust_Integrity_Methodology_Standard_v1.1.0_Approved_Baseline`

---

## 1. KEFE'nin Temel Mantığı ve Varoluş Felsefesi (The Philosophy)

> **"Kural ne diyor, vicdan ne söylüyor?"**  
> *(Sakin, meraklı, yargılamayan, premium ama erişilebilir.)*

KEFE bir sosyal medya platformu, anket sitesi veya tartışma forumu değildir. 

### Varoluş Sebebi:
1. **Manipülasyon ve Yankı Odalarını Kırmak:** Günümüz internetinde insanlar bir haber veya olay gördüğünde önce başkalarının ne düşündüğünü (beğeni sayıları, linç kampanyaları, algoritmik kutuplaşma) görür ve kararlarını bu sosyal baskı altında verir.
2. **Kör Karar İlkesi (Commit First / Blind First):** KEFE'de kullanıcı, bir ikilem karşısında **başkalarının ne oy verdiğini, çoğunluğun nerede durduğunu veya uzman görüşünü görmeden önce kendi saf vicdanıyla kararını kilitler (Commit)**.
3. **Perspektif ve Köprüleri Keşfetmek:** Kararını kilitledikten sonra (`Reveal`), kendisini toplumla kıyaslar. Ama asıl amaç "haklı çıkmak" değil; **"Benim gibi düşünmeyenlerin güçlü gerekçesi ne?"** ve **"Bizi buluşturan ortak zemin (Bridge) neresi?"** sorularını keşfetmektir.
4. **Bilişsel Yük Bütçesi (Cognitive Budget):**
   - **5 Saniye:** Kullanıcı vakanın ne olduğunu ve temel soruyu anlar.
   - **30 Saniye:** Yazı yazmadan, hızlıca tartıp (`Weigh`) kilitleyerek (`Commit`) ilk sonuca ulaşır.
   - **5 Dakika:** İsteyen kullanıcı kaynaklara, delillere, karşıt argümanlara ve derin metodolojiye dalar.

---

## 2. Kullanıcının Haklı Tespiti: "Bunların hepsi ekran mı, yoksa arka plan motoru mu?"

Önceki yapay zeka oturumlarının yaptığı en büyük mimari hata tam olarak buydu: **Dokümantasyonda geçen backend algoritmalarını, analitik formüllerini, web yönetim panellerini ve yapay zeka boru hatlarını körü körüne birer Flutter mobil kartına dönüştürüp mobil uygulamanın içine yığdılar!**

Sistemin gerçek mimarisinde **5 Kesin Katman** vardır ve bu katmanlar birbirine asla karıştırılamaz:

```mermaid
graph TD
    subgraph Katman 1: Mobil Tüketici Uygulaması (Flutter)
        UI1[Keşfet / Explore]
        UI2[Vaka Akışı & Tartım / Weigh]
        UI3[Sonuç & Çekirdek 4 Perspektif]
        UI4[Kefem / My KEFE & Aktivite]
    end

    subgraph Katman 2: Arka Plan Analitik & İstatistik Motorları (Python / BigQuery)
        ENG1[Depolarization Index Calculator]
        ENG2[Synthetic Astroturfing / Bot Shield]
        ENG3[Differential Privacy Budget]
        ENG4[Activation Funnel & Retention]
        ENG5[Merkle Audit Cryptographic Engine]
    end

    subgraph Katman 3: Yapay Zeka Kapısı (AI Orchestrator)
        AI1[Tarafsız Vaka Özeti Üretici]
        AI2[Haberlerden İddia / Claim Çıkarıcı]
        AI3[Soru Taslağı Önerici]
        AI4[Gerekçe Anlamsal Kümeleyici]
    end

    subgraph Katman 4: Admin Studio (Ayrı Web Paneli - Next.js)
        ADM1[Editoryal Vaka Stüdyosu]
        ADM2[İçerik Öneri / Aday İnceleme Kuyruğu]
        ADM3[Dört Göz / Maker-Checker Onay Kapısı]
        ADM4[Gerekçe ve Rapor Moderasyonu]
    end

    subgraph Katman 5: B2B, Araştırma ve Kurumsal Sistemler
        B2B1[KEFE Research Akademik Portalı]
        B2B2[KEFE Insights B2B Agregasyon]
        B2B3[Toplulaştırılmış Karar API]
    end

    AI1 --> ADM2
    ADM1 -->|Onaylanan Vaka| UI1
    UI2 -->|Kullanıcı Kararı| ENG5
    ENG5 --> ENG1
    ENG1 -->|Hesaplanan Özet Metrik| UI3
```

---

## 3. Katmanların Detaylı İncelemesi

### KATMAN 1: Mobil Tüketici Uygulaması (Gerçek Telefon Ekranı)
* **Teknoloji:** Flutter (Android / iOS).
* **Ekran Sayısı:** Çok az ve son derece odaklıdır:
  1. **Keşfet (Explore):** Günün öne çıkan ikilemleri, kategoriler, arama çubuğu ve anayasal güvence vitrini.
  2. **Vaka Detay & Tartım (Weigh):** Nötr özet, kritik bağlam, 1 ana karar sorusu, uç seçenekler ve "Kararımı Ver" (Commit) butonu.
  3. **Açığa Çıkarma & Perspektif (Reveal & Perspective):** Kararın tekrarı, güvenilir örneklem topluluk dağılımı ve **yalnızca 4 odak gerekçe kartı** (Yakın, Karşıt, Köprü, Alternatif).
  4. **Aktivite:** Geçmiş kararlar, güncellenen olaylar ve "fikrin değişti mi?" davetleri.
  5. **Kefem (My KEFE):** Kullanıcının düşünce yolculuğu, zaman içindeki eğilimleri ve kriptografik karar makbuzları.
* **Kural:** Mobil uygulamada asla karmaşık tablolar, 50 tane alt alta yığılmış analitik kart veya yönetim kontrolleri yer almaz.

---

### KATMAN 2: Arka Plan Analitik Motorları (Kesinlikle Mobil Ekran Değildir!)
Bunlar sunucuda (Python FastAPI / PostgreSQL / BigQuery) çalışan matematiksel algoritmalardır:
* **Depolarization Index Engine (CAP-117):** İki kutup arasındaki ortak paydaları ve köprü argümanların etkisini ölçen matematiksel formüldür. Ekranda bir sayfa değil, sonuç ekranında gerekirse tek satırlık bir "Kutuplaşmayı Azaltma Gücü: %68" rozetidir.
* **Synthetic Astroturfing Shield (CAP-073):** Bot saldırılarını, koordineli trol kampanyalarını ve sahte hesapları yakalayan arka plan güvenlik algoritmasıdır. Telefonda bir ekran değil, backend güvenlik filtresidir!
* **Differential Privacy Budget Monitor (CAP-119):** Kullanıcıların kararlarını anonimleştirirken gürültü ekleyerek bireyin kimliğinin deşifre edilmesini engelleyen matematiksel kütüphanedir.
* **Merkle Audit Proof (CAP-120):** Kararların değiştirilmediğini kanıtlayan kriptografik SHA-256 hash ağacıdır.
* **Hata Analizi:** Önceki ajanlar bu motorları mobil ekranda kocaman birer `Card` bileşeni yaparak mobil UI'ı şişirmişlerdir. Bunlar backend servisleridir.

---

### KATMAN 3: Yapay Zeka Mimarisi (`KEFE_AI_Architecture`)
KEFE'de Yapay Zeka (AI) kullanımı çok sıkı kurallara ve anayasal sınırlara bağlanmıştır:

1. **AI Asla Doğrudan Karar Veremez veya Yayın Yapamaz:**
   - AI suçluluk/masumiyet hükmü veremez.
   - Bilimsel/hukuki gerçeği oyla belirleyemez.
   - Uzman görüşü uyduramaz.
   - **En kritik kural:** Yüksek riskli gerçek bir olayı AI tek başına sisteme yayımlayamaz! Mutlaka insan editör onayı (`Human Gate`) gerekir.
2. **AI Nerede ve Nasıl Kullanılır? (Arka Plan Asistanı):**
   - **Tarafsız Özetleme (Neutral Summary):** Haber kaynaklarını ve iddiaları tarayıp 40-80 kelimelik tarafsız bir ikilem metni taslağı hazırlar.
   - **İddia Sınıflandırma (Claim Classification):** Olaydaki somut iddiaları ve delil durumunu etiketler.
   - **Soru Önerisi (Question Proposal):** Olayın kalbindeki asıl etik/kamusal soruyu editöre önerir.
   - **Gerekçe Kümeleme (Reason Clustering):** Kullanıcıların yazdığı binlerce serbest metin gerekçeyi anlamsal olarak 4 ana kümeye (Bilişsel, Etik, Hukuki, Toplumsal) ayırır.
3. **Gelecek AI Deneyimleri (Yol Haritası):**
   - `Perspective Coach`: Kullanıcının kendi düşünce kalıplarını sorgulamasına yardım eden yapay zeka rehberi.
   - `AI Devil's Advocate`: Kullanıcının savunduğu görüşün tam tersindeki en akıllı argümanı sunan şeytanın avukatı (yalnızca LAB/Eğitim modunda, açıkça AI olduğu belirtilerek).

---

### KATMAN 4: Admin Studio (`KEFE_Admin_Studio_Specification`)
Admin Studio, mobil uygulamanın bir parçası **değildir**. Ayrı bir Web uygulamasıdır (Next.js):
* **Amacı:** İçerik editörlerinin, moderatörlerin ve yöneticilerin sistemi yönettiği operasyon merkezidir.
* **Temel Modüller:**
  1. **Editoryal Vaka Stüdyosu (Case Studio):**
     - Olay/senaryo girilir, vaka formatı seçilir (DILEMMA, TODAY, CALL, RETRO, DECIDE).
     - Sorular, 1. ve 2. boyutlar, ölçekler tasarlanır.
     - Risk seviyesi (L0: Düşük, L1: Orta, L2/L3: Yüksek/Hassas) belirlenir.
  2. **Dört Göz İlkesi (Four-Eyes / Maker-Checker):**
     - Bir editörün hazırladığı yüksek riskli bir vaka, ikinci bir kıdemli editör veya hukukçu onaylamadan asla yayımlanamaz (`DRAFT → IN_REVIEW → APPROVED → PUBLISHED`).
  3. **Haber & Kaynak Havuzu (Source Ingestion Queue):**
     - RSS, haber ajansları ve resmi kurumlardan gelen ham haberler burada toplanır; editörler bunları vaka haline dönüştürür.
  4. **Moderasyon Masası:**
     - Kullanıcıların yazdığı gerekçelerdeki nefret söylemi, kişisel veri (PII) veya hakaretler burada denetlenir.

---

### KATMAN 5: B2B ve Araştırma Sistemleri
* **KEFE Research / Insights:** Üniversiteler, sivil toplum kuruluşları ve kamu kurumları için toplulaştırılmış, tamamen anonimleştirilmiş etik eğilim raporları sunan web portalları ve API'lerdir.

---

## 4. 128 Yeteneğin Tam Yol Haritası (Madde Madde)

KEFE ekosisteminde resmi olarak tanımlı 128 yetenek (`CAP-001` – `CAP-128`) şu 12 ana kulvara ayrılmıştır:

### 1. Bireysel Deneyim (ME - 14 Yetenek)
- `CAP-001`: Commit First / Önceden Sonuç Görmeme İzolasyonu (Faz 1)
- `CAP-002`: Tiplendirilmiş Soru Primitifleri (Ölçek, Tekli Seçim, Tahsis) (Faz 1)
- `CAP-003`: Özel / Gizli Gerekçe Kaydı (Faz 1)
- `CAP-004`: Karar Güven Seviyesi (Confidence Capture) (Faz 1)
- `CAP-005`: Kör Varyantlar (Aktörsüz / Kaynaksız Ön-Tartım) (Faz 2)
- `CAP-006`: İlke-Öncelikli Karar Akışı (Faz 2)
- `CAP-007`: Rol Değişimi (Role Flip / Karşı Tarafın Açısından Tartma) (Faz 4)
- `CAP-008`: Karar Revizyonu ve Karar Farkı (Decision Delta) (Faz 2)
- `CAP-009`: Nedensel Olmayan Karar Sonrası Yansıtma (Reflection) (Faz 2)
- `CAP-010`: "Ne Fikrimi Değiştirirdi?" Sorgulaması (Faz 4)
- `CAP-011`: "Yeterli Bilgim Yok / Seçenekler Eksik" Seçeneği (Faz 2)
- `CAP-012`: Kriptografik Sürümlü Karar Makbuzu (Faz 3)
- `CAP-013`: Kör Zamansal Yeniden Test / Zaman İçinde Fikir Kayması (Faz 4)
- `CAP-014`: Zihinsel Yorgunluk Kalkanı / Sağlıklı Tempo Koruyucu (Faz 5)

### 2. Kolektif Müzakere (WE - 11 Yetenek)
- `CAP-031`: Karar Sonrası Kolektif Sonuç Dağılımı (Faz 1)
- `CAP-032`: Gerekçe Dağılımı (Faz 2)
- `CAP-033`: Argüman Örüntü Kümelemesi (Faz 4)
- `CAP-034`: Köprü Argümanlar ve Ortak Zemin (Bridge Arguments) (Faz 4)
- `CAP-035`: 4 Odak Perspektif (Yakın, Karşıt, Köprü, Alternatif) (Faz 2)
- `CAP-036`: Mahremiyet Güvenli Segment Dağılımı (Faz 3)
- `CAP-037`: Paydaş Dağılımı (Faz 4)
- `CAP-038`: Paydaş Açığı Bildirimi (Faz 4)
- `CAP-039`: Konsensüs ve Ayrışma Sınıflandırması (Faz 4)
- `CAP-040`: Ayrışma Anatomisi (Divergence Anatomy) (Faz 4)
- `CAP-041`: Uzman - Kamuoyu Farkı Analizi (Faz 8)

### 3. Vaka Mimarisi ve Formatlar (CASE_COMPOSITION - 16 Yetenek)
- `CAP-015`: Jenerik Vaka Kompozisyonu (Faz 1)
- `CAP-016`: Toplumsal Sinyal ve Konsensüs Kartı (Faz 2)
- `CAP-017`: Politika Simülatörü ve Parametre Ayarlama (Faz 6)
- `CAP-018`: Eşik Duyarlılık Analizi (Faz 4)
- `CAP-019`: Adalet ve Normatif Modeller Karşılaştırması (Faz 4)
- `CAP-020`: Sorumluluk ve Hesap Verebilirlik Matrisi (Faz 4)
- `CAP-021`: Süreç Analizi Motoru (Faz 4)
- `CAP-022`: Teşvik Haritası (Incentive Map) (Faz 4)
- `CAP-023`: Paydaş Etki Matrisi (Faz 4)
- `CAP-024`: Sports CALL (Spor Tartımları ve Hakem Kararları) (Faz 3)
- `CAP-025`: KEFE Atlas (Coğrafi ve Kültürel Karar Haritası) (Faz 3)
- `CAP-026`: KEFE Today (Güncel Sıcak Olaylardan Vaka Üretimi) (Faz 2)
- `CAP-027`: KEFE Decide (Kaynak Tahsisi ve Bütçe Simülasyonu) (Faz 6)
- `CAP-028`: KEFE Retro (Tarihsel Olayları Dönemin Bilgisiyle Tartma) (Faz 6)
- `CAP-029`: Sadece Oku / Gözlem Modu (Observe Mode) (Post-MVP)
- `CAP-030`: UGC Topluluk İkilem Önerileri ve Eş-Kürasyon (Faz 5)

### 4. Toplumsal Sinyal (SIGNAL - 6 Yetenek)
- `CAP-042`: Metodolojik Nitelikli Sinyal Motoru (Faz 4)
- `CAP-043`: Ön-Karar / Maruziyet / Aktivizm Katkı Ayrımı (Faz 4)
- `CAP-044`: Sinyal Sağlık Kartı (Faz 4)
- `CAP-045`: Sinyal Yarılanma Ömrü ve Tazelik Döngüsü (Faz 4)
- `CAP-046`: Sinyal Kapsam Hizalaması (Faz 4)
- `CAP-047`: Metodoloji Sürümüne Kilitli Sinyal Tarihçesi (Faz 4)

### 5. Kurumsal Etki ve Eylem (IMPACT - 7 Yetenek)
- `CAP-048`: Sinyal Hedef Kayıt Defteri (Bakanlık, Belediye, Kurum) (Faz 5)
- `CAP-049`: Doğrulanmış Kurumsal Yanıt (Faz 5)
- `CAP-050`: Kurum Cevap Odası (Impact Room) (Faz 5)
- `CAP-051`: Kurumsal Yanıt Sonrası Yeniden Tartım (Faz 5)
- `CAP-052`: Kurum Eylem ve Vaat Takip Matrisi (Faz 5)
- `CAP-053`: Etki Kanıtı Toplama (Faz 5)
- `CAP-054`: Etki Doğrulama ve Raporlama (Faz 5)

### 6. Editoryal ve Admin Operasyonları (CONTENT_ADMIN - 14 Yetenek)
- `CAP-055`: Sağlayıcı Bağımsız İçerik Toplama (Ingestion) (Faz 2)
- `CAP-056`: Orijinal Kaynak ve Doğruluk Çözümleme (Faz 2)
- `CAP-057`: Birinci Sınıf İddia (Claim) Çıkarımı (Faz 2)
- `CAP-058`: İddia Değerlendirme ve Yaşam Döngüsü (Faz 2)
- `CAP-059`: İddia ve Argüman Çizgesi (Graph) (Faz 4)
- `CAP-060`: AI Destekli Ayıklama, Sınıflandırma ve Soru Önerisi (Faz 2)
- `CAP-061`: Dayanıklı İnsan İnceleme Kuyruğu (Proposal Queue) (Faz 2)
- `CAP-062`: Aday Vakadan Editoryal Taslağa Otomatik Yansıtma (Faz 2)
- `CAP-063`: Admin Vaka Stüdyosu (Case Builder Web) (Faz 2)
- `CAP-064`: Sürümlü Akış Bestecisi (Flow Composer) (Faz 3)
- `CAP-065`: Editoryal Kalite ve Risk Değerlendirmesi (Faz 2)
- `CAP-066`: Gerekçe ve İçerik Moderasyonu Masası (Faz 2)
- `CAP-067`: Doğrulanmış Uzman Katkısı (Faz 3)
- `CAP-068`: Vaka İtiraz ve Kamusal Meydan Okuma Mekanizması (Faz 3)

### 7. Güven ve Bütünlük (TRUST - 7 Yetenek)
- `CAP-069`: Kaynak Mikro-Önizlemesi (Faz 2)
- `CAP-070`: Tüketici Bilgi Durumu Rozetleri (Faz 2)
- `CAP-071`: Kaynak Çeşitliliği Göstergesi (Faz 3)
- `CAP-072`: Vaka Düzeltme ve Sürüm Tarihçesi Denetim Kütüğü (Faz 2)
- `CAP-073`: Bot Kalkanı ve Koordineli Manipülasyon Filtresi (Faz 2)
- `CAP-074`: Sonuç Başına Açık Metodoloji Sayfası (Faz 3)
- `CAP-075`: Vaka Kalite Kontrol Listesi (Büyülü Skor Yerine) (Faz 2)

### 8. Tüketici Büyümesi ve Mobil Deneyim (CONSUMER_GROWTH - 21 Yetenek)
- `CAP-076`: Canlı Karar Radarı (Faz 3)
- `CAP-077`: Kullanıcı Kontrollü Keşif Profili (Faz 3)
- `CAP-078`: Arama ve Hoşgörülü Filtreleme (Faz 2)
- `CAP-079`: Kaydetme, Takip ve Yaşam Döngüsü Bildirimleri (Faz 2)
- `CAP-080`: Kefem Betimsel İlerleme Tarihçesi (Faz 1)
- `CAP-081`: KEFE Chronicle (Karar Günlüğü) (Faz 4)
- `CAP-082`: KEFE Wrapped (Dönemsel Özetler) (Faz 5)
- `CAP-083`: KEFE Değerler Opt-in Kişisel Profili (Faz 9)
- `CAP-084`: Misafir (Guest) Kullanıcıdan Hesaba Geçiş ve Karar Birleştirme (Faz 1)
- `CAP-085`: Kullanıcı Verisi İndirme ve Hesabı Tamamen Silme (Faz 2)
- `CAP-086`: KEFE Circle / Birlikte Tart (Faz 5)
- `CAP-087`: KEFE Odaları (Rooms) (Faz 5+)
- `CAP-088`: KEFE Eğitim ve Sınıf Modülü (Faz 7)
- `CAP-089`: KEFE Canlı Etkinlik Mikro-Vakaları (Faz 6)
- `CAP-090`: Yerel KEFE (İl / İlçe Düzeyinde Tartımlar) (Faz 6)
- `CAP-091`: Gömülü (Embeddable) KEFE Karar Kartları (Faz 8)
- `CAP-092`: Kamusal Web Açılış Sayfaları ve Derin Linkler (Post-MVP)
- `CAP-093`: Ek Diller ve Ülkeler (Faz 3+)
- `CAP-094`: Üretim CDN ve Medya Saklama Hattı (Faz 3)
- `CAP-095`: Erişilebilirlik, Reduce Motion ve Düşük Donanımlı Android Desteği (Zorunlu)
- `CAP-096`: Etik ve Tarafsız Katılım Dinamikleri (Faz 5)

### 9. Ticari & Kurumsal (COMMERCIAL - 11 Yetenek)
- `CAP-103`: KEFE+ Premium Abonelik (Post-PMF)
- `CAP-104`: Sağlayıcı Bağımsız Yetki Servisi (Entitlement Service) (Post-PMF)
- `CAP-105`: Apple / Google Uygulama İçi Satın Alma & Doğrulama (Post-PMF)
- `CAP-106`: Web Ödeme ve Hesap Eşleştirme (Post-PMF)
- `CAP-107`: Bölgesel Ürün ve Fiyatlandırma Kataloğu (Post-PMF)
- `CAP-108`: KEFE Insights B2B Agregasyon (Faz 8)
- `CAP-109`: KEFE Research Akademik Araştırma Modülü (Faz 7)
- `CAP-110`: Özel Kurumsal Araştırmalar (Custom Studies) (Faz 7/8)
- `CAP-111`: KEFE Pulse Medya Dağıtım Widget'ları (Faz 8)
- `CAP-112`: Toplulaştırılmış Karar Veri API'si (Faz 8)
- `CAP-113`: Şeffaf Sponsorluk ve Ortaklık Modeli (Faz 8)

### 10. Analitik ve Matematiksel Motorlar (ANALYTICS_REPORTING - 12 Yetenek)
- `CAP-114`: Anlamlı Tartımlar Toplayıcısı (Meaningful Weighs Aggregator) (Faz 1)
- `CAP-115`: Aktivasyon Hunisi Hesaplayıcısı (Activation Funnel) (Faz 1)
- `CAP-116`: Perspektif Direnci ve Tutum Değişimi Hesaplayıcısı (Faz 2)
- `CAP-117`: Kutuplaşma Azaltma ve Köprü Etkinliği Endeksi (Faz 4)
- `CAP-118`: Müzakere Derinliği ve Yansıtma Puanı (Faz 4)
- `CAP-119`: Diferansiyel Gizlilik Bütçe Monitörü (Faz 3)
- `CAP-120`: Kriptografik Merkle Denetim İzi (Faz 2)
- `CAP-121`: Zaman İçinde Fikir Kayması Analizi (Faz 4)
- `CAP-122`: Gerekçe Kalitesi ve Çeşitlilik Ölçer (Faz 2)
- `CAP-123`: Temsiliyet ve Demografik Dengeleyici (Faz 3)
- `CAP-124`: FinOps ve Maliyet / Gecikme İzleyici (Faz 1)
- `CAP-125`: Model Sürüklenmesi ve Güvenlik Değerlendirme Motoru (Faz 2)

### 11. Yönetişim ve Standartlar (GOVERNANCE - 3 Yetenek)
- `CAP-126`: Yetenek Portföy Sicili ve Unutulan Özellik Kapısı (Tüm Fazlar)
- `CAP-127`: Bağımsız Standartlar Konseyi (Faz 9+)
- `CAP-128`: Küresel Demokrasi ve Karar Endeksleri (Faz 9)

---

## 5. Doğru ve Sağlıklı Uygulama Stratejisi

Bu muazzam sistem analizi ışığında yapılması gerekenler:

1. **Mobil Uygulamanın Temiz Tutulması:**
   - Mobil uygulama asla bir "motor çöplüğü" olmamalıdır.
   - 117 tane yazılmış kartın çoğu aslında backend algoritmasıdır. Bunların yeri `services/api/` veya `core/analytics/` katmanıdır.
   - Mobil ekranda sadece kullanıcının görmesi gereken çekirdek bileşenler kalmalıdır:
     * Keşfet ekranında güven veren bir vitrin (`DeliberationCockpitShowcase`) ve vaka kartlarında güvence rozetleri.
     * Vaka detayında şeffaflık eylemleri (Kalite denetimi, sürüm geçmişi, itiraz).
     * Sonuç ekranında 4 çekirdek perspektif ve derinleşmek isteyenler için kategorize edilmiş analiz sekmesi.
     * Kefem ekranında kişisel makbuz ve güvence kasası.
2. **Yapay Zeka ve Admin Studio'nun Kendi Doğal Katmanlarında Konumlandırılması:**
   - Vaka oluşturma ve editoryal akışlar Admin Studio'ya aittir.
   - Yapay zeka orkestrasyonu backend'deki `AI Orchestrator` portlarına aittir.
