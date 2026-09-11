import '../../../core/localization/kefe_locale_catalog.dart';

abstract final class ObservatoryStringCatalog {
  static const KefeLocaleResources resources = {
    'tr': {
      'screen.title': 'Kamusal Gözlemevi',
      'eyebrow': 'KAMUSAL GÖZLEMEVİ (CAP-016 & CAP-049)',
      'header.title': 'Sinyal ve Etki Takip Masası',
      'header.body':
          'Ön-karar manipülasyonlarından arındırılmış kamusal uzlaşı odakları ve yetkili kamu kurumlarının resmi taahhütleri.',
      'signals.section.title': 'Nitelikli Topluluk Uzlaşı Sinyalleri',
      'signals.section.body':
          'Bireysel oylardan bağımsız, bot ve astroturfing filtrelerinden geçmiş sertifikalı uzlaşı haritaları.',
      'signals.empty': 'Şu anda yayımlanmış kamusal uzlaşı sinyali bulunmuyor.',
      'institution.section.title': 'Doğrulanmış Kurum Yanıtları ve Taahhütler',
      'institution.section.body':
          'Uzlaşı sinyallerine bakanlıklar, belediyeler ve sivil toplum kuruluşlarınca verilen resmi yanıtlar.',
      'institution.empty': 'Henüz doğrulanmış bir kurumsal yanıt kaydı yok.',
    },
    'en': {
      'screen.title': 'Public Observatory',
      'eyebrow': 'PUBLIC OBSERVATORY (CAP-016 & CAP-049)',
      'header.title': 'Signal & Impact Desk',
      'header.body':
          'Methodology-qualified public consensus signals and official commitments from verified authorities.',
      'signals.section.title': 'Qualified Community Consensus Signals',
      'signals.section.body':
          'Certified societal consensus patterns filtered from bot manipulation and astroturfing.',
      'signals.empty': 'No public consensus signals currently published.',
      'institution.section.title': 'Verified Institution Responses & Pledges',
      'institution.section.body':
          'Official responses from ministries, municipalities, and verified institutions.',
      'institution.empty': 'No verified institutional response records yet.',
    },
  };
}