import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/kefe_app.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';

void main() {
  test('MVP keeps encrypted seven-day uncommitted draft policy in production code', () {
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
    expect(controller, isNot(contains('SharedPreferencesDecisionDraftStore()')));
  });

  test('production composition exposes MVP capabilities without preview fallback', () {
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
  });

  test('locale and theme contract includes MVP minimum surfaces', () {
    expect(KefeStrings.supportedLocales, contains(const Locale('tr')));
    expect(KefeStrings.supportedLocales, contains(const Locale('en')));
    expect(KefeTheme.light().brightness, Brightness.light);
    expect(KefeTheme.dark().brightness, Brightness.dark);
  });

  testWidgets('welcome remains usable with large text and semantic tree', (tester) async {
    tester.view.physicalSize = const Size(1080, 2400);
    tester.view.devicePixelRatio = 3;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final semantics = tester.ensureSemantics();
    addTearDown(semantics.dispose);

    await tester.pumpWidget(
      const MediaQuery(
        data: MediaQueryData(textScaler: TextScaler.linear(1.5)),
        child: KefeApp(initialLocation: '/welcome'),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(Scaffold), findsOneWidget);
    expect(find.text('KEFE'), findsWidgets);
    expect(tester.takeException(), isNull);
  });
}
