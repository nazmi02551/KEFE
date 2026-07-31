import '../../../core/localization/kefe_locale_catalog.dart';
import '../../../core/localization/kefe_strings.dart';
import '../localization/saved_case_string_catalog.dart';

extension SavedCaseStrings on KefeStrings {
  String _savedCaseText(String key) => KefeLocaleCatalog.resolve(
    locale: locale,
    resources: SavedCaseStringCatalog.resources,
    key: key,
  );

  String get savedCasesTitle => _savedCaseText('saved.title');
  String get savedCasesSubtitle => _savedCaseText('saved.subtitle');
  String get savedCasesEmpty => _savedCaseText('saved.empty');
  String get savedCasesOpen => _savedCaseText('saved.open');
  String get savedCasesRemove => _savedCaseText('saved.remove');
  String get savedCasesSave => _savedCaseText('saved.save');
  String get exploreSearchHint => _savedCaseText('explore.search_hint');
  String get exploreAllDomains => _savedCaseText('explore.all_domains');
  String get exploreSavedOnly => _savedCaseText('explore.saved_only');
  String get exploreClearFilters => _savedCaseText('explore.clear_filters');
  String get exploreNoResults => _savedCaseText('explore.no_results');
  String get exploreDiscoveryLabel => _savedCaseText('explore.discovery_label');
}
