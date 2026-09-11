import '../../../core/localization/kefe_locale_catalog.dart';
import '../../../core/localization/kefe_strings.dart';
import 'observatory_string_catalog.dart';

extension ObservatoryStrings on KefeStrings {
  String _obs(
    String key, {
    Map<String, Object?> placeholders = const {},
  }) =>
      KefeLocaleCatalog.resolve(
        locale: locale,
        resources: ObservatoryStringCatalog.resources,
        key: key,
        placeholders: placeholders,
      );

  String get observatoryScreenTitle => _obs('screen.title');
  String get observatoryEyebrow => _obs('eyebrow');
  String get observatoryHeaderTitle => _obs('header.title');
  String get observatoryHeaderBody => _obs('header.body');
  String get observatorySignalsSectionTitle => _obs('signals.section.title');
  String get observatorySignalsSectionBody => _obs('signals.section.body');
  String get observatorySignalsEmpty => _obs('signals.empty');
  String get observatoryInstitutionSectionTitle =>
      _obs('institution.section.title');
  String get observatoryInstitutionSectionBody =>
      _obs('institution.section.body');
  String get observatoryInstitutionEmpty => _obs('institution.empty');
}