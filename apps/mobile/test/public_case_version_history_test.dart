import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kefe_mobile/core/config/app_config.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_repository.dart';
import 'package:kefe_mobile/features/decision/data/http_decision_repository.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';
import 'package:kefe_mobile/features/decision/presentation/case_version_history_section.dart';

const caseId = '71000000-0000-4000-8000-000000000001';

final config = AppConfig(
  apiBaseUri: Uri.parse('https://api.example.com'),
  requestTimeout: const Duration(seconds: 5),
);

Map<String, Object?> version({
  required String id,
  required int number,
  required String classification,
  String? publishedAt = '2026-08-27T12:00:00Z',
}) => {
  'case_version_id': id,
  'version_no': number,
  'title': 'Title $number',
  'summary': 'Summary $number',
  'published_at': publishedAt,
  'classification': classification,
};

HttpDecisionRepository repositoryFor(List<Object?> items) {
  return HttpDecisionRepository(
    config: config,
    client: MockClient((request) async {
      expect(request.url.path, '/v1/cases/$caseId/history');
      return http.Response(
        jsonEncode({'case_id': caseId, 'items': items}),
        200,
        headers: const {'content-type': 'application/json'},
      );
    }),
    credentialStore: MemoryCredentialStore(),
  );
}

class HistoryFakeRepository
    implements DecisionRepository, PublicCaseHistoryRepository {
  HistoryFakeRepository(this.versions);

  final List<PublicCaseVersion> versions;

  @override
  Future<List<PublicCaseVersion>> fetchPublicCaseHistory(String caseId) async =>
      versions;

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class UnavailableHistoryFakeRepository extends HistoryFakeRepository {
  UnavailableHistoryFakeRepository() : super(const []);

  @override
  Future<List<PublicCaseVersion>> fetchPublicCaseHistory(String caseId) {
    throw const ClientTransportFailure();
  }
}

Widget historyApp({
  required Locale locale,
  required DecisionRepository repository,
  Future<List<PublicCaseVersion>> Function()? historyLoader,
}) => ProviderScope(
  retry: (_, _) => null,
  overrides: [
    decisionRepositoryProvider.overrideWithValue(repository),
    if (historyLoader != null)
      publicCaseVersionHistoryProvider(
        caseId,
      ).overrideWith((ref) => historyLoader()),
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
    home: const Scaffold(
      body: SingleChildScrollView(
        child: CaseVersionHistorySection(caseId: caseId),
      ),
    ),
  ),
);

void main() {
  test('parses exact newest-first public history', () async {
    final history = await repositoryFor([
      version(
        id: '71000000-0000-4000-8000-000000000003',
        number: 2,
        classification: 'CURRENT',
      ),
      version(
        id: '71000000-0000-4000-8000-000000000002',
        number: 1,
        classification: 'PREVIOUS',
        publishedAt: null,
      ),
    ]).fetchPublicCaseHistory(caseId);

    expect(history.map((item) => item.versionNo), [2, 1]);
    expect(history.first.isCurrent, isTrue);
    expect(history.last.isCurrent, isFalse);
    expect(history.first.publishedAt, DateTime.utc(2026, 8, 27, 12));
    expect(history.last.publishedAt, isNull);
  });

  test(
    'fails closed on duplicate, reordered or unknown public history',
    () async {
      for (final items in <List<Object?>>[
        [
          version(
            id: '71000000-0000-4000-8000-000000000003',
            number: 2,
            classification: 'CURRENT',
          ),
          version(
            id: '71000000-0000-4000-8000-000000000002',
            number: 2,
            classification: 'PREVIOUS',
          ),
        ],
        [
          version(
            id: '71000000-0000-4000-8000-000000000002',
            number: 1,
            classification: 'CURRENT',
          ),
          version(
            id: '71000000-0000-4000-8000-000000000003',
            number: 2,
            classification: 'PREVIOUS',
          ),
        ],
        [
          version(
            id: '71000000-0000-4000-8000-000000000003',
            number: 2,
            classification: 'CORRECTED',
          ),
        ],
      ]) {
        await expectLater(
          repositoryFor(items).fetchPublicCaseHistory(caseId),
          throwsA(
            isA<ClientTransportFailure>().having(
              (error) => error.code,
              'code',
              'PUBLIC_CASE_HISTORY_RESPONSE_INVALID',
            ),
          ),
        );
      }
    },
  );

  test(
    'history provider delegates through the configured repository',
    () async {
      final versions = [
        PublicCaseVersion(
          versionId: 'current',
          versionNo: 2,
          title: 'Current title',
          summary: 'Current summary',
          publishedAt: DateTime.utc(2026, 8, 27),
          classification: PublicCaseVersionClassification.current,
        ),
      ];
      final repository = HistoryFakeRepository(versions);
      final container = ProviderContainer(
        retry: (_, _) => null,
        overrides: [decisionRepositoryProvider.overrideWithValue(repository)],
      );
      addTearDown(container.dispose);

      expect(
        await container.read(publicCaseVersionHistoryProvider(caseId).future),
        same(versions),
      );
    },
  );

  testWidgets('shows localized current and previous public versions', (
    tester,
  ) async {
    final versions = [
      PublicCaseVersion(
        versionId: 'current',
        versionNo: 2,
        title: 'Güncel başlık',
        summary: 'Güncel özet',
        publishedAt: DateTime.utc(2026, 8, 27),
        classification: PublicCaseVersionClassification.current,
      ),
      PublicCaseVersion(
        versionId: 'previous',
        versionNo: 1,
        title: 'Önceki başlık',
        summary: 'Önceki özet',
        publishedAt: DateTime.utc(2026, 8, 20),
        classification: PublicCaseVersionClassification.previous,
      ),
    ];
    await tester.pumpWidget(
      historyApp(
        locale: const Locale('tr', 'TR'),
        repository: HistoryFakeRepository(versions),
        historyLoader: () async => versions,
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Yayımlanmış sürüm geçmişi'), findsOneWidget);
    expect(find.text('2 yayımlanmış sürüm'), findsOneWidget);
    expect(find.text('Güncel başlık'), findsNothing);

    await tester.tap(find.byKey(const ValueKey('case-history-expand')));
    await tester.pumpAndSettle();

    expect(find.text('Güncel yayımlanmış sürüm · Sürüm 2'), findsOneWidget);
    expect(find.text('Önceki yayımlanmış sürüm · Sürüm 1'), findsOneWidget);
    expect(find.text('Güncel başlık'), findsOneWidget);
    expect(find.text('Önceki başlık'), findsOneWidget);
    expect(find.textContaining('Düzeltildi'), findsNothing);
  });

  testWidgets(
    'history failure is localized and remains independently retryable',
    (tester) async {
      await tester.pumpWidget(
        historyApp(
          locale: const Locale('en'),
          repository: UnavailableHistoryFakeRepository(),
        ),
      );
      await tester.pumpAndSettle();

      expect(
        find.text(
          'Published version history is unavailable. You can still review and weigh this case.',
        ),
        findsOneWidget,
      );
      expect(find.byKey(const ValueKey('case-history-retry')), findsOneWidget);
    },
  );

  testWidgets('empty history fails closed without blocking the case journey', (
    tester,
  ) async {
    await tester.pumpWidget(
      historyApp(
        locale: const Locale('tr'),
        repository: HistoryFakeRepository(const []),
      ),
    );
    await tester.pumpAndSettle();

    expect(
      find.byKey(const ValueKey('case-history-unavailable')),
      findsOneWidget,
    );
    expect(find.byKey(const ValueKey('case-history-section')), findsNothing);
  });
}
