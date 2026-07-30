import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/preferences/app_preferences.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('defaults to device locale and theme', () async {
    SharedPreferences.setMockInitialValues({});
    final store = SharedPreferencesAppPreferencesStore();

    final state = await store.read();

    expect(state.loaded, isTrue);
    expect(state.locale, AppLocalePreference.system);
    expect(state.theme, AppThemePreference.system);
    expect(state.resolvedLocale, isNull);
    expect(state.resolvedThemeMode, ThemeMode.system);
  });

  test('persists explicit English and dark preferences', () async {
    SharedPreferences.setMockInitialValues({});
    final store = SharedPreferencesAppPreferencesStore();

    await store.writeLocale(AppLocalePreference.en);
    await store.writeTheme(AppThemePreference.dark);

    final restored = await SharedPreferencesAppPreferencesStore().read();
    expect(restored.locale, AppLocalePreference.en);
    expect(restored.theme, AppThemePreference.dark);
    expect(restored.resolvedLocale, const Locale('en', 'US'));
    expect(restored.resolvedThemeMode, ThemeMode.dark);
  });

  test('persists Turkish and light preferences independently of account', () async {
    SharedPreferences.setMockInitialValues({});
    final store = SharedPreferencesAppPreferencesStore();

    await store.writeLocale(AppLocalePreference.tr);
    await store.writeTheme(AppThemePreference.light);

    final restored = await store.read();
    expect(restored.resolvedLocale, const Locale('tr', 'TR'));
    expect(restored.resolvedThemeMode, ThemeMode.light);
  });
}
