import 'kefe_locale_catalog.dart';

abstract final class SettingsStringCatalog {
  static const KefeLocaleResources resources = {
    'en': {
      'settings.title': 'Settings',
      'settings.loading': 'Loading your saved settings…',
      'settings.saving': 'Saving your setting…',
      'settings.unavailable':
          'Saved settings are unavailable. Your last confirmed choices are shown when possible.',
      'settings.retry': 'Retry',
      'language.title': 'Language',
      'language.system': 'Use device language',
      'language.turkish': 'Türkçe',
      'language.english': 'English',
      'appearance.title': 'Appearance',
      'theme.system': 'Use device setting',
      'theme.light': 'Light',
      'theme.dark': 'Dark',
      'account.title': 'Account and continuity',
      'account.helper':
          'Optionally link your current KEFE history to a verified email or phone. Guest use remains available.',
      'privacy.title': 'Privacy and data',
      'privacy.helper': 'Manage export, deletion and data preferences.',
      'preview.internal_label': 'Internal product preview',
    },
    'tr': {
      'settings.title': 'Ayarlar',
      'settings.loading': 'Kayıtlı ayarların yükleniyor…',
      'settings.saving': 'Ayarın kaydediliyor…',
      'settings.unavailable':
          'Kayıtlı ayarlara ulaşılamıyor. Mümkün olduğunda son doğrulanan seçimlerin gösterilir.',
      'settings.retry': 'Yeniden dene',
      'language.title': 'Dil',
      'language.system': 'Cihaz dilini kullan',
      'language.turkish': 'Türkçe',
      'language.english': 'English',
      'appearance.title': 'Görünüm',
      'theme.system': 'Cihaz ayarını kullan',
      'theme.light': 'Açık',
      'theme.dark': 'Koyu',
      'account.title': 'Hesap ve devamlılık',
      'account.helper':
          'Mevcut KEFE geçmişini istersen doğrulanmış e-posta veya telefonla ilişkilendir. Misafir olarak kullanmaya devam edebilirsin.',
      'privacy.title': 'Gizlilik ve veriler',
      'privacy.helper': 'Dışa aktarma, silme ve veri tercihlerini yönet.',
      'preview.internal_label': 'Dahili ürün önizlemesi',
    },
  };
}
