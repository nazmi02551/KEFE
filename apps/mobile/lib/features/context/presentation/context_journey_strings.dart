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

  String contextJourneyProgress(int current, int total) =>
      _contextJourneyText(
        'progress',
        placeholders: {'current': current, 'total': total},
      );

  String contextJourneyTitle(ContextJourneyLayer layer) =>
      _contextJourneyText('${layer.name}.title');

  String contextJourneyHelper(ContextJourneyLayer layer) =>
      _contextJourneyText('${layer.name}.helper');

  String get contextJourneyNext => _contextJourneyText('next');
  String get contextJourneyBack => _contextJourneyText('back');
  String get contextJourneyOptional => _contextJourneyText('optional');
}
