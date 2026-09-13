from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid5

CATALOG_NAMESPACE = UUID("5a2f93ad-2cc6-43e8-8b84-563b757a0b10")


@dataclass(frozen=True, slots=True)
class PerspectiveEntry:
    slot: str  # NEAR | OPPOSING | BRIDGE | ALTERNATIVE_CONTEXT
    body: str


@dataclass(frozen=True, slots=True)
class ContextBlock:
    block_type: str  # ESSENTIAL | DETAIL | DATA_POINT
    label: str
    body: str


@dataclass(frozen=True, slots=True)
class BetaCatalogCase:
    slug: str
    title: str
    summary: str
    prompt: str
    option_a: str
    option_b: str
    domain: str
    base_format: str
    perspectives: tuple[PerspectiveEntry, ...] = field(default_factory=tuple)
    context_blocks: tuple[ContextBlock, ...] = field(default_factory=tuple)

    @property
    def case_id(self) -> UUID:
        return uuid5(CATALOG_NAMESPACE, f"case:{self.slug}")

    @property
    def version_id(self) -> UUID:
        return uuid5(CATALOG_NAMESPACE, f"version:{self.slug}:1")

    @property
    def issue_id(self) -> UUID:
        return uuid5(CATALOG_NAMESPACE, f"issue:{self.slug}:1")

    @property
    def question_id(self) -> UUID:
        return uuid5(CATALOG_NAMESPACE, f"question:{self.slug}:primary")

    @property
    def confidence_id(self) -> UUID:
        return uuid5(CATALOG_NAMESPACE, f"question:{self.slug}:confidence")

    @property
    def result_id(self) -> UUID:
        return uuid5(CATALOG_NAMESPACE, f"result:{self.slug}:1")

    @property
    def perspective_id(self) -> UUID:
        return uuid5(CATALOG_NAMESPACE, f"perspective:{self.slug}:bridge")


# ---------------------------------------------------------------------------
# Engineering readiness catalog.
# Copy remains L0 and illustrative until human CQB approval.
# The existing "Son koltuk" demo is the 20th L0 DILEMMA.
# ---------------------------------------------------------------------------

DILEMMAS: tuple[BetaCatalogCase, ...] = (
    BetaCatalogCase(
        slug="sirada-acil-ihtiyac",
        title="Sırada acil ihtiyaç",
        summary="Sıra hakkı ile açık aciliyet çatıştığında önceliği tart.",
        prompt="Kime öncelik verilmeli?",
        option_a="Sıradaki kişiye",
        option_b="Acil ihtiyacı olana",
        domain="DAILY_LIFE",
        base_format="DILEMMA",
        perspectives=(
            PerspectiveEntry("NEAR", "Sırayı bekleyenler de zaman harcadı; istisna kuralı belirsizlik yaratır ve herkes acil olduğunu iddia edebilir."),
            PerspectiveEntry("OPPOSING", "Görünür aciliyeti görmezden gelmek kural uygulayıcısını vicdansız gösterir ve toplumsal dayanışmayı zayıflatır."),
            PerspectiveEntry("BRIDGE", "Açık ve öngörülemeyen aciliyetler için kısa bir 'öncelik penceresi' tanımlamak hem düzeni hem insanlığı korur."),
            PerspectiveEntry("ALTERNATIVE_CONTEXT", "Bazı ülkelerde sağlık hizmetlerinde 'triaj' modeli, aciliyeti nesnel ölçütlerle sıra hakkından ayırır."),
        ),
        context_blocks=(
            ContextBlock("ESSENTIAL", "Durum", "Kasiyer ya da görevli, hem sırasını bekleyen birini hem de belirgin şekilde acil ihtiyacı olan birini görüyor. Resmi bir istisna politikası yok."),
            ContextBlock("DETAIL", "Neden zor?", "Sıra, eşit muamele ve öngörülebilirlik sağlar. Ama katı kural uygulaması, herkesin görebildiği bir aciliyeti görmezden gelmek anlamına gelebilir."),
            ContextBlock("DATA_POINT", "Araştırma bulgusu", "Sosyal psikoloji araştırmaları, insanların çoğunluğunun tıbbi acil durumlarda sıra önceliğini devretmeye razı olduğunu gösteriyor — ama bu oran 'acil' tanımı belirsizleşince düşüyor."),
        ),
    ),
    BetaCatalogCase(
        slug="sessiz-vagon-cocuk",
        title="Sessiz vagonda çocuk",
        summary="Sessizlik beklentisi ile ailelerin kamusal alan kullanımı arasındaki dengeyi tart.",
        prompt="Öncelik hangisinde olmalı?",
        option_a="Sessiz vagon kuralında",
        option_b="Ailenin birlikte yolculuğunda",
        domain="FAMILY_PARENTING",
        base_format="DILEMMA",
        perspectives=(
            PerspectiveEntry("NEAR", "Sessiz vagon, o ortamı bilinçli seçen yolcular için bir taahhüttür; kural ihlali tüm yolculuğu etkiler."),
            PerspectiveEntry("OPPOSING", "Küçük çocukların sessiz vagonda bekleneni yerine getirmeleri gerçekçi değildir; aileler sosyal dışlanmayla karşılaşabilir."),
            PerspectiveEntry("BRIDGE", "Aile compartımanları veya esnek saatler, hem sessizlik hakkını hem aile katılımını koruyabilir."),
            PerspectiveEntry("ALTERNATIVE_CONTEXT", "Japonya'daki Shinkansen'de çocuk dostu ve sessiz vagonlar ayrı işletilmekte; bu uygulama çatışmayı önemli ölçüde azaltmaktadır."),
        ),
        context_blocks=(
            ContextBlock("ESSENTIAL", "Durum", "Bir ebeveyn, küçük çocuğuyla 'sessiz vagon' olarak işaretlenmiş vagonda yolculuk ediyor. Çocuk zaman zaman ses çıkarıyor."),
            ContextBlock("DETAIL", "Kural ne diyor?", "Sessiz vagon kuralı, çoğu demiryolu işletmesinde telefon konuşmalarını ve yüksek sesi yasaklar; ama çocuklar için açık bir istisna genellikle tanımlanmamıştır."),
        ),
    ),
    BetaCatalogCase(
        slug="ortak-mutfak-son-porsiyon",
        title="Ortak mutfakta son porsiyon",
        summary="Eşit paylaşım ile o anda daha fazla ihtiyacı olan kişiyi tart.",
        prompt="Son porsiyon nasıl ayrılmalı?",
        option_a="Eşit sıraya göre",
        option_b="İhtiyaca göre",
        domain="DAILY_LIFE",
        base_format="DILEMMA",
        perspectives=(
            PerspectiveEntry("NEAR", "Sıraya göre paylaşım, kişisel değerlendirmeden bağımsız öngörülebilir bir sistem kurar ve tartışmayı önler."),
            PerspectiveEntry("OPPOSING", "İhtiyaç temelli paylaşım, topluluğun birlikte yaşama kapasitesini ve empatiyi güçlendirir."),
            PerspectiveEntry("BRIDGE", "Küçük ortak stoklarda 'kim son aldı' kaydı tutmak, hem sıra hem ihtiyaç dengesini şeffaf biçimde kurar."),
        ),
        context_blocks=(
            ContextBlock("ESSENTIAL", "Durum", "Ortak mutfakta son ekmek veya yemek porsiyonu kaldı. Birden fazla kişi aynı anda mutfakta."),
            ContextBlock("DETAIL", "Neden önemli?", "Paylaşılan kaynakların dağılımı küçük ölçekli de olsa adalet algısını ve grup uyumunu doğrudan etkiler."),
        ),
    ),
    BetaCatalogCase(
        slug="sinif-proje-gorev",
        title="Grup projesinde görev",
        summary="Herkese eşit görev vermek ile güçlü yönlere göre iş bölümü yapmayı tart.",
        prompt="Görevler nasıl bölüşülmeli?",
        option_a="Eşit miktarda",
        option_b="Yetkinliğe göre",
        domain="EDUCATION",
        base_format="DILEMMA",
        perspectives=(
            PerspectiveEntry("NEAR", "Eşit görev dağılımı, herkesin projeye aktif katıldığını garanti eder ve güçlü üyelerin tüm yükü taşımasını önler."),
            PerspectiveEntry("OPPOSING", "Yetkinliğe göre görev, projenin kalitesini artırır ve her üyenin gerçek anlamda katkı sağlamasını kolaylaştırır."),
            PerspectiveEntry("BRIDGE", "Ana hedefleri yetkinliğe göre dağıtıp herkesin en az bir temel görevi üstlenmesini sağlamak her iki değeri de korur."),
            PerspectiveEntry("ALTERNATIVE_CONTEXT", "Eğitimde 'yaparak öğrenme' araştırmaları, zayıf alanlarda görev almanın uzun vadede yetkinlik gelişimini hızlandırdığını gösteriyor."),
        ),
        context_blocks=(
            ContextBlock("ESSENTIAL", "Durum", "Bir öğrenci grubu proje görevlerini paylaştırıyor. Grup üyelerinin bilgi ve deneyim seviyeleri farklı."),
            ContextBlock("DETAIL", "İki temel değer", "Adalet (herkes eşit yük taşısın) ile verimlilik (en iyi sonuç için en iyi kişi) arasında seçim yapılıyor."),
        ),
    ),
    BetaCatalogCase(
        slug="ofiste-hibrit-gun",
        title="Ofiste hibrit gün",
        summary="Ekip koordinasyonu ile bireysel esnekliği tart.",
        prompt="Ortak ofis günü nasıl belirlenmeli?",
        option_a="Tek ortak gün zorunlu",
        option_b="Ekipler kendisi seçsin",
        domain="WORK_BUSINESS",
        base_format="DILEMMA",
        perspectives=(
            PerspectiveEntry("NEAR", "Ortak zorunlu gün, ekip içi koordinasyonu ve spontane etkileşimi kolaylaştırır; planlama yükünü azaltır."),
            PerspectiveEntry("OPPOSING", "Ekiplerin kendi günlerini seçmesi, bireysel yaşam koşullarına ve iş akışlarına göre optimum esneklik sağlar."),
            PerspectiveEntry("BRIDGE", "Merkezi koordinasyon gerektiren toplantılar için çapraz-ekip günleri belirlenirken ekip içi günler serbest bırakılabilir."),
            PerspectiveEntry("ALTERNATIVE_CONTEXT", "Microsoft ve Spotify gibi şirketlerin hibrit politikaları, tam merkeziyetçilik ile tam esneklik arasındaki farklı dengeleri ve sonuçlarını karşılaştırmalı olarak ortaya koyuyor."),
        ),
        context_blocks=(
            ContextBlock("ESSENTIAL", "Durum", "Şirket, hibrit çalışmaya geçiyor ve hangi günlerin ofiste geçirileceğine karar verilmesi gerekiyor."),
            ContextBlock("DATA_POINT", "Araştırma verisi", "Stanford araştırmacıları, haftada 2-3 gün hibrit çalışmanın hem üretkenlik hem çalışan memnuniyeti açısından tam uzak ya da tam ofis modellerinden daha iyi sonuçlar verdiğini buldu."),
        ),
    ),
    BetaCatalogCase(
        slug="parkta-sessiz-etkinlik",
        title="Parkta etkinlik",
        summary="Mahalle huzuru ile kamusal alanın canlı kullanımını tart.",
        prompt="Akşam etkinliği için ne yapılmalı?",
        option_a="Erken bitirilmeli",
        option_b="Belirli saate kadar sürmeli",
        domain="CITY_PUBLIC_LIFE",
        base_format="DILEMMA",
        perspectives=(
            PerspectiveEntry("NEAR", "Erken bitiş, çocuklu aileler ve erken kalkanlar dahil geniş bir kesimin uyku düzenini korur."),
            PerspectiveEntry("OPPOSING", "Mahalle parkları kamusal alandır; canlı kullanım, sosyal bağı ve topluluğun kendini ifade etmesini güçlendirir."),
            PerspectiveEntry("BRIDGE", "Şehirlerin çoğunda belirlenen gürültü saatleri, etkinliklerin topluluk müdahalesi olmadan planlı biçimde bitmesini sağlar."),
        ),
        context_blocks=(
            ContextBlock("ESSENTIAL", "Durum", "Mahalle parkında düzenlenen bir etkinlik akşam geç saatlere kadar devam ediyor. Yakın çevredeki sakinler rahatsız."),
            ContextBlock("DETAIL", "Kamusal alan ikilemi", "Parklar hem topluluk etkinliği hem de huzur hakkı için ortak alan; bu iki kullanım çatışabiliyor."),
        ),
    ),
    BetaCatalogCase(
        slug="kutuphane-grup-calisma",
        title="Kütüphanede grup çalışması",
        summary="Sessiz çalışma hakkı ile ortak öğrenme alanı ihtiyacını tart.",
        prompt="Alan kullanımı nasıl düzenlenmeli?",
        option_a="Tam sessizlik",
        option_b="Ayrılmış grup bölümü",
        domain="EDUCATION",
        base_format="DILEMMA",
        perspectives=(
            PerspectiveEntry("NEAR", "Kütüphanenin geleneksel işlevi bireysel odaklanma gerektiren çalışma ortamı sunmaktır; sessizlik bu işlevin temelidir."),
            PerspectiveEntry("OPPOSING", "İşbirlikçi öğrenme, bilişsel gelişimde kritik bir rol oynar; kütüphaneler bu ihtiyacı da karşılayacak biçimde evrilmelidir."),
            PerspectiveEntry("BRIDGE", "Pek çok modern kütüphane, sessiz bölümler ile grup çalışma odalarını bir arada sunarak her iki ihtiyacı da karşılıyor."),
        ),
        context_blocks=(
            ContextBlock("ESSENTIAL", "Durum", "Kütüphane, hem bireysel çalışmak isteyenleri hem de grup çalışması yapan öğrencileri aynı anda ağırlıyor."),
        ),
    ),
    BetaCatalogCase(
        slug="yapay-zeka-odev",
        title="Ödevde yapay zekâ",
        summary="Öğrenme emeği ile yeni araçlardan yararlanmayı tart.",
        prompt="YZ kullanımı nasıl ele alınmalı?",
        option_a="Kullanılmamalı",
        option_b="Kaynak göstererek kullanılmalı",
        domain="TECHNOLOGY_AI",
        base_format="DILEMMA",
        perspectives=(
            PerspectiveEntry("NEAR", "YZ kullanımını yasaklamak, öğrencinin konuyu bizzat düşünmesini ve özgün beceriler geliştirmesini güvence altına alır."),
            PerspectiveEntry("OPPOSING", "YZ, işyerinde standart bir araç hâline geliyor; öğrencilere bu araçları sorumlu biçimde kullanmayı öğretmek onları geleceğe hazırlar."),
            PerspectiveEntry("BRIDGE", "YZ'yi bir süreç aracı olarak şeffaf biçimde kullanmak (kaynak göstermek, eleştirel değerlendirme eklemek) hem öğrenmeyi hem akademik dürüstlüğü koruyabilir."),
            PerspectiveEntry("ALTERNATIVE_CONTEXT", "2023'ten itibaren pek çok üniversite, YZ için 'alıntı politikası' modeli benimsedi; bu modelde YZ'nin nasıl kullanıldığının açıklanması esastır."),
        ),
        context_blocks=(
            ContextBlock("ESSENTIAL", "Durum", "Bir öğrenci, ödev hazırlığında YZ kullanıp kullanamayacağını sorguluyor. Okulun net bir politikası henüz yok."),
            ContextBlock("DATA_POINT", "Bağlam", "Turnitin'in 2023 raporuna göre, dünya genelinde akademik çevrelerin %85'i YZ kullanımına ilişkin net politika eksikliğinden yakınıyor."),
        ),
    ),
    BetaCatalogCase(
        slug="toplanti-kamera",
        title="Çevrim içi toplantıda kamera",
        summary="Ekip iletişimi ile mahremiyet/esnekliği tart.",
        prompt="Kamera politikası ne olmalı?",
        option_a="Genelde açık",
        option_b="Kişinin tercihine bırakılmalı",
        domain="WORK_BUSINESS",
        base_format="DILEMMA",
        perspectives=(
            PerspectiveEntry("NEAR", "Kameranın açık olması, yüz ifadesini ve beden dilini görünür kılar; bu da iletişim kalitesini artırır ve toplantı bağlılığını güçlendirir."),
            PerspectiveEntry("OPPOSING", "Ev ortamını paylaşmak veya kameraya hazırlanmak, herkes için eşit ölçüde kolay değildir; zorunluluk kaygıyı artırabilir."),
            PerspectiveEntry("BRIDGE", "Kameranın varsayılan olarak açık olduğu, ancak kişisel gerekçelerle kapatılabildiği esnek bir politika her iki değeri de korur."),
        ),
        context_blocks=(
            ContextBlock("ESSENTIAL", "Durum", "Uzaktan çalışan bir ekip, çevrim içi toplantılarda kamera politikasını tartışıyor. Bazı üyeler kameranın açık olmasını tercih ederken diğerleri tercih etmiyor."),
            ContextBlock("DATA_POINT", "Araştırma", "Microsoft'un 2022 Work Trend raporunda, katılımcıların %43'ü video yorgunluğunun üretkenliğini olumsuz etkilediğini belirtti."),
        ),
    ),
    BetaCatalogCase(
        slug="mahalle-otopark",
        title="Mahallede sınırlı otopark",
        summary="İlk gelen hakkı ile özel ihtiyacı olanlara ayrılan alanı tart.",
        prompt="Boş alan önceliği nasıl olmalı?",
        option_a="İlk gelene",
        option_b="Belirlenmiş ihtiyaca",
        domain="CITY_PUBLIC_LIFE",
        base_format="DILEMMA",
        perspectives=(
            PerspectiveEntry("NEAR", "İlk gelen alır ilkesi, müdahale gerektirmeyen, öngörülebilir ve nesnel bir sistem sunar."),
            PerspectiveEntry("OPPOSING", "Engeli olan veya küçük çocuklu bireyler gibi gerçek ihtiyaç sahiplerinin ayrılmış alanlara erişimi, eşitlik ve erişilebilirlik açısından gereklidir."),
            PerspectiveEntry("BRIDGE", "Bazı alanları belgelenmiş ihtiyaca göre ayırmak, geri kalanı serbest bırakmak her iki ilkeyi uzlaştırır."),
        ),
        context_blocks=(
            ContextBlock("ESSENTIAL", "Durum", "Yoğun bir mahallede otopark alanları yetersiz. Bazı sakinler özel ihtiyaçları olduğunu öne sürerek belirli alanların kendileri için ayrılmasını istiyor."),
        ),
    ),
    BetaCatalogCase(
        slug="aile-tatil-butcesi",
        title="Aile tatil bütçesi",
        summary="Herkesin eşit söz hakkı ile bütçeyi sağlayanın tercih ağırlığını tart.",
        prompt="Karar nasıl alınmalı?",
        option_a="Herkes eşit oy",
        option_b="Katkı oranı da dikkate alınsın",
        domain="FAMILY_PARENTING",
        base_format="DILEMMA",
        perspectives=(
            PerspectiveEntry("NEAR", "Eşit oy, aile içinde her bireyin değerini ve katkısını (çocukların varlığı, ev işleri vb.) sayısallaştırılmayan biçimde tanır."),
            PerspectiveEntry("OPPOSING", "Maddi katkı sağlayanların karar sürecinde daha fazla ağırlık taşıması, sorumluluk ve hak arasındaki dengeyi yansıtır."),
            PerspectiveEntry("BRIDGE", "Herkesin öneri sunduğu, ardından katkı ve ihtiyaç birlikte değerlendirilerek ortak kararın alındığı bir süreç her iki yaklaşımın güçlü yönlerini birleştirir."),
        ),
        context_blocks=(
            ContextBlock("ESSENTIAL", "Durum", "Aile, yıllık tatil planını yaparken kimin ne istediği ve bütçenin nasıl kullanılacağı konusunda anlaşmazlık yaşıyor."),
        ),
    ),
    BetaCatalogCase(
        slug="takim-son-penalti",
        title="Takımın son penaltısı",
        summary="En formda oyuncu ile takım liderinin sorumluluğunu tart.",
        prompt="Son penaltıyı kim kullanmalı?",
        option_a="En formda oyuncu",
        option_b="Belirlenmiş kaptan/lider",
        domain="SPORTS",
        base_format="DILEMMA",
        perspectives=(
            PerspectiveEntry("NEAR", "En formda oyuncuyu seçmek, gol atma ihtimalini matematiksel olarak artırır; sonuç odaklı bir yaklaşımdır."),
            PerspectiveEntry("OPPOSING", "Kaptan/lider seçimi takım hiyerarşisini ve baskı altında sorumluluk üstlenme kültürünü pekiştirir."),
            PerspectiveEntry("BRIDGE", "Büyük turnuvalarda pek çok takım, teknik analiz ve liderlik değerini harmanlamak için önceden belirlenmiş bir vuruş sırası kullanıyor."),
            PerspectiveEntry("ALTERNATIVE_CONTEXT", "2021 Avrupa Şampiyonası'nda İtalya'nın penaltı galibiyeti, titiz hazırlık ve net bir vuruş sırası planlamasının farkını ortaya koydu."),
        ),
        context_blocks=(
            ContextBlock("ESSENTIAL", "Durum", "Penaltı atışına gidilen kritik bir maçta antrenör son vuruşu kime vereceğine karar veriyor."),
            ContextBlock("DETAIL", "İki yaklaşım", "Veri odaklı karar (son dönem istatistikleri, baskı altında performans) ile liderlik değeri (moral, sorumluluk, tecrübe) arasında seçim yapılıyor."),
        ),
    ),
    BetaCatalogCase(
        slug="muzede-fotograf",
        title="Müzede fotoğraf",
        summary="Ziyaretçi deneyimi ile eser/alan düzenini tart.",
        prompt="Fotoğraf politikası nasıl olmalı?",
        option_a="Serbest olmalı",
        option_b="Belirli bölümlerde sınırlı olmalı",
        domain="CULTURE_MEDIA",
        base_format="DILEMMA",
        perspectives=(
            PerspectiveEntry("NEAR", "Serbest fotoğraf, müze deneyimini kişiselleştirir, sosyal paylaşımı mümkün kılar ve kurumun organik tanıtımına katkı sağlar."),
            PerspectiveEntry("OPPOSING", "Flaş ışığı ve kalabalık grupların çekimleri eserlere zarar verebilir, diğer ziyaretçilerin deneyimini bozabilir."),
            PerspectiveEntry("BRIDGE", "Flaşsız fotoğraf ve belirlenmiş çekim alanları, hem erişimi hem eserlerin korunmasını sağlayan yaygın bir dengedir."),
        ),
        context_blocks=(
            ContextBlock("ESSENTIAL", "Durum", "Müze yönetimi, ziyaretçilerin eserlerin yanında fotoğraf çekip çekemeyeceğine dair politikasını gözden geçiriyor."),
            ContextBlock("DATA_POINT", "Kültürel bağlam", "Louvre ve MoMA gibi pek çok büyük müze, kişisel kullanım için fotoğrafa izin verirken ticari çekimler için ayrı koşullar uyguluyor."),
        ),
    ),
    BetaCatalogCase(
        slug="restoranda-rezervasyon",
        title="Geciken rezervasyon",
        summary="Rezervasyon hakkı ile bekleyen müşterilerin hakkını tart.",
        prompt="Masa kime verilmeli?",
        option_a="Rezervasyon sahibine biraz daha beklenmeli",
        option_b="Bekleyen müşteriye verilmeli",
        domain="DAILY_LIFE",
        base_format="DILEMMA",
        perspectives=(
            PerspectiveEntry("NEAR", "Rezervasyona güven, planlamanın temelini oluşturur; belirli bir bekleme payı bu taahhüdün parçasıdır."),
            PerspectiveEntry("OPPOSING", "Uzun gecikme hem bekleyen müşterilere hem restorana haksızlık yapar; belirli bir süre sonra masa serbest bırakılmalıdır."),
            PerspectiveEntry("BRIDGE", "Net bir bekleme süresi politikası (örneğin 15 dakika) ve müşteriye önceden bildirim, her iki tarafın beklentisini yönetir."),
        ),
        context_blocks=(
            ContextBlock("ESSENTIAL", "Durum", "Rezervasyon sahibi belirtilen saatten 20 dakika geçmesine rağmen gelmiş değil. Restoranda bekleyen müşteriler var."),
        ),
    ),
    BetaCatalogCase(
        slug="okul-kulubu-kontenjan",
        title="Okul kulübünde kontenjan",
        summary="İlk başvuru ile fırsat eşitliğini tart.",
        prompt="Kontenjan nasıl dağıtılmalı?",
        option_a="İlk başvurana",
        option_b="Kura ile",
        domain="EDUCATION",
        base_format="DILEMMA",
        perspectives=(
            PerspectiveEntry("NEAR", "İlk başvuru ilkesi, proaktif ve kararlı öğrencileri ödüllendirir; harekete geçme motivasyonunu artırır."),
            PerspectiveEntry("OPPOSING", "Kura, internet erişimi ya da bilgi ağı gibi avantajlara bağlı olmaksızın tüm öğrencilere eşit fırsat tanır."),
            PerspectiveEntry("BRIDGE", "Belirli gün ve saatte açılan başvuru, ardından kura ile seçim, hem hız hem eşitlik değerlerini bir arada sunar."),
        ),
        context_blocks=(
            ContextBlock("ESSENTIAL", "Durum", "Popüler okul kulübünün kontenjandan fazla başvurusu var. Kimin kabul edileceğine karar vermek gerekiyor."),
        ),
    ),
    BetaCatalogCase(
        slug="apartman-ortak-alan",
        title="Apartman ortak alanı",
        summary="Sessiz kullanım ile sosyal ortak alan ihtiyacını tart.",
        prompt="Akşam kullanımı nasıl olmalı?",
        option_a="Sessiz kullanım öncelikli",
        option_b="Belirli saate kadar sosyal kullanım",
        domain="CITY_PUBLIC_LIFE",
        base_format="DILEMMA",
        perspectives=(
            PerspectiveEntry("NEAR", "Ortak alanlar apartmandaki tüm sakinlere ait; sessizlik hakkı yalnızca bazı sakinlerin tercihine göre kısıtlanamaz."),
            PerspectiveEntry("OPPOSING", "Sosyal etkileşim, komşuluk ilişkisini güçlendirir; belirli saatlere kadar ortak alanda bir araya gelmek topluluk ruhunu besler."),
            PerspectiveEntry("BRIDGE", "Net saat sınırı ile sakin şikâyeti için açık bir kanal oluşturmak, her iki ihtiyacı da uzlaştırır."),
        ),
        context_blocks=(
            ContextBlock("ESSENTIAL", "Durum", "Apartman sakinleri, ortak alanın akşam geç saate kadar sosyal amaçlı kullanılıp kullanılmaması gerektiğini tartışıyor."),
        ),
    ),
    BetaCatalogCase(
        slug="etkinlik-bilet-iade",
        title="Etkinlik bileti iadesi",
        summary="Katı satış koşulu ile beklenmedik durumlarda esnekliği tart.",
        prompt="İade politikası nasıl olmalı?",
        option_a="Satış koşulu aynen uygulansın",
        option_b="Belirli şartlarda esneklik olsun",
        domain="CULTURE_MEDIA",
        base_format="DILEMMA",
        perspectives=(
            PerspectiveEntry("NEAR", "Katı iade politikası, organizatörlerin nakit akışını ve planlama güvenilirliğini korur; bu koşullar satın alım sırasında açıkça belirtilmektedir."),
            PerspectiveEntry("OPPOSING", "Hastalık gibi öngörülemeyen durumlar için esneklik, müşteri sadakatini artırır ve organizatörün itibarına da katkı sağlar."),
            PerspectiveEntry("BRIDGE", "Belgelenmiş olağanüstü durumlar için (tıbbi rapor vb.) kredi transferi veya ertelenmiş bilet seçeneği her iki tarafı dengeler."),
        ),
        context_blocks=(
            ContextBlock("ESSENTIAL", "Durum", "Bilet satın alan bir kişi, hastalık nedeniyle etkinliğe katılamıyor; organizatör iade politikasını uygulamak zorunda."),
        ),
    ),
    BetaCatalogCase(
        slug="ekip-basari-odulu",
        title="Ekip başarı ödülü",
        summary="Eşit ekip payı ile bireysel katkı farklarını tart.",
        prompt="Ödül nasıl dağıtılmalı?",
        option_a="Eşit paylaşılmalı",
        option_b="Katkıya göre farklılaşmalı",
        domain="WORK_BUSINESS",
        base_format="DILEMMA",
        perspectives=(
            PerspectiveEntry("NEAR", "Eşit dağılım ekip dayanışmasını güçlendirir; başarı kolektif bir emekle kazanılmıştır ve bu kolektif yapıyı ödüllendirmelidir."),
            PerspectiveEntry("OPPOSING", "Katkıya göre farklılaşma, yüksek performansı tanır; bu da uzun vadede üretkenlik motivasyonunu destekler."),
            PerspectiveEntry("BRIDGE", "Temel eşit pay artı katkıya dayalı ek prim, hem dayanışmayı hem bireysel motivasyonu korur."),
            PerspectiveEntry("ALTERNATIVE_CONTEXT", "Araştırmalar, tamamen bireysel teşviklerin zaman zaman ekip içi işbirliğini azalttığını, saf eşit paylaşımın ise düşük performansı tolere ettiğini gösteriyor."),
        ),
        context_blocks=(
            ContextBlock("ESSENTIAL", "Durum", "Bir ekip büyük bir projeyi başarıyla tamamladı. Yönetim, ödülün nasıl dağıtılacağına karar vermek zorunda."),
            ContextBlock("DATA_POINT", "Araştırma bulgusu", "Harvard Business Review, karma teşvik modellerinin (eşit taban + performans primi) hem bireysel üretkenliği hem ekip uyumunu en iyi düzeyde optimize ettiğini ortaya koyuyor."),
        ),
    ),
    BetaCatalogCase(
        slug="mahalle-spor-sahasi",
        title="Mahalle spor sahası",
        summary="Rezervasyon düzeni ile spontane kullanımı tart.",
        prompt="Saha erişimi nasıl olmalı?",
        option_a="Rezervasyon öncelikli",
        option_b="Belirli saatler serbest kullanım",
        domain="SPORTS",
        base_format="DILEMMA",
        perspectives=(
            PerspectiveEntry("NEAR", "Rezervasyon sistemi, planlamanın mümkün olduğunu ve sahanın sürekli dolu olduğu senaryolarda kullanım hakkını güvence altına alır."),
            PerspectiveEntry("OPPOSING", "Serbest saat dilimleri, özellikle çocuklar için spontane oyunu ve kendiliğinden gelişen topluluk bağını teşvik eder."),
            PerspectiveEntry("BRIDGE", "Belirli saatleri rezervasyona, diğerlerini serbest kullanıma açmak her iki ihtiyacı karşılayan yaygın bir modeldir."),
        ),
        context_blocks=(
            ContextBlock("ESSENTIAL", "Durum", "Mahallede tek bir spor sahası var; hem düzenli takımlar hem spontane oynamak isteyen bireyler bu sahayı kullanmak istiyor."),
        ),
    ),
)

CALLS: tuple[BetaCatalogCase, ...] = (
    BetaCatalogCase(
        slug="call-temas-faulu",
        title="Temas faul mü?",
        summary="Hızlı bir spor pozisyonunda temasın oyunun doğal parçası mı faul mü olduğunu tart.",
        prompt="Bu temas için kararın ne?",
        option_a="Devam",
        option_b="Faul",
        domain="SPORTS",
        base_format="CALL",
        perspectives=(
            PerspectiveEntry("NEAR", "Temas, oyunun doğal akışında meydana geldi; müdahale oyunun ritmini bozar."),
            PerspectiveEntry("OPPOSING", "Pozisyonun doğası ve temas açısı, kurallara göre faul sınırına giriyor."),
            PerspectiveEntry("BRIDGE", "Bu tür sınır durumlar için video teknolojisi (VAR/hawkeye), nesnel karar destek sistemi sunuyor."),
        ),
        context_blocks=(
            ContextBlock("ESSENTIAL", "Pozisyon", "Hızlı bir atakta iki oyuncu arasında minimal temas var. Pozisyon kısa sürede gelişti."),
        ),
    ),
    BetaCatalogCase(
        slug="call-top-cizgiyi-gecti",
        title="Top çizgiyi geçti mi?",
        summary="Sınırlı açıdaki bir pozisyonda saha içi karar ile ihtiyatlı değerlendirmeyi tart.",
        prompt="Saha içi kararın ne?",
        option_a="Oyun devam",
        option_b="Top dışarı",
        domain="SPORTS",
        base_format="CALL",
        perspectives=(
            PerspectiveEntry("NEAR", "Belirsiz pozisyonlarda oyun devam kararı, akışı korur ve avantaj kuralıyla örtüşür."),
            PerspectiveEntry("OPPOSING", "Top tamamen çizgiyi geçmişse kural açıktır; belirsizlik teknoloji ile giderilebilir."),
        ),
        context_blocks=(
            ContextBlock("ESSENTIAL", "Pozisyon", "Top, çizgiye çok yakın bir noktada sahadan çıkmış olabilir. Saha içi hakem sınırlı açıdan değerlendiriyor."),
        ),
    ),
    BetaCatalogCase(
        slug="call-hucum-faulu",
        title="Hücum faulü mü?",
        summary="Savunmacının konumu ile hücum oyuncusunun hareketini tart.",
        prompt="Pozisyon için kararın ne?",
        option_a="Savunma faulü/yok",
        option_b="Hücum faulü",
        domain="SPORTS",
        base_format="CALL",
        perspectives=(
            PerspectiveEntry("NEAR", "Savunmacı pozisyonunu tamamlamadan önce temas gerçekleşti; hücum oyuncusu durduramadı."),
            PerspectiveEntry("OPPOSING", "Savunmacı gerekli alanı kurmuştu; hücum oyuncusu kaçınabilirdi."),
        ),
        context_blocks=(
            ContextBlock("ESSENTIAL", "Pozisyon", "Hücum oyuncusu sürüyor, savunmacı yolunu kesiyor. Temas anında savunmacının pozisyon aldığı tartışmalı."),
        ),
    ),
    BetaCatalogCase(
        slug="call-el-temasi",
        title="El teması ihlal mi?",
        summary="Yakın mesafeden gelen top ile kolun konumunu tart.",
        prompt="Pozisyon için kararın ne?",
        option_a="Devam",
        option_b="İhlal",
        domain="SPORTS",
        base_format="CALL",
        perspectives=(
            PerspectiveEntry("NEAR", "Kol vücuda yakın ve doğal konumdaydı; top beklenmedik bir şekilde çarptı."),
            PerspectiveEntry("OPPOSING", "Kolun pozisyonu alanı genişletiyordu; bu da kural gereği ihlal sayılabilir."),
            PerspectiveEntry("BRIDGE", "El topu kuralları liglere ve dönemlere göre farklılık gösteriyor; bu durum hakemler için tutarlı karar vermeyi zorlaştırıyor."),
        ),
        context_blocks=(
            ContextBlock("ESSENTIAL", "Pozisyon", "Top kısa mesafeden oyuncunun koluna çarpıyor. Kolun vücuda olan açısı ve hareketin kasıtlı olup olmadığı tartışmalı."),
        ),
    ),
)

BETA_CATALOG: tuple[BetaCatalogCase, ...] = DILEMMAS + CALLS


def readiness_counts() -> dict[str, int]:
    # The canonical demo case is also L0 DILEMMA and is counted separately.
    return {
        "DILEMMA": len(DILEMMAS) + 1,
        "CALL": len(CALLS),
        "TOTAL": len(BETA_CATALOG) + 1,
    }