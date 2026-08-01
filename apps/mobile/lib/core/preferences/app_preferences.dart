import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

enum AppLocalePreference { system, tr, en }

enum AppThemePreference { system, light, dark }

enum AppPreferencesStatus { idle, loading, ready, saving, error }

enum AppPreferencesFailure { read, write }

class AppPreferencesState {
  const AppPreferencesState({
    this.locale = AppLocalePreference.system,
    this.theme = AppThemePreference.system,
    bool loaded = false,
    AppPreferencesStatus? status,
    this.failure,
  }) : status = status ??
            (loaded ? AppPreferencesStatus.ready : AppPreferencesStatus.idle);

  final AppLocalePreference locale;
  final AppThemePreference theme;
  final AppPreferencesStatus status;
  final AppPreferencesFailure? failure;

  bool get loaded =>
      status == AppPreferencesStatus.ready ||
      status == AppPreferencesStatus.saving ||
      (status == AppPreferencesStatus.error &&
          failure == AppPreferencesFailure.write);

  bool get loading => status == AppPreferencesStatus.loading;
  bool get saving => status == AppPreferencesStatus.saving;
  bool get hasError => status == AppPreferencesStatus.error;

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
    AppPreferencesStatus? status,
    AppPreferencesFailure? failure,
    bool clearFailure = false,
  }) {
    final resolvedStatus = status ??
        (loaded == null
            ? this.status
            : loaded
            ? AppPreferencesStatus.ready
            : AppPreferencesStatus.idle);
    return AppPreferencesState(
      locale: locale ?? this.locale,
      theme: theme ?? this.theme,
      status: resolvedStatus,
      failure: clearFailure ? null : failure ?? this.failure,
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
  MemoryAppPreferencesStore([
    this.value = const AppPreferencesState(loaded: true),
  ]);

  AppPreferencesState value;

  @override
  Future<AppPreferencesState> read() async => value;

  @override
  Future<void> writeLocale(AppLocalePreference locale) async {
    value = value.copyWith(locale: locale, loaded: true, clearFailure: true);
  }

  @override
  Future<void> writeTheme(AppThemePreference theme) async {
    value = value.copyWith(theme: theme, loaded: true, clearFailure: true);
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
  bool _loadInFlight = false;
  bool _writeInFlight = false;

  AppPreferencesStore get _store => ref.read(appPreferencesStoreProvider);

  @override
  AppPreferencesState build() => const AppPreferencesState();

  Future<void> load({bool force = false}) async {
    if (_loadInFlight || _writeInFlight) return;
    if (state.loaded && !force) return;

    _loadInFlight = true;
    state = state.copyWith(
      status: AppPreferencesStatus.loading,
      clearFailure: true,
    );
    try {
      final persisted = await _store.read();
      state = persisted.copyWith(
        status: AppPreferencesStatus.ready,
        clearFailure: true,
      );
    } on Object {
      state = state.copyWith(
        status: AppPreferencesStatus.error,
        failure: AppPreferencesFailure.read,
      );
    } finally {
      _loadInFlight = false;
    }
  }

  Future<void> retry() => load(force: true);

  Future<void> setLocale(AppLocalePreference locale) async {
    final next = state.copyWith(
      locale: locale,
      status: AppPreferencesStatus.ready,
      clearFailure: true,
    );
    await _persist(
      next: next,
      write: () => _store.writeLocale(locale),
    );
  }

  Future<void> setTheme(AppThemePreference theme) async {
    final next = state.copyWith(
      theme: theme,
      status: AppPreferencesStatus.ready,
      clearFailure: true,
    );
    await _persist(
      next: next,
      write: () => _store.writeTheme(theme),
    );
  }

  Future<void> _persist({
    required AppPreferencesState next,
    required Future<void> Function() write,
  }) async {
    if (_loadInFlight || _writeInFlight || !state.loaded) return;

    final persisted = state.copyWith(
      status: AppPreferencesStatus.ready,
      clearFailure: true,
    );
    _writeInFlight = true;
    state = next.copyWith(
      status: AppPreferencesStatus.saving,
      clearFailure: true,
    );
    try {
      await write();
      state = state.copyWith(
        status: AppPreferencesStatus.ready,
        clearFailure: true,
      );
    } on Object {
      state = persisted.copyWith(
        status: AppPreferencesStatus.error,
        failure: AppPreferencesFailure.write,
      );
    } finally {
      _writeInFlight = false;
    }
  }
}
