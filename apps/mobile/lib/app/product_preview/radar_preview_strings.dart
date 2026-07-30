import 'package:flutter/widgets.dart';

import '../../core/localization/kefe_locale_catalog.dart';

class RadarPreviewStrings {
  const RadarPreviewStrings._(this._locale);

  final Locale _locale;

  static const KefeLocaleResources _catalog = {
    'tr': {
      'eyebrow': 'KEFE RADAR',
      'title': 'Dünya şu an\nneyi tartışıyor?',
      'notice':
          'Canlı trend verisi değil · Product Preview için temsili sıralama',
      'view.trends': 'Trendler',
      'view.rising': 'Yükselen',
      'view.global': 'Global',
      'domain.TECH_GLOBAL': 'TEKNOLOJİ · GLOBAL',
      'domain.SPORTS': 'SPOR',
      'domain.WORK': 'İŞ',
      'domain.DAILY_LIFE': 'GÜNLÜK YAŞAM',
      'domain.EDUCATION': 'EĞİTİM',
      'signal.RISING_DISCUSSION': 'Yükselen tartışma',
      'signal.SPORTS_CALL': 'Sports CALL',
      'signal.WORK_ECONOMY': 'İş & ekonomi',
      'signal.DAILY_DILEMMA': 'Günlük ikilem',
      'signal.EDUCATION': 'Eğitim',
      'rank': 'Sıra',
    },
    'en': {
      'eyebrow': 'KEFE RADAR',
      'title': 'What is the world\nweighing right now?',
      'notice':
          'Not live trend data · Representative ranking for Product Preview',
      'view.trends': 'Trends',
      'view.rising': 'Rising',
      'view.global': 'Global',
      'domain.TECH_GLOBAL': 'TECH · GLOBAL',
      'domain.SPORTS': 'SPORTS',
      'domain.WORK': 'WORK',
      'domain.DAILY_LIFE': 'DAILY LIFE',
      'domain.EDUCATION': 'EDUCATION',
      'signal.RISING_DISCUSSION': 'Rising discussion',
      'signal.SPORTS_CALL': 'Sports CALL',
      'signal.WORK_ECONOMY': 'Work & economy',
      'signal.DAILY_DILEMMA': 'Daily dilemma',
      'signal.EDUCATION': 'Education',
      'rank': 'Rank',
    },
  };

  static KefeLocaleResources get resources => _catalog;

  static RadarPreviewStrings of(BuildContext context) =>
      RadarPreviewStrings._(Localizations.localeOf(context));

  String _text(String id) => KefeLocaleCatalog.resolve(
    locale: _locale,
    resources: _catalog,
    key: id,
  );

  String get eyebrow => _text('eyebrow');
  String get title => _text('title');
  String get notice => _text('notice');
  String get trends => _text('view.trends');
  String get rising => _text('view.rising');
  String get global => _text('view.global');

  String domain(String code) => _text('domain.$code');
  String signal(String code) => _text('signal.$code');
  String rankLabel(int rank) => '${_text('rank')} $rank';
}
