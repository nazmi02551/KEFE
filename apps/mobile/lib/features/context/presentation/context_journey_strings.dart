import '../../../core/localization/kefe_locale_catalog.dart';
import '../../../core/localization/kefe_strings.dart';
import 'context_journey_string_catalog.dart';

export 'context_journey_string_catalog.dart';

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
  // contextInformationStatusGuideTitle, contextInformationStatusGuideHelper,
  // contextInformationStatusDescription are defined as instance methods on
  // KefeStrings (core_string_catalog.dart). Instance methods take precedence
  // over extension methods in Dart, so the extension versions were dead code.
  // They have been removed here to avoid confusion.
  String get contextJourneyNext => _contextJourneyText('next');
  String get contextJourneyBack => _contextJourneyText('back');
  String get contextJourneyOptional => _contextJourneyText('optional');

  static String _contextIsoDate(DateTime value) {
    final utc = value.toUtc();
    String twoDigits(int number) => number.toString().padLeft(2, '0');
    return '${utc.year}-${twoDigits(utc.month)}-${twoDigits(utc.day)}';
  }
}
