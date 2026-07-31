import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_surface.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/onboarding/application/onboarding_controller.dart';
import 'package:kefe_mobile/features/onboarding/data/onboarding_store.dart';
import 'package:kefe_mobile/features/onboarding/presentation/onboarding_gate_screen.dart';

void main() {
  test('slice 16 v2 contract locks first-use and preview boundaries', () {
    final contractFile = File(
      '../../docs/contracts/premium-first-use-slice16.v2.json',
    );
    expect(contractFile.existsSync(), isTrue);

    final contract =
        jsonDecode(contractFile.readAsStringSync()) as Map<String, Object?>;
    final scope = contract['scope']! as Map<String, Object?>;
    final onboarding = contract['onboarding']! as Map<String, Object?>;
    final preview = contract['preview']! as Map<String, Object?>;
    final continuation = contract['continuation']! as Map<String, Object?>;
    final presentation = contract['presentation']! as Map<String, Object?>;
    final invariants = contract['invariants']! as Map<String, Object?>;

    expect(contract['version'], 2);
    expect(scope['onboarding_visual_convergence'], isTrue);
    expect(scope['first_reveal_completion_visual_convergence'], isTrue);
    expect(scope['preview_review_path'], isTrue);
    expect(scope['new_onboarding_step'], isFalse);
    expect(scope['copy_change'], isFalse);
    expect(scope['case_selection_change'], isFalse);
    expect(scope['backend_change'], isFalse);
    expect(scope['production_route_change'], isFalse);
    expect(scope['preview_route_change'], isTrue);
    expect(onboarding['promise_count'], 2);
    expect(onboarding['first_case_fetch_before_promises'], isFalse);
    expect(
      onboarding['completion_persisted_after_first_reveal_in_production'],
      isTrue,
    );
    expect(onboarding['review_mode_bypasses_only_completion_gate'], isTrue);
    expect(preview['initial_location_preserved'], '/explore');
    expect(preview['review_route'], '/welcome?review=1');
    expect(preview['review_action_key'], 'open-preview-first-use');
    expect(preview['review_store'], 'memory');
    expect(preview['production_persistence_mutated'], isFalse);
    expect(preview['first_reveal_completion_reachable'], isTrue);
    expect(continuation['continue_as_guest_preserved'], isTrue);
    expect(continuation['continue_destination'], '/explore');
    expect(continuation['account_required'], isFalse);
    expect(presentation['semantic_kefe_surfaces_required'], isTrue);
    expect(presentation['theme_adaptive_required'], isTrue);
    expect(presentation['reduce_motion_aware'], isTrue);
    expect(presentation['continuous_loading_animation_added'], isFalse);
    expect(invariants['commit_first'], isTrue);
    expect(invariants['blind_first'], isTrue);
    expect(invariants['immutable_case_version'], isTrue);
    expect(invariants['generic_runtime'], isTrue);
    expect(invariants['preview_production_isolation'], isTrue);
    expect(invariants['signal_in_scope'], isFalse);
    expect(invariants['impact_in_scope'], isFalse);
  });

  for (final locale in const [Locale('tr', 'TR'), Locale('en', 'US')]) {
    for (final dark in const [false, true]) {
      testWidgets(
        'onboarding is premium in ${locale.languageCode} ${dark ? 'dark' : 'light'}',
        (tester) async {
          await _pumpOnboarding(tester, locale: locale, dark: dark);

          expect(
            find.byKey(const ValueKey('onboarding-pages')),
            findsOneWidget,
          );
          expect(
            find.byKey(const ValueKey('onboarding-promise-1')),
            findsOneWidget,
          );
          expect(
            find.byKey(const ValueKey('onboarding-primary-button')),
            findsOneWidget,
          );
          expect(find.byType(KefeSurface), findsWidgets);
          expect(find.byType(CircularProgressIndicator), findsNothing);
          expect(
            Theme.of(
              tester.element(
                find.byKey(const ValueKey('onboarding-promise-1')),
              ),
            ).brightness,
            dark ? Brightness.dark : Brightness.light,
          );

          await tester.tap(
            find.byKey(const ValueKey('onboarding-primary-button')),
          );
          await tester.pumpAndSettle();

          expect(
            find.byKey(const ValueKey('onboarding-promise-2')),
            findsOneWidget,
          );
          expect(tester.takeException(), isNull);
        },
      );
    }
  }

  testWidgets('review mode bypasses only the persisted completion gate', (
    tester,
  ) async {
    final store = _TrackingOnboardingStore(completed: true);
    tester.platformDispatcher.localeTestValue = const Locale('tr', 'TR');
    addTearDown(tester.platformDispatcher.clearLocaleTestValue);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [onboardingStoreProvider.overrideWithValue(store)],
        child: MaterialApp(
          locale: const Locale('tr', 'TR'),
          supportedLocales: KefeStrings.supportedLocales,
          localizationsDelegates: const [
            KefeStringsDelegate(),
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          theme: KefeTheme.light(),
          home: const OnboardingGateScreen(reviewMode: true),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(store.readCount, 0);
    expect(store.markCount, 0);
    expect(find.byKey(const ValueKey('onboarding-pages')), findsOneWidget);
    expect(find.byKey(const ValueKey('onboarding-promise-1')), findsOneWidget);
  });

  test('governed first-use presentation uses semantic KEFE primitives', () {
    final onboardingSource = File(
      'lib/features/onboarding/presentation/onboarding_gate_screen.dart',
    ).readAsStringSync();
    final decisionSource = File(
      'lib/features/decision/presentation/decision_flow_screen.dart',
    ).readAsStringSync();
    final previewAppSource = File(
      'lib/app/product_preview_app.dart',
    ).readAsStringSync();
    final previewMainSource = File('lib/main_preview.dart').readAsStringSync();
    final productionAppSource = File(
      'lib/app/kefe_app.dart',
    ).readAsStringSync();
    final productionMainSource = File('lib/main.dart').readAsStringSync();
    final completionSource = decisionSource
        .split('class _FirstUseCompletionCard')[1]
        .split('class _ErrorState')[0];

    expect(onboardingSource, contains('KefeSurface('));
    expect(onboardingSource, contains('KefeSurfaceTone.premium'));
    expect(onboardingSource, contains('KefeMotion.resolve('));
    expect(onboardingSource, contains('this.reviewMode = false'));
    expect(onboardingSource, isNot(contains('CircularProgressIndicator')));
    expect(onboardingSource, contains("ValueKey('onboarding-pages')"));
    expect(onboardingSource, contains("ValueKey('onboarding-promise-1')"));
    expect(onboardingSource, contains("ValueKey('onboarding-promise-2')"));
    expect(onboardingSource, contains("ValueKey('onboarding-primary-button')"));

    expect(completionSource, contains('KefeSurface('));
    expect(completionSource, contains('KefeSurfaceTone.premium'));
    expect(completionSource, contains("ValueKey('first-use-completion')"));
    expect(completionSource, contains("ValueKey('continue-as-guest')"));

    expect(previewAppSource, contains("path: '/welcome'"));
    expect(previewAppSource, contains("queryParameters['review'] == '1'"));
    expect(previewAppSource, contains("ValueKey('open-preview-first-use')"));
    expect(
      previewAppSource,
      contains("firstUse: state.uri.queryParameters['firstUse'] == '1'"),
    );
    expect(
      previewMainSource,
      contains('onboardingStoreProvider.overrideWithValue'),
    );
    expect(previewMainSource, contains('MemoryOnboardingStore()'));
    expect(productionAppSource, contains('const OnboardingGateScreen()'));
    expect(productionMainSource, isNot(contains('MemoryOnboardingStore')));
  });
}

Future<void> _pumpOnboarding(
  WidgetTester tester, {
  required Locale locale,
  required bool dark,
}) async {
  tester.platformDispatcher.localeTestValue = locale;
  addTearDown(tester.platformDispatcher.clearLocaleTestValue);

  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        onboardingStoreProvider.overrideWithValue(MemoryOnboardingStore()),
      ],
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
        home: const OnboardingGateScreen(),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

class _TrackingOnboardingStore implements OnboardingStore {
  _TrackingOnboardingStore({required this.completed});

  bool completed;
  int readCount = 0;
  int markCount = 0;

  @override
  Future<bool> isCompleted() async {
    readCount += 1;
    return completed;
  }

  @override
  Future<void> markCompleted() async {
    markCount += 1;
    completed = true;
  }
}
