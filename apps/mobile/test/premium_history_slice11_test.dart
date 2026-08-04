import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/product_preview/preview_content_localizer.dart';
import 'package:kefe_mobile/core/design/kefe_surface.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/localization/kefe_content_localizer.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/activity/presentation/activity_screen.dart';
import 'package:kefe_mobile/features/progress/application/progress_controller.dart';
import 'package:kefe_mobile/features/progress/data/preview_progress_repository.dart';
import 'package:kefe_mobile/features/progress/presentation/my_kefe_journey_screen.dart';
import 'package:kefe_mobile/features/saved_cases/application/saved_cases_controller.dart';
import 'package:kefe_mobile/features/saved_cases/data/saved_case_store.dart';

void main() {
  test('slice 11 contract keeps descriptive history boundaries closed', () {
    final contractFile = File(
      '../../docs/contracts/premium-history-slice11.v1.json',
    );
    expect(contractFile.existsSync(), isTrue);

    final contract =
        jsonDecode(contractFile.readAsStringSync()) as Map<String, Object?>;
    final scope = contract['scope']! as Map<String, Object?>;
    final presentation = contract['presentation']! as Map<String, Object?>;
    final myKefe = contract['my_kefe']! as Map<String, Object?>;
    final invariants = contract['invariants']! as Map<String, Object?>;

    expect(scope['activity_visual_convergence'], isTrue);
    expect(scope['my_kefe_visual_convergence'], isTrue);
    expect(scope['progress_visual_convergence'], isTrue);
    expect(scope['backend_model_change'], isFalse);
    expect(scope['new_history_metric'], isFalse);
    expect(presentation['semantic_kefe_surfaces_required'], isTrue);
    expect(presentation['light_dark_parity_required'], isTrue);
    expect(presentation['preview_truthfulness_notice_preserved'], isTrue);
    expect(presentation['non_inference_note_preserved'], isTrue);
    expect(myKefe['observed_descriptive_only'], isTrue);
    expect(myKefe['personality_inference'], isFalse);
    expect(myKefe['ideology_inference'], isFalse);
    expect(myKefe['psychometric_inference'], isFalse);
    expect(myKefe['bias_inference'], isFalse);
    expect(myKefe['causal_inference'], isFalse);
    expect(myKefe['normative_scoring'], isFalse);
    expect(invariants['commit_first'], isTrue);
    expect(invariants['blind_first'], isTrue);
    expect(invariants['signal_in_scope'], isFalse);
    expect(invariants['impact_in_scope'], isFalse);
  });

  for (final locale in const [Locale('tr', 'TR'), Locale('en', 'US')]) {
    for (final dark in const [false, true]) {
      testWidgets(
        'Activity renders semantic history in ${locale.languageCode} ${dark ? 'dark' : 'light'}',
        (tester) async {
          await _pumpHistorySurface(
            tester,
            locale: locale,
            dark: dark,
            child: const ActivityScreen(embedded: true),
          );

          expect(find.byKey(const ValueKey('activity-screen')), findsOneWidget);
          expect(
            find.byKey(const ValueKey('activity-preview-notice')),
            findsOneWidget,
          );
          expect(
            find.byKey(const ValueKey('saved-cases-section')),
            findsOneWidget,
          );
          expect(find.byType(KefeSurface), findsWidgets);
          expect(tester.takeException(), isNull);
        },
      );

      testWidgets(
        'My KEFE renders descriptive journey in ${locale.languageCode} ${dark ? 'dark' : 'light'}',
        (tester) async {
          await _pumpHistorySurface(
            tester,
            locale: locale,
            dark: dark,
            child: const MyKefeJourneyScreen(embedded: true),
          );

          expect(find.byKey(const ValueKey('my-kefe-journey')), findsOneWidget);
          expect(
            find.byKey(const ValueKey('my-kefe-preview-notice')),
            findsOneWidget,
          );
          expect(
            find.byKey(const ValueKey('saved-cases-section')),
            findsNothing,
          );
          expect(find.byType(KefeSurface), findsWidgets);

          final recentJourneys = find.byKey(
            const ValueKey('my-kefe-recent-journeys'),
          );
          await tester.ensureVisible(recentJourneys);
          final firstJourney = find.descendant(
            of: recentJourneys,
            matching: find.byType(ExpansionTile),
          ).first;
          await tester.tap(firstJourney);
          await tester.pumpAndSettle();
          expect(
            find.byKey(const ValueKey('my-kefe-journey-timeline')),
            findsOneWidget,
          );

          final footnote = find.byKey(
            const ValueKey('my-kefe-no-inference-note'),
          );
          final journeyScroll = find.descendant(
            of: find.byKey(const ValueKey('my-kefe-journey')),
            matching: find.byType(Scrollable),
          );
          await tester.scrollUntilVisible(
            footnote,
            300,
            scrollable: journeyScroll,
          );
          expect(
            find.byKey(const ValueKey('my-kefe-no-inference-note')),
            findsOneWidget,
          );
          expect(tester.takeException(), isNull);
        },
      );
    }
  }

  test('governed history screens do not reintroduce dark-only tokens', () {
    final paths = [
      'lib/features/activity/presentation/activity_screen.dart',
      'lib/features/progress/presentation/my_kefe_journey_screen.dart',
      'lib/features/progress/presentation/progress_section.dart',
      'lib/features/saved_cases/presentation/saved_cases_section.dart',
    ];

    for (final path in paths) {
      final source = _readPresentationLibrary(path);
      expect(source, contains('KefeSurface'));
      expect(source, isNot(contains('KefeColorTokens.surfaceDark')));
      expect(source, isNot(contains('KefeColorTokens.borderDark')));
      expect(source, isNot(contains('KefeColorTokens.textMutedDark')));
    }
  });

  test('history presentation uses display-time Case localization only', () {
    final myKefe = _readPresentationLibrary(
      'lib/features/progress/presentation/my_kefe_journey_screen.dart',
    );
    final progress = File(
      'lib/features/progress/presentation/progress_section.dart',
    ).readAsStringSync();
    final saved = File(
      'lib/features/saved_cases/presentation/saved_cases_section.dart',
    ).readAsStringSync();

    for (final source in [myKefe, progress, saved]) {
      expect(source, contains('kefeContentLocalizerProvider'));
      expect(source, contains('KefeContentNamespace.caseTitle'));
    }
    expect(saved, contains('KefeContentNamespace.caseSummary'));
  });
}

String _readPresentationLibrary(String mainPath) {
  final mainFile = File(mainPath);
  final mainSource = mainFile.readAsStringSync();
  final parts = RegExp(r"part '([^']+)';")
      .allMatches(mainSource)
      .map((match) => File('${mainFile.parent.path}/${match.group(1)}'))
      .where((file) => file.existsSync())
      .map((file) => file.readAsStringSync());
  return ([mainSource, ...parts]).join('\n');
}

Future<void> _pumpHistorySurface(
  WidgetTester tester, {
  required Locale locale,
  required bool dark,
  required Widget child,
}) async {
  tester.platformDispatcher.localeTestValue = locale;
  addTearDown(tester.platformDispatcher.clearLocaleTestValue);

  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        progressRepositoryProvider.overrideWithValue(
          PreviewProgressRepository(),
        ),
        savedCaseStoreProvider.overrideWithValue(MemorySavedCaseStore()),
        kefeContentLocalizerProvider.overrideWithValue(
          const PreviewContentLocalizer(),
        ),
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
        home: Scaffold(body: child),
      ),
    ),
  );
  await tester.pumpAndSettle();
}
