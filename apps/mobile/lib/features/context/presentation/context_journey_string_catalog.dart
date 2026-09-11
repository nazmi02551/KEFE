import '../../../core/localization/kefe_locale_catalog.dart';

/// Locale resources for the Context Journey feature (ADR-0142, CAP-069, CAP-070).
///
/// Single authoritative source for all context journey and information-status
/// guide strings. Referenced by both:
/// - ContextJourneyStrings extension (context_journey_strings.dart)
/// - KefeStrings instance methods (kefe_strings.dart) for contextInformationStatus*
abstract final class ContextJourneyStringCatalog {
  static const KefeLocaleResources resources = {
    'tr': {
      'progress': 'BAĞLAM {current}/{total}',
      'essential.title': 'Önce temel bilgileri incele',
      'essential.helper':
          'Karar için gerekli kısa özet ve doğrulama durumları burada.',
      'details.title': 'Ayrıntılara bak',
      'details.helper':
          'Bu katman isteğe bağlıdır; temel bilgileri genişleten ayrıntıları gösterir.',
      'sources.title': 'Kaynakları incele',
      'sources.helper':
          'Bilgilerin dayandığı yayıncı ve kaynak türlerini burada görebilirsin.',
      'sources.reference': 'Kaynak kaydı',
      'sources.published': 'Yayın tarihi: {date}',
      'status.guide.title': 'Bilgi durumları ne anlama geliyor?',
      'status.guide.helper':
          'Durum bilgi bloğuna aittir; bağlı kaynağı ayrıca doğrulamaz.',
      'status.verified.helper':
          'Editoryal kayıt bu bilgi bloğunu kontrol edilmiş olarak işaretler.',
      'status.claimed.helper':
          'Bu blok bir iddia sunar; doğrulanmış olarak işaretlenmez.',
      'status.disputed.helper':
          'Mevcut kayıtlarda bu bilgi bloğu hakkında uyuşmazlık vardır.',
      'status.unknown.helper':
          'Mevcut kayıt bu bilgi bloğu için bir durum belirlemiyor.',
      'next': 'Sonraki katman',
      'back': 'Önceki katman',
      'optional': 'İsteğe bağlı',
    },
    'en': {
      'progress': 'CONTEXT {current}/{total}',
      'essential.title': 'Review the essential information first',
      'essential.helper':
          'The short decision context and verification states appear here.',
      'details.title': 'Inspect the details',
      'details.helper':
          'This optional layer expands the essential information.',
      'sources.title': 'Review the sources',
      'sources.helper':
          'See the publishers and source types supporting the information.',
      'sources.reference': 'Source reference',
      'sources.published': 'Published: {date}',
      'status.guide.title': 'What do these information states mean?',
      'status.guide.helper':
          'A state belongs to the information block; it does not independently verify a linked source.',
      'status.verified.helper':
          'The editorial record marks this information block as checked.',
      'status.claimed.helper':
          'This block presents a claim and is not marked as verified.',
      'status.disputed.helper':
          'The available record contains disagreement about this information block.',
      'status.unknown.helper':
          'The current record does not establish a state for this information block.',
      'next': 'Next layer',
      'back': 'Previous layer',
      'optional': 'Optional',
    },
  };
}