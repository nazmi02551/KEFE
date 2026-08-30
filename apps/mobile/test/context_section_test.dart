import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/context/data/context_repository.dart';
import 'package:kefe_mobile/features/context/domain/context_models.dart';
import 'package:kefe_mobile/features/context/presentation/context_section.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_repository.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';

const caseVersionId = '22222222-2222-4222-8222-222222222222';

class ContextFakeRepository implements DecisionRepository, ContextRepository {
  ContextFakeRepository({this.includePublishedAt = true});

  final bool includePublishedAt;

  @override
  Future<CaseContextSnapshot> fetchContext(String caseVersionId) async {
    return CaseContextSnapshot(
      caseVersionId: caseVersionId,
      blocks: const [
        CaseContextBlock(
          id: 'essential',
          displayOrder: 0,
          disclosureLevel: 'ESSENTIAL',
          title: 'Durum',
          body: 'Temel bağlam.',
          claimStatus: 'VERIFIED',
          sourceIds: ['source-1'],
        ),
        CaseContextBlock(
          id: 'detail',
          displayOrder: 10,
          disclosureLevel: 'DETAIL',
          title: 'Ayrıntı',
          body: 'Ek bağlam.',
          claimStatus: 'UNKNOWN',
          sourceIds: ['source-1'],
        ),
      ],
      sources: [
        CaseContextSource(
          id: 'source-1',
          title: 'Senaryo notu',
          publisher: 'KEFE Editorial',
          sourceKind: 'EDITORIAL',
          url: null,
          publishedAt: includePublishedAt
              ? DateTime.utc(2026, 8, 30, 9, 45)
              : null,
        ),
      ],
    );
  }

  @override
  Future<void> answer({
    required String sessionId,
    required String questionId,
    required Object value,
  }) => throw UnimplementedError();

  @override
  Future<void> commit({
    required String sessionId,
    required String idempotencyKey,
  }) => throw UnimplementedError();

  @override
  Future<GuestCredential> ensureGuestCredential() => throw UnimplementedError();

  @override
  Future<DecisionCase> fetchCase(String caseId) => throw UnimplementedError();

  @override
  Future<List<DecisionCaseSummary>> fetchExploreCases({int limit = 20}) =>
      throw UnimplementedError();

  @override
  Future<RevealResult> reveal(String sessionId) => throw UnimplementedError();

  @override
  Future<void> savePrivateReason({
    required String sessionId,
    required List<String> tags,
    required String? text,
  }) => throw UnimplementedError();

  @override
  Future<String> startSession(String caseId) => throw UnimplementedError();
}

void main() {
  testWidgets(
    'Context keeps claim verification separate from neutral source records',
    (tester) async {
      tester.platformDispatcher.localeTestValue = const Locale('tr', 'TR');
      addTearDown(tester.platformDispatcher.clearLocaleTestValue);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            decisionRepositoryProvider.overrideWithValue(
              ContextFakeRepository(),
            ),
          ],
          child: MaterialApp(
            locale: const Locale('tr', 'TR'),
            supportedLocales: KefeStrings.supportedLocales,
            localizationsDelegates: const [
              KefeStringsDelegate(),
              GlobalMaterialLocalizations.delegate,
              GlobalWidgetsLocalizations.delegate,
              GlobalCupertinoLocalizations.delegate,
            ],
            home: const Scaffold(
              body: SingleChildScrollView(
                child: ContextSection(caseVersionId: caseVersionId),
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('context-section')), findsOneWidget);
      expect(find.text('Temel bağlam.'), findsOneWidget);
      expect(find.text('Doğrulandı'), findsOneWidget);
      expect(
        find.byKey(const ValueKey('context-information-status-guide')),
        findsOneWidget,
      );
      expect(
        find.text('Bilgi durumları ne anlama geliyor?'),
        findsOneWidget,
      );
      expect(
        find.text(
          'Durum bilgi bloğuna aittir; bağlı kaynağı ayrıca doğrulamaz.',
        ),
        findsOneWidget,
      );

      await tester.tap(
        find.byKey(const ValueKey('context-information-status-guide')),
      );
      await tester.pumpAndSettle();
      for (final status in const [
        'verified',
        'claimed',
        'disputed',
        'unknown',
      ]) {
        expect(
          find.byKey(ValueKey('context-information-status-$status')),
          findsOneWidget,
        );
      }
      expect(
        find.text(
          'Bu blok bir iddia sunar; doğrulanmış olarak işaretlenmez.',
        ),
        findsOneWidget,
      );
      expect(find.text('Ek bağlam.'), findsNothing);
      expect(find.byKey(const ValueKey('context-details')), findsOneWidget);
      expect(find.byKey(const ValueKey('context-sources')), findsOneWidget);

      final details = find.byKey(const ValueKey('context-details'));
      await tester.ensureVisible(details);
      await tester.tap(details);
      await tester.pumpAndSettle();
      expect(find.text('Ek bağlam.'), findsOneWidget);
      expect(find.text('Bilinmiyor'), findsOneWidget);

      final sources = find.byKey(const ValueKey('context-sources'));
      await tester.ensureVisible(sources);
      await tester.tap(sources);
      await tester.pumpAndSettle();
      expect(
        find.byKey(const ValueKey('context-source-source-1')),
        findsOneWidget,
      );
      expect(find.text('Senaryo notu'), findsOneWidget);
      expect(
        find.text('Kaynak kaydı · KEFE Editorial · Editoryal kaynak'),
        findsOneWidget,
      );
      expect(find.text('Yayın tarihi: 2026-08-30'), findsOneWidget);
      expect(
        find.byKey(
          const ValueKey('context-source-published-source-1'),
        ),
        findsOneWidget,
      );
      expect(find.byIcon(Icons.verified_outlined), findsNothing);

      expect(find.textContaining('result', findRichText: true), findsNothing);
      expect(
        find.textContaining('community', findRichText: true),
        findsNothing,
      );
    },
  );

  testWidgets('Progressive Context shows neutral source references', (
    tester,
  ) async {
    tester.platformDispatcher.localeTestValue = const Locale('tr', 'TR');
    addTearDown(tester.platformDispatcher.clearLocaleTestValue);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          decisionRepositoryProvider.overrideWithValue(ContextFakeRepository()),
        ],
        child: MaterialApp(
          locale: const Locale('tr', 'TR'),
          supportedLocales: KefeStrings.supportedLocales,
          localizationsDelegates: const [
            KefeStringsDelegate(),
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          home: const Scaffold(
            body: SingleChildScrollView(
              child: ContextSection(
                caseVersionId: caseVersionId,
                progressive: true,
              ),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(
      find.byKey(const ValueKey('context-progressive-journey')),
      findsOneWidget,
    );
    expect(find.text('Temel bağlam.'), findsOneWidget);
    expect(find.text('Doğrulandı'), findsOneWidget);
    expect(
      find.byKey(const ValueKey('context-information-status-guide')),
      findsOneWidget,
    );
    expect(find.text('Ek bağlam.'), findsNothing);
    expect(find.text('Senaryo notu'), findsNothing);

    await tester.tap(find.byKey(const ValueKey('context-journey-next')));
    await tester.pumpAndSettle();
    expect(find.text('Temel bağlam.'), findsNothing);
    expect(find.text('Ek bağlam.'), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('context-journey-next')));
    await tester.pumpAndSettle();
    expect(find.text('Ek bağlam.'), findsNothing);
    expect(find.text('Senaryo notu'), findsOneWidget);
    expect(
      find.byKey(const ValueKey('context-source-source-1')),
      findsOneWidget,
    );
    expect(
      find.text('Kaynak kaydı · KEFE Editorial · Editoryal kaynak'),
      findsOneWidget,
    );
    expect(find.text('Yayın tarihi: 2026-08-30'), findsOneWidget);
    expect(find.byIcon(Icons.verified_outlined), findsNothing);
    expect(find.byIcon(Icons.link_rounded), findsWidgets);

    await tester.tap(find.byKey(const ValueKey('context-journey-back')));
    await tester.pumpAndSettle();
    expect(find.text('Ek bağlam.'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'status guide supports English dark theme and enlarged text',
    (tester) async {
      tester.platformDispatcher.localeTestValue = const Locale('en', 'US');
      addTearDown(tester.platformDispatcher.clearLocaleTestValue);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            decisionRepositoryProvider.overrideWithValue(
              ContextFakeRepository(),
            ),
          ],
          child: MaterialApp(
            locale: const Locale('en', 'US'),
            theme: ThemeData.dark(),
            supportedLocales: KefeStrings.supportedLocales,
            localizationsDelegates: const [
              KefeStringsDelegate(),
              GlobalMaterialLocalizations.delegate,
              GlobalWidgetsLocalizations.delegate,
              GlobalCupertinoLocalizations.delegate,
            ],
            home: const MediaQuery(
              data: MediaQueryData(
                size: Size(320, 640),
                textScaler: TextScaler.linear(1.6),
              ),
              child: Scaffold(
                body: SingleChildScrollView(
                  child: ContextSection(caseVersionId: caseVersionId),
                ),
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(
        find.text('What do these information states mean?'),
        findsOneWidget,
      );
      expect(
        find.text(
          'A state belongs to the information block; it does not independently verify a linked source.',
        ),
        findsOneWidget,
      );
      final guide = find.byKey(
        const ValueKey('context-information-status-guide'),
      );
      await tester.ensureVisible(guide);
      await tester.tap(guide);
      await tester.pumpAndSettle();
      expect(
        find.text(
          'The current record does not establish a state for this information block.',
        ),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('source preview omits publication date when absent', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          decisionRepositoryProvider.overrideWithValue(
            ContextFakeRepository(includePublishedAt: false),
          ),
        ],
        child: MaterialApp(
          locale: const Locale('en', 'US'),
          supportedLocales: KefeStrings.supportedLocales,
          localizationsDelegates: const [
            KefeStringsDelegate(),
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          home: const Scaffold(
            body: SingleChildScrollView(
              child: ContextSection(caseVersionId: caseVersionId),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    final sources = find.byKey(const ValueKey('context-sources'));
    await tester.ensureVisible(sources);
    await tester.tap(sources);
    await tester.pumpAndSettle();
    expect(
      find.byKey(const ValueKey('context-source-published-source-1')),
      findsNothing,
    );
    expect(find.textContaining('Published:'), findsNothing);
    expect(tester.takeException(), isNull);
  });
}
