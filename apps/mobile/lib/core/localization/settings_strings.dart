import 'kefe_strings.dart';

extension KefeSettingsStrings on KefeStrings {
  bool get _isTurkish => locale.languageCode == 'tr';

  String get settingsTitle => _isTurkish ? 'Ayarlar' : 'Settings';
  String get languageTitle => _isTurkish ? 'Dil' : 'Language';
  String get languageSystem =>
      _isTurkish ? 'Cihaz dilini kullan' : 'Use device language';
  String get languageTurkish => 'Türkçe';
  String get languageEnglish => 'English';
  String get appearanceTitle => _isTurkish ? 'Görünüm' : 'Appearance';
  String get themeSystem =>
      _isTurkish ? 'Cihaz ayarını kullan' : 'Use device setting';
  String get themeLight => _isTurkish ? 'Açık' : 'Light';
  String get themeDark => _isTurkish ? 'Koyu' : 'Dark';
  String get privacyAndData =>
      _isTurkish ? 'Gizlilik ve veriler' : 'Privacy and data';
  String get privacyAndDataHelper => _isTurkish
      ? 'Dışa aktarma, silme ve veri tercihlerini yönet.'
      : 'Manage export, deletion and data preferences.';
  String get internalPreviewLabel =>
      _isTurkish ? 'Dahili ürün önizlemesi' : 'Internal product preview';
}
