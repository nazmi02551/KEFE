import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kefe_mobile/app/kefe_app.dart';
import 'package:kefe_mobile/core/config/app_config.dart';
import 'package:kefe_mobile/core/preferences/app_preferences.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_draft_store.dart';
import 'package:kefe_mobile/features/decision/data/http_decision_repository.dart';
import 'package:kefe_mobile/features/decision/data/preview_journey_decision_repository.dart';
import 'package:kefe_mobile/features/progress/application/progress_controller.dart';
import 'package:kefe_mobile/features/progress/data/http_progress_repository.dart';
import 'package:kefe_mobile/features/progress/data/preview_progress_repository.dart';
import 'package:kefe_mobile/features/progress/domain/progress_models.dart';

const _caseId = '11111111-1111-4111-8111-111111111116';
const _caseVersionId = '22222222-2222-4222-8222-222222222227';

Map<String, Object?> _progressBody({Object? personalReport = _missing}) => {
  'account_offer': {
    'eligible': false,
    'placement': 'POST_REVEAL',
    'blocking': false,
    'dismissible': true,
    'continue_as_guest_available': true,
    'account_creation_available': false,
  },
  'progress': {
    'readiness': 'FORMING',
    'meaningful_weigh_count': 2,
    'distinct_case_count': 1,
    'distinct_domain_count': 1,
    'first_committed_at': '2026-07-29T18:31:00Z',
    'last_committed_at': '2026-07-29T18:45:00Z',
    'recent_cases': <Object?>[],
  },
  'journey': {
    'decision_update_count': 1,
    'revisited_case_count': 1,
    'reflection_completion_count': 1,
    'domain_activity': <Object?>[],
    'recent_journeys': <Object?>[],
  },
  if (!identical(personalReport, _missing)) 'personal_report': personalReport,
  'methodology': {'journey_semantics': 'OBSERVED_PRODUCT_HISTORY_ONLY'},
};

const _missing = Object();

Map<String, Object?> _moment(String type, {Object? revisionNo}) => {
  'type': type,
  'case_id': _caseId,
  'case_version_id': _caseVersionId,
  'title': 'Son koltuk kime verilmeli?',
  'primary_domain': 'DAILY_LIFE',
  'occurred_at': '2026-07-29T18:45:00Z',
  'revision_no': revisionNo,
};

Future<HttpProgressRepository> _repository(Object body) async {
  final store = MemoryCredentialStore();
  await store.write('actor-token');
  return HttpProgressRepository(
    config: AppConfig(
      apiBaseUri: Uri.parse('https://api.example.com'),
      requestTimeout: const Duration(seconds: 2),
    ),
    client: MockClient(
      (_) async => http.Response(
        jsonEncode(body),
        200,
        headers: const {'content-type': 'application/json'},
      ),
    ),
    credentialStore: store,
  );
}

MemoryAppPreferencesStore _preferences({
  required AppLocalePreference locale,
  required AppThemePreference theme,
}) => MemoryAppPreferencesStore(
  AppPreferencesState(locale: locale, theme: theme, loaded: true),
);

Future<void> _pumpReportApp(
  WidgetTester tester, {
  required AppLocalePreference locale,
  required AppThemePreference theme,
  String initialLocation = '/my-kefe/report',
}) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        appPreferencesStoreProvider.overrideWithValue(
          _preferences(locale: locale, theme: theme),
        ),
        decisionRepositoryProvider.overrideWithValue(
          PreviewJourneyDecisionRepository(),
        ),
        decisionDraftStoreProvider.overrideWithValue(
          MemoryDecisionDraftStore(),
        ),
        progressRepositoryProvider.overrideWithValue(
          PreviewProgressRepository(),
        ),
      ],
      child: KefeApp(initialLocation: initialLocation),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  test('strictly parses bounded observed personal-report moments', () async {
    final repository = await _repository(
      _progressBody(
        personalReport: {
          'moments': [
            _moment('DECISION_UPDATE', revisionNo: 2),
            {
              ..._moment('INITIAL_COMMIT'),
              'occurred_at': '2026-07-29T18:31:00Z',
            },
          ],
        },
      ),
    );

    final envelope = await repository.fetchProgress();
    expect(envelope.personalReport.moments, hasLength(2));
    expect(
      envelope.personalReport.moments.first.type,
      MyKefeReportMomentType.decisionUpdate,
    );
    expect(envelope.personalReport.moments.first.revisionNo, 2);
    expect(
      envelope.personalReport.moments.last.type,
      MyKefeReportMomentType.initialCommit,
    );
  });

  test('missing additive report remains backwards-compatible', () async {
    final repository = await _repository(_progressBody());
    expect((await repository.fetchProgress()).personalReport.moments, isEmpty);
  });

  test('malformed present report fails closed', () async {
    final repository = await _repository(
      _progressBody(
        personalReport: {
          'moments': [_moment('DECISION_UPDATE')],
        },
      ),
    );
    await expectLater(repository.fetchProgress(), throwsFormatException);
  });

  testWidgets(
    'My KEFE opens the Turkish dark report and returns through canonical Case',
    (tester) async {
      await _pumpReportApp(
        tester,
        locale: AppLocalePreference.tr,
        theme: AppThemePreference.dark,
        initialLocation: '/my-kefe',
      );

      final journey = find.byKey(const ValueKey('my-kefe-journey'));
      final action = find.byKey(const ValueKey('my-kefe-report-action'));
      await tester.scrollUntilVisible(
        action,
        260,
        scrollable: find.descendant(
          of: journey,
          matching: find.byType(Scrollable),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.textContaining('kayıtlı an'), findsOneWidget);
      await tester.tap(action);
      await tester.pumpAndSettle();

      expect(
        find.byKey(const ValueKey('my-kefe-personal-report')),
        findsOneWidget,
      );
      expect(
        find.text('Karar anların, tek bir zaman çizgisinde.'),
        findsOneWidget,
      );
      expect(
        find.byKey(const ValueKey('my-kefe-report-preview-notice')),
        findsOneWidget,
      );
      final report = find.byKey(const ValueKey('my-kefe-personal-report'));
      final reportScrollable = find.descendant(
        of: report,
        matching: find.byType(Scrollable),
      ).first;
      await tester.scrollUntilVisible(
        find.byKey(const ValueKey('my-kefe-report-no-inference')),
        260,
        scrollable: reportScrollable,
      );
      await tester.pumpAndSettle();
      expect(
        find.byKey(const ValueKey('my-kefe-report-no-inference')),
        findsOneWidget,
      );
      await tester.scrollUntilVisible(
        find.byKey(const ValueKey('my-kefe-report-moment-0')),
        -260,
        scrollable: reportScrollable,
      );
      await tester.pumpAndSettle();
      expect(find.textContaining('Yansıma tamamlandı'), findsWidgets);

      await tester.tap(find.byKey(const ValueKey('my-kefe-report-moment-0')));
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('case-title')), findsOneWidget);
    },
  );

  testWidgets('personal report has English light-theme copy', (tester) async {
    await _pumpReportApp(
      tester,
      locale: AppLocalePreference.en,
      theme: AppThemePreference.light,
    );

    expect(
      find.text('Your decision moments, on one timeline.'),
      findsOneWidget,
    );
    expect(find.text('Journey snapshot'), findsOneWidget);
    final report = find.byKey(const ValueKey('my-kefe-personal-report'));
    final reportScrollable = find.descendant(
      of: report,
      matching: find.byType(Scrollable),
    ).first;
    await tester.scrollUntilVisible(
      find.textContaining('Reflection completed'),
      220,
      scrollable: reportScrollable,
    );
    await tester.pumpAndSettle();
    expect(find.textContaining('Reflection completed'), findsWidgets);
    await tester.scrollUntilVisible(
      find.byKey(const ValueKey('my-kefe-report-no-inference')),
      240,
      scrollable: reportScrollable,
    );
    await tester.pumpAndSettle();
    expect(
      find.textContaining('does not infer why you changed'),
      findsOneWidget,
    );
  });
}
