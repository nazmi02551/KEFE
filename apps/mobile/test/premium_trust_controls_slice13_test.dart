import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:kefe_mobile/core/design/kefe_surface.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/core/preferences/app_preferences.dart';
import 'package:kefe_mobile/features/account/presentation/account_conversion_screen.dart';
import 'package:kefe_mobile/features/privacy/application/privacy_controller.dart';
import 'package:kefe_mobile/features/privacy/presentation/privacy_controls_section.dart';
import 'package:kefe_mobile/features/settings/presentation/settings_screen.dart';

Future<void> _revealSettingsEntry(WidgetTester tester, Finder entry) async {
  await tester.scrollUntilVisible(
    entry,
    240,
    scrollable: find.descendant(
      of: find.byKey(const ValueKey('settings-screen')),
      matching: find.byType(Scrollable),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  test('slice 13 contract preserves trust/control product boundaries', () {
    final contractFile = File(
      '../../docs/contracts/premium-trust-controls-slice13.v1.json',
    );
    expect(contractFile.existsSync(), isTrue);

    final contract =
        jsonDecode(contractFile.readAsStringSync()) as Map<String, Object?>;
    final scope = contract['scope']! as Map<String, Object?>;
    final settings = contract['settings']! as Map<String, Object?>;
    final privacy = contract['privacy']! as Map<String, Object?>;
    final account = contract['account']! as Map<String, Object?>;
    final presentation = contract['presentation']! as Map<String, Object?>;
    final invariants = contract['invariants']! as Map<String, Object?>;

    expect(scope['settings_visual_convergence'], isTrue);
    expect(scope['privacy_visual_convergence'], isTrue);
    expect(scope['account_visual_convergence'], isTrue);
    expect(scope['public_share_visual_convergence'], isFalse);
    expect(scope['authentication_backend_change'], isFalse);
    expect(scope['otp_provider_change'], isFalse);
    expect(settings['locale_values'], ['SYSTEM', 'TR', 'EN']);
    expect(settings['theme_values'], ['SYSTEM', 'LIGHT', 'DARK']);
    expect(settings['new_locale_enabled'], isFalse);
    expect(privacy['feature_gate_preserved'], isTrue);
    expect(privacy['disabled_state_not_activated'], isTrue);
    expect(privacy['delete_confirmation_token'], 'DELETE');
    expect(privacy['successful_delete_route'], '/welcome');
    expect(account['optional'], isTrue);
    expect(account['channels'], ['EMAIL', 'SMS']);
    expect(account['production_otp_claim'], isFalse);
    expect(presentation['semantic_kefe_surfaces_required'], isTrue);
    expect(presentation['direct_dark_only_tokens_forbidden'], isTrue);
    expect(invariants['commit_first'], isTrue);
    expect(invariants['blind_first'], isTrue);
    expect(invariants['my_kefe_observed_descriptive_only'], isTrue);
    expect(invariants['personality_inference'], isFalse);
    expect(invariants['causal_inference'], isFalse);
    expect(invariants['signal_in_scope'], isFalse);
    expect(invariants['impact_in_scope'], isFalse);
  });

  for (final locale in const [Locale('tr', 'TR'), Locale('en', 'US')]) {
    for (final dark in const [false, true]) {
      testWidgets(
        'settings uses semantic grouped controls in ${locale.languageCode} ${dark ? 'dark' : 'light'}',
        (tester) async {
          final expectedVisual = dark
              ? KefeVisualTheme.dark
              : KefeVisualTheme.light;
          final expectedTitle = locale.languageCode == 'tr'
              ? 'Ayarlar'
              : 'Settings';
          final expectedLanguage = locale.languageCode == 'tr'
              ? 'Dil'
              : 'Language';
          final expectedAppearance = locale.languageCode == 'tr'
              ? 'Görünüm'
              : 'Appearance';

          await _pumpLocalized(
            tester,
            locale: locale,
            dark: dark,
            child: const SettingsScreen(),
          );

          expect(find.text(expectedTitle), findsOneWidget);
          expect(find.text(expectedLanguage), findsOneWidget);
          expect(find.text(expectedAppearance), findsOneWidget);
          expect(
            find.byKey(const ValueKey('settings-language-group')),
            findsOneWidget,
          );
          expect(
            find.byKey(const ValueKey('settings-appearance-group')),
            findsOneWidget,
          );
          expect(
            find.byType(RadioListTile<AppLocalePreference>),
            findsNWidgets(3),
          );
          expect(
            find.byType(RadioListTile<AppThemePreference>),
            findsNWidgets(3),
          );

          final privacyEntry = find.byKey(
            const ValueKey('settings-privacy-entry'),
          );
          await _revealSettingsEntry(tester, privacyEntry);
          expect(privacyEntry, findsOneWidget);

          final appBar = tester.widget<AppBar>(find.byType(AppBar));
          expect(appBar.backgroundColor, expectedVisual.surfaceRaised);
          expect(appBar.foregroundColor, expectedVisual.foreground);
          expect(tester.takeException(), isNull);
        },
      );
    }
  }

  testWidgets(
    'settings keeps preference controller and privacy route semantics',
    (tester) async {
      final container = ProviderContainer(
        overrides: [
          appPreferencesStoreProvider.overrideWithValue(
            MemoryAppPreferencesStore(),
          ),
        ],
      );
      addTearDown(container.dispose);

      final router = GoRouter(
        initialLocation: '/settings',
        routes: [
          GoRoute(path: '/settings', builder: (_, _) => const SettingsScreen()),
          GoRoute(
            path: '/privacy',
            builder: (_, _) =>
                const Scaffold(body: Text('privacy-route-sentinel')),
          ),
        ],
      );
      addTearDown(router.dispose);

      await tester.pumpWidget(
        UncontrolledProviderScope(
          container: container,
          child: MaterialApp.router(
            locale: const Locale('en', 'US'),
            supportedLocales: KefeStrings.supportedLocales,
            localizationsDelegates: const [
              KefeStringsDelegate(),
              GlobalMaterialLocalizations.delegate,
              GlobalWidgetsLocalizations.delegate,
              GlobalCupertinoLocalizations.delegate,
            ],
            theme: KefeTheme.light(),
            routerConfig: router,
          ),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.text('Dark'));
      await tester.pump();
      expect(
        container.read(appPreferencesControllerProvider).theme,
        AppThemePreference.dark,
      );

      await tester.tap(find.text('English'));
      await tester.pump();
      expect(
        container.read(appPreferencesControllerProvider).locale,
        AppLocalePreference.en,
      );

      final privacyEntry = find.byKey(const ValueKey('settings-privacy-entry'));
      await _revealSettingsEntry(tester, privacyEntry);
      await tester.tap(privacyEntry);
      await tester.pumpAndSettle();
      expect(find.text('privacy-route-sentinel'), findsOneWidget);
    },
  );

  testWidgets('privacy gate stays hidden by default', (tester) async {
    await _pumpLocalized(
      tester,
      locale: const Locale('en', 'US'),
      dark: false,
      child: const PrivacyControlsSection(),
    );

    expect(find.byKey(const ValueKey('privacy-controls')), findsNothing);
    expect(find.byKey(const ValueKey('privacy-export')), findsNothing);
    expect(find.byKey(const ValueKey('privacy-delete')), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('privacy controls render when gate is explicitly enabled', (
    tester,
  ) async {
    await _pumpLocalized(
      tester,
      locale: const Locale('en', 'US'),
      dark: true,
      privacyEnabled: true,
      child: const PrivacyControlsSection(),
    );

    expect(find.byKey(const ValueKey('privacy-controls')), findsOneWidget);
    expect(find.byKey(const ValueKey('privacy-export')), findsOneWidget);
    expect(find.byKey(const ValueKey('privacy-delete')), findsOneWidget);
    expect(
      tester
          .widget<KefeSurface>(find.byKey(const ValueKey('privacy-controls')))
          .tone,
      KefeSurfaceTone.raised,
    );
    expect(tester.takeException(), isNull);
  });

  for (final locale in const [Locale('tr', 'TR'), Locale('en', 'US')]) {
    for (final dark in const [false, true]) {
      testWidgets(
        'optional account entry preserves interactive keys in ${locale.languageCode} ${dark ? 'dark' : 'light'}',
        (tester) async {
          await _pumpLocalized(
            tester,
            locale: locale,
            dark: dark,
            child: const AccountConversionScreen(),
          );

          expect(
            find.byKey(const ValueKey('account-conversion-screen')),
            findsOneWidget,
          );
          expect(
            find.byKey(const ValueKey('account-intro-surface')),
            findsOneWidget,
          );
          expect(
            find.byKey(const ValueKey('account-identifier-surface')),
            findsOneWidget,
          );
          expect(
            find.byKey(const ValueKey('account-identifier')),
            findsOneWidget,
          );
          expect(
            find.byKey(const ValueKey('account-request-otp')),
            findsOneWidget,
          );
          expect(
            find.byKey(const ValueKey('account-continue-guest')),
            findsOneWidget,
          );
          expect(find.byType(SegmentedButton<String>), findsOneWidget);
          expect(tester.takeException(), isNull);
        },
      );
    }
  }

  test('governed trust/control presentation rejects dark-only token debt', () {
    final paths = [
      'lib/features/settings/presentation/settings_screen.dart',
      'lib/features/privacy/presentation/privacy_screen.dart',
      'lib/features/privacy/presentation/privacy_controls_section.dart',
      'lib/features/account/presentation/account_conversion_screen.dart',
    ];

    for (final path in paths) {
      final source = File(path).readAsStringSync();
      expect(source, contains('kefeVisual'));
      expect(source, isNot(contains('KefeColorTokens.surfaceDark')));
      expect(source, isNot(contains('KefeColorTokens.borderDark')));
      expect(source, isNot(contains('KefeColorTokens.textMutedDark')));
    }

    final privacySource = File(
      'lib/features/privacy/presentation/privacy_controls_section.dart',
    ).readAsStringSync();
    expect(privacySource, contains("ValueKey('privacy-export')"));
    expect(privacySource, contains("ValueKey('privacy-delete')"));
    expect(privacySource, contains("ValueKey('privacy-delete-confirmation')"));
    expect(privacySource, contains("typed.text.trim() == 'DELETE'"));
    expect(privacySource, contains("context.go('/welcome')"));

    final accountSource = File(
      'lib/features/account/presentation/account_conversion_screen.dart',
    ).readAsStringSync();
    for (final key in const [
      'account-identifier',
      'account-request-otp',
      'account-otp-code',
      'account-verify-merge',
      'account-error',
      'account-continue-guest',
    ]) {
      expect(accountSource, contains("ValueKey('$key')"));
    }
    expect(accountSource, contains("value: 'EMAIL'"));
    expect(accountSource, contains("value: 'SMS'"));
  });
}

Future<void> _pumpLocalized(
  WidgetTester tester, {
  required Locale locale,
  required bool dark,
  required Widget child,
  bool privacyEnabled = false,
}) async {
  tester.platformDispatcher.localeTestValue = locale;
  addTearDown(tester.platformDispatcher.clearLocaleTestValue);

  await tester.pumpWidget(
    ProviderScope(
      overrides: privacyEnabled
          ? [privacyExperienceEnabledProvider.overrideWithValue(true)]
          : const [],
      child: MaterialApp(
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
        themeMode: dark ? ThemeMode.dark : ThemeMode.light,
        home: child,
      ),
    ),
  );
  await tester.pumpAndSettle();
}
