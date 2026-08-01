import 'kefe_locale_catalog.dart';
import 'kefe_strings.dart';
import 'settings_string_catalog.dart';

extension KefeSettingsStrings on KefeStrings {
  String _settingsText(String key) => KefeLocaleCatalog.resolve(
    locale: locale,
    resources: SettingsStringCatalog.resources,
    key: key,
  );

  String get settingsTitle => _settingsText('settings.title');
  String get settingsLoading => _settingsText('settings.loading');
  String get settingsSaving => _settingsText('settings.saving');
  String get settingsUnavailable => _settingsText('settings.unavailable');
  String get settingsRetry => _settingsText('settings.retry');
  String get languageTitle => _settingsText('language.title');
  String get languageSystem => _settingsText('language.system');
  String get languageTurkish => _settingsText('language.turkish');
  String get languageEnglish => _settingsText('language.english');
  String get appearanceTitle => _settingsText('appearance.title');
  String get themeSystem => _settingsText('theme.system');
  String get themeLight => _settingsText('theme.light');
  String get themeDark => _settingsText('theme.dark');
  String get privacyAndData => _settingsText('privacy.title');
  String get privacyAndDataHelper => _settingsText('privacy.helper');
  String get internalPreviewLabel => _settingsText('preview.internal_label');
}
