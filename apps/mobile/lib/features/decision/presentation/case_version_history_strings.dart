import '../../../core/localization/kefe_locale_catalog.dart';
import '../../../core/localization/kefe_strings.dart';

abstract final class CaseVersionHistoryStringCatalog {
  static const KefeLocaleResources resources = {
    'en': {
      'title': 'Published version history',
      'helper':
          'Only versions that were previously public are shown. A previous version does not by itself mean a correction was made.',
      'loading': 'Loading published version history…',
      'unavailable':
          'Published version history is unavailable. You can still review and weigh this case.',
      'retry': 'Try history again',
      'current': 'Current published version',
      'previous': 'Previous published version',
      'single': 'No previous published version is available.',
      'count': '{count} public versions',
      'version': 'Version {version}',
      'published': 'Published {date}',
    },
    'tr': {
      'title': 'Yayımlanmış sürüm geçmişi',
      'helper':
          'Yalnız daha önce kamuya açılmış sürümler gösterilir. Önceki bir sürüm tek başına düzeltme yapıldığı anlamına gelmez.',
      'loading': 'Yayımlanmış sürüm geçmişi yükleniyor…',
      'unavailable':
          'Yayımlanmış sürüm geçmişine şu anda ulaşılamıyor. Vakayı incelemeye ve tartmaya devam edebilirsin.',
      'retry': 'Geçmişi yeniden dene',
      'current': 'Güncel yayımlanmış sürüm',
      'previous': 'Önceki yayımlanmış sürüm',
      'single': 'Önceki bir yayımlanmış sürüm bulunmuyor.',
      'count': '{count} yayımlanmış sürüm',
      'version': 'Sürüm {version}',
      'published': 'Yayımlanma {date}',
    },
  };
}

extension CaseVersionHistoryStrings on KefeStrings {
  String _historyText(
    String key, {
    Map<String, Object?> placeholders = const {},
  }) => KefeLocaleCatalog.resolve(
    locale: locale,
    resources: CaseVersionHistoryStringCatalog.resources,
    key: key,
    placeholders: placeholders,
  );

  String get caseHistoryTitle => _historyText('title');
  String get caseHistoryHelper => _historyText('helper');
  String get caseHistoryLoading => _historyText('loading');
  String get caseHistoryUnavailable => _historyText('unavailable');
  String get caseHistoryRetry => _historyText('retry');
  String get caseHistoryCurrent => _historyText('current');
  String get caseHistoryPrevious => _historyText('previous');
  String get caseHistorySingle => _historyText('single');
  String caseHistoryCount(int count) =>
      _historyText('count', placeholders: {'count': count});
  String caseHistoryVersion(int version) =>
      _historyText('version', placeholders: {'version': version});
  String caseHistoryPublished(DateTime value) =>
      _historyText('published', placeholders: {'date': _isoDate(value)});

  static String _isoDate(DateTime value) {
    final utc = value.toUtc();
    String twoDigits(int number) => number.toString().padLeft(2, '0');
    return '${utc.year}-${twoDigits(utc.month)}-${twoDigits(utc.day)}';
  }
}
