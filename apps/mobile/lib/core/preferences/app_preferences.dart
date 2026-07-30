import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

enum AppLocalePreference { system, tr, en }

enum AppThemePreference { system, light, dark }

class AppPreferencesState {
  const AppPreferencesState({
    this.locale = AppLocalePreference.system,
    this.theme = AppThemePreference.system,
    this.loaded = false,
  });

  final AppLocalePreference locale;
  final AppThemePreference theme;
  final bool loaded;

  Locale? get resolvedLocale => switch (locale) {
    AppLocalePreference.system => null,
    AppLocalePreference.tr => const Locale('tr', 'TR'),
    AppLocalePreference.en => const Locale('en', 'US'),
  };

  ThemeMode get resolvedThemeMode => switch (theme) {
    AppThemePreference.system => ThemeMode.system,
    AppThemePreference.light => ThemeMode.light,
    AppThemePreference.dark => ThemeMode.dark,
  };

  AppPreferencesState copyWith({
    AppLocalePreference? locale,
    AppThemePreference? theme,
    bool? loaded,
  }) {
    return AppPreferencesState(
      locale: locale ?? this.locale,
      theme: theme ?? this.theme,
      loaded: loaded ?? this.loaded,
    );
  }
}

abstract interface class AppPreferencesStore {
  Future<AppPreferencesState> read();
  Future<void> writeLocale(AppLocalePreference value);
  Future<void> writeTheme(AppThemePreference value);
}

class SharedPreferencesAppPreferencesStore implements AppPreferencesStore {
  SharedPreferencesAppPreferencesStore({SharedPreferences? preferences})
    : _preferences = preferences;

  static const _localeKey = 'kefe.preferences.locale.v1';
  static const _themeKey = 'kefe.preferences.theme.v1';

  SharedPreferences? _preferences;

  Future<SharedPreferences> _prefs() async {
    return _preferences ??= await SharedPreferences.getInstance();
  }

  @override
  Future<AppPreferencesState> read() async {
    final preferences = await _prefs();
    final locale = AppLocalePreference.values.where(
      (item) => item.name == preferences.getString(_localeKey),
    );
    final theme = AppThemePreference.values.where(
      (item) => item.name == preferences.getString(_themeKey),
    );
    return AppPreferencesState(
      locale: locale.isEmpty ? AppLocalePreference.system : locale.first,
      theme: theme.isEmpty ? AppThemePreference.system : theme.first,
      loaded: true,
    );
  }

  @override
  Future<void> writeLocale(AppLocalePreference value) async {
    await (await _prefs()).setString(_localeKey, value.name);
  }

  @override
  Future<void> writeTheme(AppThemePreference value) async {
    await (await _prefs()).setString(_themeKey, value.name);
  }
}

class MemoryAppPreferencesStore implements AppPreferencesStore {
  MemoryAppPreferencesStore([this.value = const AppPreferencesState(loaded: true)]);

  AppPreferencesState value;

  @override
  Future<AppPreferencesState> read() async => value;

  @override
  Future<void> writeLocale(AppLocalePreference locale) async {
    value = value.copyWith(locale: locale, loaded: true);
  }

  @override
  Future<void> writeTheme(AppThemePreference theme) async {
    value = value.copyWith(theme: theme, loaded: true);
  }
}

final appPreferencesStoreProvider = Provider<AppPreferencesStore>((ref) {
  return SharedPreferencesAppPreferencesStore();
});

final appPreferencesControllerProvider =
    NotifierProvider<AppPreferencesController, AppPreferencesState>(
      AppPreferencesController.new,
    );

class AppPreferencesController extends Notifier<AppPreferencesState> {
  AppPreferencesStore get _store => ref.read(appPreferencesStoreProvider);

  @override
  AppPreferencesState build() => const AppPreferencesState();

  Future<void> load() async {
    if (state.loaded) return;
    state = await _store.read();
  }

  Future<void> setLocale(AppLocalePreference locale) async {
    state = state.copyWith(locale: locale, loaded: true);
    await _store.writeLocale(locale);
  }

  Future<void> setTheme(AppThemePreference theme) async {
    state = state.copyWith(theme: theme, loaded: true);
    await _store.writeTheme(theme);
  }
}
