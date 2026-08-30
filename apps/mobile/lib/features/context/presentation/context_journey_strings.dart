import '../../../core/localization/kefe_locale_catalog.dart';
import '../../../core/localization/kefe_strings.dart';

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

enum ContextJourneyLayer { essential, details, sources }

extension ContextJourneyStrings on KefeStrings {
  String _contextJourneyText(
    String key, {
    Map<String, Object?> placeholders = const {},
  }) => KefeLocaleCatalog.resolve(
    locale: locale,
    resources: ContextJourneyStringCatalog.resources,
    key: key,
    placeholders: placeholders,
  );

  String contextJourneyProgress(int current, int total) => _contextJourneyText(
    'progress',
    placeholders: {'current': current, 'total': total},
  );

  String contextJourneyTitle(ContextJourneyLayer layer) =>
      _contextJourneyText('${layer.name}.title');

  String contextJourneyHelper(ContextJourneyLayer layer) =>
      _contextJourneyText('${layer.name}.helper');

  String get contextJourneySourceReference =>
      _contextJourneyText('sources.reference');
  String contextJourneySourcePublished(DateTime value) => _contextJourneyText(
    'sources.published',
    placeholders: {'date': _contextIsoDate(value)},
  );
  String get contextInformationStatusGuideTitle =>
      _contextJourneyText('status.guide.title');
  String get contextInformationStatusGuideHelper =>
      _contextJourneyText('status.guide.helper');
  String contextInformationStatusDescription(String status) =>
      _contextJourneyText('status.${status.toLowerCase()}.helper');
  String get contextJourneyNext => _contextJourneyText('next');
  String get contextJourneyBack => _contextJourneyText('back');
  String get contextJourneyOptional => _contextJourneyText('optional');

  static String _contextIsoDate(DateTime value) {
    final utc = value.toUtc();
    String twoDigits(int number) => number.toString().padLeft(2, '0');
    return '${utc.year}-${twoDigits(utc.month)}-${twoDigits(utc.day)}';
  }
}
