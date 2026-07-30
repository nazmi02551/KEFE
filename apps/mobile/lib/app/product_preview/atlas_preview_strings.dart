import 'package:flutter/widgets.dart';

import '../../core/localization/kefe_locale_catalog.dart';

class AtlasPreviewStrings {
  const AtlasPreviewStrings._(this._locale);

  final Locale _locale;

  static const KefeLocaleResources _catalog = {
    'tr': {
      'eyebrow': 'KEFE ATLAS',
      'title': 'Aynı soru,\nfarklı dünyalar.',
      'notice':
          'Atlas değerleri temsili Product Preview verisidir · gerçek ülke sonucu değildir',
      'selected_case': 'SEÇİLEN OLAY',
      'world_view': 'Dünya görünümü',
      'country_averages': 'Ülkelere göre ortalamalar',
      'average': 'Ortalama',
      'rules_rights': 'Kural / Hak',
      'empathy_compassion': 'Vicdan / Empati',
      'scale_helper': '0–10 temsili KEFE ekseni',
      'country.TR': 'Türkiye',
      'country.DE': 'Almanya',
      'country.US': 'ABD',
      'country.JP': 'Japonya',
      'country.BR': 'Brezilya',
      'country.ID': 'Endonezya',
    },
    'en': {
      'eyebrow': 'KEFE ATLAS',
      'title': 'Same question,\ndifferent worlds.',
      'notice':
          'Atlas values are representative Product Preview data · not real country results',
      'selected_case': 'SELECTED CASE',
      'world_view': 'World view',
      'country_averages': 'Country averages',
      'average': 'Average',
      'rules_rights': 'Rules / Rights',
      'empathy_compassion': 'Empathy / Compassion',
      'scale_helper': 'Representative 0–10 KEFE continuum',
      'country.TR': 'Türkiye',
      'country.DE': 'Germany',
      'country.US': 'USA',
      'country.JP': 'Japan',
      'country.BR': 'Brazil',
      'country.ID': 'Indonesia',
    },
  };

  static KefeLocaleResources get resources => _catalog;

  static AtlasPreviewStrings of(BuildContext context) =>
      AtlasPreviewStrings._(Localizations.localeOf(context));

  String _text(String id) =>
      KefeLocaleCatalog.resolve(locale: _locale, resources: _catalog, key: id);

  String get eyebrow => _text('eyebrow');
  String get title => _text('title');
  String get notice => _text('notice');
  String get selectedCase => _text('selected_case');
  String get worldView => _text('world_view');
  String get countryAverages => _text('country_averages');
  String get average => _text('average');
  String get rulesRights => _text('rules_rights');
  String get empathyCompassion => _text('empathy_compassion');
  String get scaleHelper => _text('scale_helper');
  String country(String code) => _text('country.$code');
}
