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
      'saved.open_updated': 'Open current Case',
      'saved.remove': 'Remove from saved',
      'saved.save': 'Save for later',
      'saved.updated': 'Case updated',
      'saved.updated_hint':
          'A new published version is available. Opening it marks this update as seen.',
      'saved.update_count.one': '{count} saved Case updated',
      'saved.update_count.many': '{count} saved Cases updated',
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
      'saved.open_updated': 'Güncel vakayı aç',
      'saved.remove': 'Kayıttan çıkar',
      'saved.save': 'Daha sonra için kaydet',
      'saved.updated': 'Vaka güncellendi',
      'saved.updated_hint':
          'Yeni bir sürüm yayımlandı. Açtığında bu güncelleme görüldü sayılır.',
      'saved.update_count.one': '{count} kayıtlı vaka güncellendi',
      'saved.update_count.many': '{count} kayıtlı vaka güncellendi',
      'explore.search_hint': 'Vaka başlığı veya özeti ara',
      'explore.all_domains': 'Tümü',
      'explore.saved_only': 'Yalnızca kaydettiklerim',
      'explore.clear_filters': 'Filtreleri temizle',
      'explore.no_results': 'Bu arama ve filtrelerle eşleşen vaka yok.',
      'explore.discovery_label': 'Vakaları keşfet',
    },
  };
}
