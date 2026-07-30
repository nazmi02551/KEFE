import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/kefe_app.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/onboarding/application/onboarding_controller.dart';
import 'package:kefe_mobile/features/onboarding/data/onboarding_store.dart';
import 'package:kefe_mobile/features/sharing/data/share_repository.dart';

void main() {
  test(
    'MVP keeps encrypted seven-day uncommitted draft policy in production code',
    () {
      final source = File(
        'lib/features/decision/data/decision_draft_store.dart',
      ).readAsStringSync();
      final controller = File(
        'lib/features/decision/application/decision_controller.dart',
      ).readAsStringSync();

      expect(source, contains('SecureDecisionDraftStore'));
      expect(source, contains('FlutterSecureStorage'));
      expect(source, contains('Duration(days: 7)'));
      expect(source, contains('DecisionDraftPhase.commitPending'));
      expect(source, contains('DecisionDraftPhase.committedAwaitingReveal'));
      expect(controller, contains('SecureDecisionDraftStore()'));
      expect(
        controller,
        isNot(contains('SharedPreferencesDecisionDraftStore()')),
      );
    },
  );

  test(
    'production composition exposes MVP capabilities without preview fallback',
    () {
      final mainSource = File('lib/main.dart').readAsStringSync();
      final routerSource = File('lib/app/kefe_app.dart').readAsStringSync();

      expect(mainSource, contains('consensusExperienceEnabledProvider'));
      expect(mainSource, contains('communityReasonExperienceEnabledProvider'));
      expect(mainSource, contains('shareExperienceEnabledProvider'));
      expect(mainSource, contains('privacyExperienceEnabledProvider'));
      expect(mainSource, isNot(contains('PreviewConsensusRepository')));
      expect(mainSource, isNot(contains('PreviewProgressRepository')));
      expect(routerSource, contains("path: '/account'"));
      expect(routerSource, contains("path: '/privacy'"));
      expect(routerSource, contains("path: '/share/:token'"));
    },
  );

  test('Share MVP is case-only with the canonical deep link', () {
    final share = CreatedShare(
      id: 'share-1',
      token: 'opaque-token',
      expiresAt: DateTime.utc(2026, 8, 1),
      includeDecision: false,
    );
    final section = File(
      'lib/features/sharing/presentation/share_section.dart',
    ).readAsStringSync();
    final controller = File(
      'lib/features/sharing/application/share_controller.dart',
    ).readAsStringSync();
    final publicModel = File(
      'lib/features/sharing/data/share_repository.dart',
    ).readAsStringSync();

    expect(share.deepLink, 'kefe:///share/opaque-token');
    expect(section, isNot(contains('share-include-decision')));
    expect(controller, contains('includeDecision: false'));
    expect(
      publicModel,
      isNot(contains('final Map<String, Object?>? decision')),
    );
  });

  test('locale and theme contract includes MVP minimum surfaces', () {
    final languageCodes = KefeStrings.supportedLocales
        .map((locale) => locale.languageCode)
        .toSet();
    expect(languageCodes, containsAll(<String>{'tr', 'en'}));
    expect(KefeTheme.light().brightness, Brightness.light);
    expect(KefeTheme.dark().brightness, Brightness.dark);
  });

  testWidgets('welcome remains usable with large text and semantic tree', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1080, 2400);
    tester.view.devicePixelRatio = 3;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final semantics = tester.ensureSemantics();
    addTearDown(semantics.dispose);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          onboardingStoreProvider.overrideWithValue(MemoryOnboardingStore()),
        ],
        child: const MediaQuery(
          data: MediaQueryData(textScaler: TextScaler.linear(1.5)),
          child: KefeApp(initialLocation: '/welcome'),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(Scaffold), findsOneWidget);
    expect(find.text('KEFE'), findsWidgets);
    expect(tester.takeException(), isNull);
  });
}
