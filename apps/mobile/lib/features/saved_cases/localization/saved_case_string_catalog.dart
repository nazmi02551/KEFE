import '../../../core/localization/kefe_locale_catalog.dart';

abstract final class SavedCaseStringCatalog {
  static const KefeLocaleResources resources = {
    'en': {
      'saved.title': 'Saved Cases',
      'saved.subtitle': 'Cases you kept for a later weigh.',
      'saved.loading': 'Loading your saved Cases…',
      'saved.unavailable':
          'Saved Cases could not be refreshed. Your last available list remains visible.',
      'saved.retry': 'Try again',
      'saved.empty': 'You have not saved a Case yet.',
      'saved.open': 'Open Case',
      'saved.remove': 'Remove from saved',
      'saved.save': 'Save for later',
      'explore.search_hint': 'Search Case title or summary',
      'explore.all_domains': 'All',
      'explore.saved_only': 'Saved only',
      'explore.clear_filters': 'Clear filters',
      'explore.no_results': 'No Cases match this search and filter.',
      'explore.discovery_label': 'Discover Cases',
    },
    'tr': {
      'saved.title': 'Kaydettiklerin',
      'saved.subtitle': 'Daha sonra tartmak için ayırdığın vakalar.',
      'saved.loading': 'Kaydettiğin vakalar yükleniyor…',
      'saved.unavailable':
          'Kaydedilen vakalar yenilenemedi. Son erişilebilen listen görünmeye devam ediyor.',
      'saved.retry': 'Yeniden dene',
      'saved.empty': 'Henüz kaydettiğin bir vaka yok.',
      'saved.open': 'Vakayı aç',
      'saved.remove': 'Kayıttan çıkar',
      'saved.save': 'Daha sonra için kaydet',
      'explore.search_hint': 'Vaka başlığı veya özeti ara',
      'explore.all_domains': 'Tümü',
      'explore.saved_only': 'Yalnızca kaydettiklerim',
      'explore.clear_filters': 'Filtreleri temizle',
      'explore.no_results': 'Bu arama ve filtrelerle eşleşen vaka yok.',
      'explore.discovery_label': 'Vakaları keşfet',
    },
  };
}
