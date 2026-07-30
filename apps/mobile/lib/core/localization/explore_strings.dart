import 'kefe_strings.dart';

extension KefeExploreStrings on KefeStrings {
  bool get _isTurkish => locale.languageCode == 'tr';

  String get exploreTrendingWeighs => _isTurkish ? 'Trend tartımlar' : 'Trending weighs';
  String exploreCaseCount(int count) => _isTurkish ? '$count vaka' : '$count cases';
  String get exploreMoreComing => _isTurkish
      ? 'Yeni tartımlar hazırlandıkça burada görünecek.'
      : 'New weighs will appear here as they are prepared.';
  String get exploreWorldQuestion => _isTurkish
      ? 'Bugün dünya\nneyi tartıyor?'
      : 'What is the world\nweighing today?';
  String get exploreFeatured => _isTurkish ? 'ÖNE ÇIKAN' : 'FEATURED';

  String domainLabel(String domain) {
    return switch (domain) {
      'DAILY_LIFE' => _isTurkish ? 'Günlük yaşam' : 'Daily life',
      'TECHNOLOGY' || 'TECHNOLOGY_AI' => _isTurkish ? 'Teknoloji & YZ' : 'Technology & AI',
      'SPORTS' => _isTurkish ? 'Spor' : 'Sports',
      'CIVIC' || 'CITY_PUBLIC_LIFE' => _isTurkish ? 'Kamusal yaşam' : 'Public life',
      'WORK_ECONOMY' || 'WORK_BUSINESS' => _isTurkish ? 'İş & Ekonomi' : 'Work & Economy',
      'EDUCATION' => _isTurkish ? 'Eğitim' : 'Education',
      'FAMILY_PARENTING' => _isTurkish ? 'Aile & Ebeveynlik' : 'Family & Parenting',
      'CULTURE_MEDIA' => _isTurkish ? 'Kültür & Medya' : 'Culture & Media',
      _ => domain.replaceAll('_', ' '),
    };
  }
}
