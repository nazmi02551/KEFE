import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/core/preferences/app_preferences.dart';
import 'package:kefe_mobile/features/settings/presentation/settings_screen.dart';

void main() {
  test('Slice 30 contract keeps preference boundaries closed', () {
    final contract =
        jsonDecode(
              File(
                '../../docs/contracts/app-preferences-reliability-slice30.v1.json',
              ).readAsStringSync(),
            )
            as Map<String, dynamic>;

    expect(contract['contract'], 'app-preferences-reliability-slice30');
    expect(contract['scope']['store_interface_change'], isFalse);
    expect(contract['scope']['persistence_key_change'], isFalse);
    expect(contract['scope']['serialization_change'], isFalse);
    expect(contract['states']['loading']['key'], 'settings-loading');
    expect(contract['states']['saving']['key'], 'settings-saving');
    expect(contract['states']['error']['retry_key'], 'settings-retry');
    expect(
      contract['resolution']['write_failure_rolls_back_last_persisted_state'],
      isTrue,
    );
  });

  test('preferences source has guarded explicit persistence states', () {
    final source = File(
      'lib/core/preferences/app_preferences.dart',
    ).readAsStringSync();
    final settingsSource = File(
      'lib/features/settings/presentation/settings_screen.dart',
    ).readAsStringSync();

    for (final token in [
      'AppPreferencesStatus',
      'AppPreferencesFailure',
      '_loadInFlight',
      '_writeInFlight',
      'Future<void> retry()',
      'on Object',
    ]) {
      expect(source, contains(token));
    }
    for (final token in [
      "ValueKey('settings-loading')",
      "ValueKey('settings-error')",
      "ValueKey('settings-retry')",
      "ValueKey('settings-saving')",
      'Future<void>.microtask',
      'IgnorePointer',
    ]) {
      expect(settingsSource, contains(token));
    }
    expect(settingsSource, isNot(contains('CircularProgressIndicator')));
    expect(settingsSource, isNot(contains('LinearProgressIndicator')));
  });

  test('read failure is caught and retry recovers persisted values', () async {
    final store = _ControllablePreferencesStore(
      value: const AppPreferencesState(
        locale: AppLocalePreference.en,
        theme: AppThemePreference.dark,
        loaded: true,
      ),
    )..readFailuresRemaining = 1;
    final container = ProviderContainer(
      overrides: [appPreferencesStoreProvider.overrideWithValue(store)],
    );
    addTearDown(container.dispose);

    final controller = container.read(
      appPreferencesControllerProvider.notifier,
    );
    await controller.load();

    var state = container.read(appPreferencesControllerProvider);
    expect(state.status, AppPreferencesStatus.error);
    expect(state.failure, AppPreferencesFailure.read);
    expect(state.loaded, isFalse);

    await controller.retry();
    state = container.read(appPreferencesControllerProvider);
    expect(state.status, AppPreferencesStatus.ready);
    expect(state.locale, AppLocalePreference.en);
    expect(state.theme, AppThemePreference.dark);
    expect(store.reads, 2);
  });

  test('locale and theme write failures roll back persisted values', () async {
    final store = _ControllablePreferencesStore(
      value: const AppPreferencesState(
        locale: AppLocalePreference.en,
        theme: AppThemePreference.dark,
        loaded: true,
      ),
    );
    final container = ProviderContainer(
      overrides: [appPreferencesStoreProvider.overrideWithValue(store)],
    );
    addTearDown(container.dispose);
    final controller = container.read(
      appPreferencesControllerProvider.notifier,
    );

    await controller.load();
    store.localeWriteFailuresRemaining = 1;
    await controller.setLocale(AppLocalePreference.tr);

    var state = container.read(appPreferencesControllerProvider);
    expect(state.locale, AppLocalePreference.en);
    expect(state.theme, AppThemePreference.dark);
    expect(state.status, AppPreferencesStatus.error);
    expect(state.failure, AppPreferencesFailure.write);

    store.themeWriteFailuresRemaining = 1;
    await controller.setTheme(AppThemePreference.light);

    state = container.read(appPreferencesControllerProvider);
    expect(state.locale, AppLocalePreference.en);
    expect(state.theme, AppThemePreference.dark);
    expect(state.status, AppPreferencesStatus.error);
    expect(state.failure, AppPreferencesFailure.write);
  });

  test('duplicate loads and writes are ignored while in flight', () async {
    final store = _ControllablePreferencesStore(
      value: const AppPreferencesState(loaded: true),
    )..readGate = Completer<AppPreferencesState>();
    final container = ProviderContainer(
      overrides: [appPreferencesStoreProvider.overrideWithValue(store)],
    );
    addTearDown(container.dispose);
    final controller = container.read(
      appPreferencesControllerProvider.notifier,
    );

    final firstLoad = controller.load();
    await controller.load();
    expect(store.reads, 1);
    store.readGate!.complete(store.value);
    await firstLoad;

    store.localeWriteGate = Completer<void>();
    final firstWrite = controller.setLocale(AppLocalePreference.tr);
    await controller.setTheme(AppThemePreference.dark);
    expect(store.localeWrites, 1);
    expect(store.themeWrites, 0);
    store.localeWriteGate!.complete();
    await firstWrite;
  });

  testWidgets('read failure keeps fallback groups disabled until retry', (
    tester,
  ) async {
    final store = _ControllablePreferencesStore(
      value: const AppPreferencesState(
        locale: AppLocalePreference.en,
        theme: AppThemePreference.light,
        loaded: true,
      ),
    )..readFailuresRemaining = 1;

    await _pump(tester, store: store, locale: const Locale('en', 'US'));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('settings-error')), findsOneWidget);
    expect(find.byKey(const ValueKey('settings-retry')), findsOneWidget);
    expect(
      find.byKey(const ValueKey('settings-language-group')),
      findsOneWidget,
    );
    expect(
      find.byKey(const ValueKey('settings-appearance-group')),
      findsOneWidget,
    );

    await tester.tap(find.text('Dark'));
    await tester.pump();
    expect(store.themeWrites, 0);

    await tester.tap(find.byKey(const ValueKey('settings-retry')));
    await tester.pumpAndSettle();

    expect(store.reads, 2);
    expect(find.byKey(const ValueKey('settings-error')), findsNothing);
    await tester.tap(find.text('Dark'));
    await tester.pumpAndSettle();
    expect(store.themeWrites, 1);
    expect(tester.takeException(), isNull);
  });

  testWidgets('saving is disclosed and choices remain single-flight', (
    tester,
  ) async {
    final store = _ControllablePreferencesStore(
      value: const AppPreferencesState(loaded: true),
    );

    await _pump(tester, store: store);
    await tester.pumpAndSettle();
    store.localeWriteGate = Completer<void>();

    await tester.tap(find.text('Türkçe'));
    await tester.pump();

    expect(find.byKey(const ValueKey('settings-saving')), findsOneWidget);
    expect(store.localeWrites, 1);

    await tester.tap(find.text('Koyu'));
    await tester.pump();
    expect(store.themeWrites, 0);

    store.localeWriteGate!.complete();
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('settings-saving')), findsNothing);
    expect(tester.takeException(), isNull);
  });

  for (final themeMode in [ThemeMode.light, ThemeMode.dark]) {
    for (final locale in const [Locale('tr', 'TR'), Locale('en', 'US')]) {
      testWidgets(
        'error state is compact-safe in ${themeMode.name} ${locale.languageCode}',
        (tester) async {
          tester.view.physicalSize = const Size(360, 800);
          tester.view.devicePixelRatio = 1;
          addTearDown(tester.view.resetPhysicalSize);
          addTearDown(tester.view.resetDevicePixelRatio);

          final store = _ControllablePreferencesStore(
            value: const AppPreferencesState(loaded: true),
          )..readFailuresRemaining = 1;
          await _pump(
            tester,
            store: store,
            locale: locale,
            themeMode: themeMode,
            textScale: 1.6,
          );
          await tester.pumpAndSettle();

          expect(find.byKey(const ValueKey('settings-error')), findsOneWidget);
          expect(find.byKey(const ValueKey('settings-retry')), findsOneWidget);
          expect(
            find.byKey(const ValueKey('settings-language-group')),
            findsOneWidget,
          );
          expect(tester.takeException(), isNull);
        },
      );
    }
  }
}

Future<void> _pump(
  WidgetTester tester, {
  required _ControllablePreferencesStore store,
  Locale locale = const Locale('tr', 'TR'),
  ThemeMode themeMode = ThemeMode.light,
  double textScale = 1,
}) async {
  tester.platformDispatcher.localeTestValue = locale;
  addTearDown(tester.platformDispatcher.clearLocaleTestValue);

  await tester.pumpWidget(
    ProviderScope(
      key: UniqueKey(),
      overrides: [appPreferencesStoreProvider.overrideWithValue(store)],
      child: MaterialApp(
        debugShowCheckedModeBanner: false,
        locale: locale,
        supportedLocales: KefeStrings.supportedLocales,
        localizationsDelegates: const [
          KefeStringsDelegate(),
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        theme: KefeTheme.light(),
        darkTheme: KefeTheme.dark(),
        themeMode: themeMode,
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(
            context,
          ).copyWith(textScaler: TextScaler.linear(textScale)),
          child: child!,
        ),
        home: const SettingsScreen(showPrivacyControls: false),
      ),
    ),
  );
}

class _ControllablePreferencesStore implements AppPreferencesStore {
  _ControllablePreferencesStore({required this.value});

  AppPreferencesState value;
  Completer<AppPreferencesState>? readGate;
  Completer<void>? localeWriteGate;
  Completer<void>? themeWriteGate;
  int readFailuresRemaining = 0;
  int localeWriteFailuresRemaining = 0;
  int themeWriteFailuresRemaining = 0;
  int reads = 0;
  int localeWrites = 0;
  int themeWrites = 0;

  @override
  Future<AppPreferencesState> read() async {
    reads += 1;
    final gate = readGate;
    if (gate != null && !gate.isCompleted) return gate.future;
    if (readFailuresRemaining > 0) {
      readFailuresRemaining -= 1;
      throw StateError('preferences read unavailable');
    }
    return value;
  }

  @override
  Future<void> writeLocale(AppLocalePreference locale) async {
    localeWrites += 1;
    final gate = localeWriteGate;
    if (gate != null && !gate.isCompleted) await gate.future;
    if (localeWriteFailuresRemaining > 0) {
      localeWriteFailuresRemaining -= 1;
      throw StateError('locale write unavailable');
    }
    value = value.copyWith(locale: locale, loaded: true, clearFailure: true);
  }

  @override
  Future<void> writeTheme(AppThemePreference theme) async {
    themeWrites += 1;
    final gate = themeWriteGate;
    if (gate != null && !gate.isCompleted) await gate.future;
    if (themeWriteFailuresRemaining > 0) {
      themeWriteFailuresRemaining -= 1;
      throw StateError('theme write unavailable');
    }
    value = value.copyWith(theme: theme, loaded: true, clearFailure: true);
  }
}
