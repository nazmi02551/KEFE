import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/onboarding/application/onboarding_controller.dart';
import 'package:kefe_mobile/features/onboarding/data/onboarding_store.dart';
import 'package:kefe_mobile/features/onboarding/presentation/onboarding_gate_screen.dart';

void main() {
  test('Slice 29 contract keeps onboarding boundaries closed', () {
    final contract =
        jsonDecode(
              File(
                '../../docs/contracts/onboarding-gate-reliability-slice29.v1.json',
              ).readAsStringSync(),
            )
            as Map<String, dynamic>;

    expect(contract['contract'], 'onboarding-gate-reliability-slice29');
    expect(contract['scope']['controller_change'], isFalse);
    expect(contract['scope']['store_change'], isFalse);
    expect(contract['scope']['completion_semantics_change'], isFalse);
    expect(contract['states']['resolving']['key'], 'onboarding-loading');
    expect(
      contract['states']['error_retryable']['retry_key'],
      'onboarding-retry',
    );
    expect(contract['resolution']['duplicate_guard'], isTrue);
    expect(contract['resolution']['review_mode_reads_persistence'], isFalse);
    expect(contract['preserved']['product_preview_isolation'], isTrue);
  });

  test('onboarding source has explicit guarded resolution states', () {
    final source = File(
      'lib/features/onboarding/presentation/onboarding_gate_screen.dart',
    ).readAsStringSync();

    for (final token in [
      '_OnboardingResolutionState',
      '_resolutionInFlight',
      "'onboarding-error'",
      "'onboarding-loading'",
      "ValueKey('onboarding-retry')",
      'on Object',
      "context.go('/explore')",
    ]) {
      expect(source, contains(token));
    }
    expect(source, isNot(contains('CircularProgressIndicator')));
    expect(source, isNot(contains('LinearProgressIndicator')));
  });

  testWidgets('first lookup renders deterministic loading', (tester) async {
    final store = _ControllableOnboardingStore()
      ..gate = Completer<bool>();

    await _pump(tester, store: store);
    await tester.pump();
    await tester.pump();

    expect(find.byKey(const ValueKey('onboarding-loading')), findsOneWidget);
    expect(find.byKey(const ValueKey('onboarding-error')), findsNothing);
    expect(store.reads, 1);
    expect(tester.takeException(), isNull);
  });

  testWidgets('failure is retryable and does not bypass onboarding', (
    tester,
  ) async {
    final store = _ControllableOnboardingStore()..failuresRemaining = 1;

    await _pump(tester, store: store, locale: const Locale('en', 'US'));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('onboarding-error')), findsOneWidget);
    expect(find.byKey(const ValueKey('onboarding-retry')), findsOneWidget);
    expect(find.byKey(const ValueKey('onboarding-pages')), findsNothing);

    await tester.tap(find.byKey(const ValueKey('onboarding-retry')));
    await tester.pumpAndSettle();

    expect(store.reads, 2);
    expect(find.byKey(const ValueKey('onboarding-error')), findsNothing);
    expect(find.byKey(const ValueKey('onboarding-pages')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('duplicate resolution attempts are ignored while in flight', (
    tester,
  ) async {
    final store = _ControllableOnboardingStore()
      ..gate = Completer<bool>();

    await _pump(tester, store: store);
    await tester.pump();
    await tester.pump();

    expect(store.reads, 1);
    expect(find.byKey(const ValueKey('onboarding-loading')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('review mode exposes pages without persistence access', (
    tester,
  ) async {
    final store = _ControllableOnboardingStore()..failuresRemaining = 10;

    await _pump(tester, store: store, reviewMode: true);
    await tester.pumpAndSettle();

    expect(store.reads, 0);
    expect(find.byKey(const ValueKey('onboarding-pages')), findsOneWidget);
    expect(find.byKey(const ValueKey('onboarding-error')), findsNothing);
    expect(tester.takeException(), isNull);
  });

  for (final themeMode in [ThemeMode.light, ThemeMode.dark]) {
    testWidgets(
      'error surface is compact-safe in ${themeMode.name} theme',
      (tester) async {
        tester.view.physicalSize = const Size(360, 800);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);

        final store = _ControllableOnboardingStore()..failuresRemaining = 1;
        await _pump(
          tester,
          store: store,
          themeMode: themeMode,
          textScale: 1.6,
        );
        await tester.pumpAndSettle();

        expect(find.byKey(const ValueKey('onboarding-error')), findsOneWidget);
        expect(find.byKey(const ValueKey('onboarding-retry')), findsOneWidget);
        expect(tester.takeException(), isNull);
      },
    );
  }
}

Future<void> _pump(
  WidgetTester tester, {
  required _ControllableOnboardingStore store,
  Locale locale = const Locale('tr', 'TR'),
  ThemeMode themeMode = ThemeMode.light,
  double textScale = 1,
  bool reviewMode = false,
}) async {
  tester.platformDispatcher.localeTestValue = locale;
  addTearDown(tester.platformDispatcher.clearLocaleTestValue);

  await tester.pumpWidget(
    ProviderScope(
      key: UniqueKey(),
      overrides: [onboardingStoreProvider.overrideWithValue(store)],
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
        home: OnboardingGateScreen(reviewMode: reviewMode),
      ),
    ),
  );
}

class _ControllableOnboardingStore implements OnboardingStore {
  Completer<bool>? gate;
  int failuresRemaining = 0;
  int reads = 0;
  bool completed = false;

  @override
  Future<bool> isCompleted() async {
    reads += 1;
    final activeGate = gate;
    if (activeGate != null && !activeGate.isCompleted) {
      return activeGate.future;
    }
    if (failuresRemaining > 0) {
      failuresRemaining -= 1;
      throw StateError('onboarding persistence unavailable');
    }
    return completed;
  }

  @override
  Future<void> markCompleted() async {
    completed = true;
  }
}
