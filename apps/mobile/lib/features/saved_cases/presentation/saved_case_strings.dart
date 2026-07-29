import '../../../core/localization/kefe_strings.dart';

extension SavedCaseStrings on KefeStrings {
  bool get _savedCaseIsTurkish => locale.languageCode == 'tr';

  String get savedCasesTitle =>
      _savedCaseIsTurkish ? 'Kaydettiklerin' : 'Saved Cases';
  String get savedCasesSubtitle => _savedCaseIsTurkish
      ? 'Daha sonra tartmak için ayırdığın vakalar.'
      : 'Cases you kept for a later weigh.';
  String get savedCasesEmpty => _savedCaseIsTurkish
      ? 'Henüz kaydettiğin bir vaka yok.'
      : 'You have not saved a Case yet.';
  String get savedCasesOpen => _savedCaseIsTurkish ? 'Vakayı aç' : 'Open Case';
  String get savedCasesRemove =>
      _savedCaseIsTurkish ? 'Kayıttan çıkar' : 'Remove from saved';
  String get savedCasesSave =>
      _savedCaseIsTurkish ? 'Daha sonra için kaydet' : 'Save for later';
  String get exploreSearchHint => _savedCaseIsTurkish
      ? 'Vaka başlığı veya özeti ara'
      : 'Search Case title or summary';
  String get exploreAllDomains => _savedCaseIsTurkish ? 'Tümü' : 'All';
  String get exploreSavedOnly =>
      _savedCaseIsTurkish ? 'Yalnızca kaydettiklerim' : 'Saved only';
  String get exploreClearFilters =>
      _savedCaseIsTurkish ? 'Filtreleri temizle' : 'Clear filters';
  String get exploreNoResults => _savedCaseIsTurkish
      ? 'Bu arama ve filtrelerle eşleşen vaka yok.'
      : 'No Cases match this search and filter.';
  String get exploreDiscoveryLabel =>
      _savedCaseIsTurkish ? 'Vakaları keşfet' : 'Discover Cases';
}