import 'explore_string_catalog.dart';
import 'kefe_locale_catalog.dart';
import 'kefe_strings.dart';

extension KefeExploreStrings on KefeStrings {
  String _exploreText(
    String key, {
    Map<String, Object?> placeholders = const {},
  }) => KefeLocaleCatalog.resolve(
    locale: locale,
    resources: ExploreStringCatalog.resources,
    key: key,
    placeholders: placeholders,
  );

  String get exploreTrendingWeighs => _exploreText('trending_weighs');
  String exploreCaseCount(int count) =>
      _exploreText('case_count', placeholders: {'count': count});
  String get exploreMoreComing => _exploreText('more_coming');
  String get exploreWorldQuestion => _exploreText('world_question');
  String get exploreFeatured => _exploreText('featured');

  String domainLabel(String domain) => switch (domain) {
    'DAILY_LIFE' => _exploreText('domain.daily_life'),
    'TECHNOLOGY' || 'TECHNOLOGY_AI' => _exploreText('domain.technology_ai'),
    'SPORTS' => _exploreText('domain.sports'),
    'CIVIC' || 'CITY_PUBLIC_LIFE' => _exploreText('domain.public_life'),
    'WORK_ECONOMY' || 'WORK_BUSINESS' => _exploreText('domain.work_economy'),
    'EDUCATION' => _exploreText('domain.education'),
    'FAMILY_PARENTING' => _exploreText('domain.family_parenting'),
    'CULTURE_MEDIA' => _exploreText('domain.culture_media'),
    _ => domain.replaceAll('_', ' '),
  };
}
