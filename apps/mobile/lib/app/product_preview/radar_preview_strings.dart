import 'package:flutter/widgets.dart';

class RadarPreviewStrings {
  const RadarPreviewStrings._(this._values);

  final Map<String, String> _values;

  static const _catalog = <String, Map<String, String>>{
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

  static RadarPreviewStrings of(BuildContext context) {
    final locale = Localizations.localeOf(context);
    final values = _catalog[locale.languageCode] ?? _catalog['en']!;
    return RadarPreviewStrings._(values);
  }

  String _text(String id) => _values[id] ?? _catalog['en']![id] ?? id;

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
