from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid5

CATALOG_NAMESPACE = UUID("5a2f93ad-2cc6-43e8-8b84-563b757a0b10")


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


# Engineering readiness catalog. Copy remains L0 and illustrative until human CQB approval.
# The existing Son koltuk demo is the 20th L0 DILEMMA.
DILEMMAS: tuple[BetaCatalogCase, ...] = (
    BetaCatalogCase("sirada-acil-ihtiyac", "Sırada acil ihtiyaç", "Sıra hakkı ile açık aciliyet çatıştığında önceliği tart.", "Kime öncelik verilmeli?", "Sıradaki kişiye", "Acil ihtiyacı olana", "DAILY_LIFE", "DILEMMA"),
    BetaCatalogCase("sessiz-vagon-cocuk", "Sessiz vagonda çocuk", "Sessizlik beklentisi ile ailelerin kamusal alan kullanımı arasındaki dengeyi tart.", "Öncelik hangisinde olmalı?", "Sessiz vagon kuralında", "Ailenin birlikte yolculuğunda", "FAMILY_PARENTING", "DILEMMA"),
    BetaCatalogCase("ortak-mutfak-son-porsiyon", "Ortak mutfakta son porsiyon", "Eşit paylaşım ile o anda daha fazla ihtiyacı olan kişiyi tart.", "Son porsiyon nasıl ayrılmalı?", "Eşit sıraya göre", "İhtiyaca göre", "DAILY_LIFE", "DILEMMA"),
    BetaCatalogCase("sinif-proje-gorev", "Grup projesinde görev", "Herkese eşit görev vermek ile güçlü yönlere göre iş bölümü yapmayı tart.", "Görevler nasıl bölüşülmeli?", "Eşit miktarda", "Yetkinliğe göre", "EDUCATION", "DILEMMA"),
    BetaCatalogCase("ofiste-hibrit-gun", "Ofiste hibrit gün", "Ekip koordinasyonu ile bireysel esnekliği tart.", "Ortak ofis günü nasıl belirlenmeli?", "Tek ortak gün zorunlu", "Ekipler kendisi seçsin", "WORK_BUSINESS", "DILEMMA"),
    BetaCatalogCase("parkta-sessiz-etkinlik", "Parkta etkinlik", "Mahalle huzuru ile kamusal alanın canlı kullanımını tart.", "Akşam etkinliği için ne yapılmalı?", "Erken bitirilmeli", "Belirli saate kadar sürmeli", "CITY_PUBLIC_LIFE", "DILEMMA"),
    BetaCatalogCase("kutuphane-grup-calisma", "Kütüphanede grup çalışması", "Sessiz çalışma hakkı ile ortak öğrenme alanı ihtiyacını tart.", "Alan kullanımı nasıl düzenlenmeli?", "Tam sessizlik", "Ayrılmış grup bölümü", "EDUCATION", "DILEMMA"),
    BetaCatalogCase("yapay-zeka-odev", "Ödevde yapay zekâ", "Öğrenme emeği ile yeni araçlardan yararlanmayı tart.", "YZ kullanımı nasıl ele alınmalı?", "Kullanılmamalı", "Kaynak göstererek kullanılmalı", "TECHNOLOGY_AI", "DILEMMA"),
    BetaCatalogCase("toplanti-kamera", "Çevrim içi toplantıda kamera", "Ekip iletişimi ile mahremiyet/esnekliği tart.", "Kamera politikası ne olmalı?", "Genelde açık", "Kişinin tercihine bırakılmalı", "WORK_BUSINESS", "DILEMMA"),
    BetaCatalogCase("mahalle-otopark", "Mahallede sınırlı otopark", "İlk gelen hakkı ile özel ihtiyacı olanlara ayrılan alanı tart.", "Boş alan önceliği nasıl olmalı?", "İlk gelene", "Belirlenmiş ihtiyaca", "CITY_PUBLIC_LIFE", "DILEMMA"),
    BetaCatalogCase("aile-tatil-butcesi", "Aile tatil bütçesi", "Herkesin eşit söz hakkı ile bütçeyi sağlayanın tercih ağırlığını tart.", "Karar nasıl alınmalı?", "Herkes eşit oy", "Katkı oranı da dikkate alınsın", "FAMILY_PARENTING", "DILEMMA"),
    BetaCatalogCase("takim-son-penalti", "Takımın son penaltısı", "En formda oyuncu ile takım liderinin sorumluluğunu tart.", "Son penaltıyı kim kullanmalı?", "En formda oyuncu", "Belirlenmiş kaptan/lider", "SPORTS", "DILEMMA"),
    BetaCatalogCase("muzede-fotograf", "Müzede fotoğraf", "Ziyaretçi deneyimi ile eser/alan düzenini tart.", "Fotoğraf politikası nasıl olmalı?", "Serbest olmalı", "Belirli bölümlerde sınırlı olmalı", "CULTURE_MEDIA", "DILEMMA"),
    BetaCatalogCase("restoranda-rezervasyon", "Geciken rezervasyon", "Rezervasyon hakkı ile bekleyen müşterilerin hakkını tart.", "Masa kime verilmeli?", "Rezervasyon sahibine biraz daha beklenmeli", "Bekleyen müşteriye verilmeli", "DAILY_LIFE", "DILEMMA"),
    BetaCatalogCase("okul-kulubu-kontenjan", "Okul kulübünde kontenjan", "İlk başvuru ile fırsat eşitliğini tart.", "Kontenjan nasıl dağıtılmalı?", "İlk başvurana", "Kura ile", "EDUCATION", "DILEMMA"),
    BetaCatalogCase("apartman-ortak-alan", "Apartman ortak alanı", "Sessiz kullanım ile sosyal ortak alan ihtiyacını tart.", "Akşam kullanımı nasıl olmalı?", "Sessiz kullanım öncelikli", "Belirli saate kadar sosyal kullanım", "CITY_PUBLIC_LIFE", "DILEMMA"),
    BetaCatalogCase("etkinlik-bilet-iade", "Etkinlik bileti iadesi", "Katı satış koşulu ile beklenmedik durumlarda esnekliği tart.", "İade politikası nasıl olmalı?", "Satış koşulu aynen uygulansın", "Belirli şartlarda esneklik olsun", "CULTURE_MEDIA", "DILEMMA"),
    BetaCatalogCase("ekip-basari-odulu", "Ekip başarı ödülü", "Eşit ekip payı ile bireysel katkı farklarını tart.", "Ödül nasıl dağıtılmalı?", "Eşit paylaşılmalı", "Katkıya göre farklılaşmalı", "WORK_BUSINESS", "DILEMMA"),
    BetaCatalogCase("mahalle-spor-sahasi", "Mahalle spor sahası", "Rezervasyon düzeni ile spontane kullanımı tart.", "Saha erişimi nasıl olmalı?", "Rezervasyon öncelikli", "Belirli saatler serbest kullanım", "SPORTS", "DILEMMA"),
)

CALLS: tuple[BetaCatalogCase, ...] = (
    BetaCatalogCase("call-temas-faulu", "Temas faul mü?", "Hızlı bir spor pozisyonunda temasın oyunun doğal parçası mı faul mü olduğunu tart.", "Bu temas için kararın ne?", "Devam", "Faul", "SPORTS", "CALL"),
    BetaCatalogCase("call-top-cizgiyi-gecti", "Top çizgiyi geçti mi?", "Sınırlı açıdaki bir pozisyonda saha içi karar ile ihtiyatlı değerlendirmeyi tart.", "Saha içi kararın ne?", "Oyun devam", "Top dışarı", "SPORTS", "CALL"),
    BetaCatalogCase("call-hucum-faulu", "Hücum faulü mü?", "Savunmacının konumu ile hücum oyuncusunun hareketini tart.", "Pozisyon için kararın ne?", "Savunma faulü/yok", "Hücum faulü", "SPORTS", "CALL"),
    BetaCatalogCase("call-el-temasi", "El teması ihlal mi?", "Yakın mesafeden gelen top ile kolun konumunu tart.", "Pozisyon için kararın ne?", "Devam", "İhlal", "SPORTS", "CALL"),
)

BETA_CATALOG: tuple[BetaCatalogCase, ...] = DILEMMAS + CALLS


def readiness_counts() -> dict[str, int]:
    # The canonical demo case is also L0 DILEMMA and is counted separately.
    return {
        "DILEMMA": len(DILEMMAS) + 1,
        "CALL": len(CALLS),
        "TOTAL": len(BETA_CATALOG) + 1,
    }
