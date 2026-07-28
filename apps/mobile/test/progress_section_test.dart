import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/progress/application/progress_controller.dart';
import 'package:kefe_mobile/features/progress/data/progress_repository.dart';
import 'package:kefe_mobile/features/progress/domain/progress_models.dart';
import 'package:kefe_mobile/features/progress/presentation/progress_section.dart';

class FakeProgressRepository implements ProgressRepository {
  FakeProgressRepository(this.envelope);

  final ProgressEnvelope envelope;

  @override
  Future<ProgressEnvelope> fetchProgress() async => envelope;
}

ProgressEnvelope sampleProgress({
  bool eligible = true,
  bool accountCreationAvailable = false,
}) {
  return ProgressEnvelope(
    accountOffer: AccountOffer(
      eligible: eligible,
      placement: 'POST_REVEAL',
      blocking: false,
      dismissible: true,
      continueAsGuestAvailable: true,
      accountCreationAvailable: accountCreationAvailable,
    ),
    progress: ProgressEnvelopeData.sample,
    methodology: const {
      'sample_scope': 'CURRENT_ACTOR_COMMITTED_HISTORY',
      'readiness_note': 'PRESENTATION_ONLY_NOT_RESEARCH_VALIDATED',
    },
  );
}

extension ProgressEnvelopeData on MyKefeProgress {
  static final sample = MyKefeProgress(
    readiness: 'INSUFFICIENT_DATA',
    meaningfulWeighCount: 1,
    distinctCaseCount: 1,
    distinctDomainCount: 1,
    firstCommittedAt: DateTime.utc(2026, 7, 28),
    lastCommittedAt: DateTime.utc(2026, 7, 28),
    recentCases: [
      RecentProgressCase(
        caseId: 'case-1',
        caseVersionId: 'version-1',
        title: 'Son koltuk kime verilmeli?',
        primaryDomain: 'DAILY_LIFE',
        committedAt: DateTime.utc(2026, 7, 28),
      ),
    ],
  );
}

Future<void> pumpProgress(
  WidgetTester tester,
  ProgressEnvelope envelope,
) async {
  tester.platformDispatcher.localeTestValue = const Locale('tr', 'TR');
  addTearDown(tester.platformDispatcher.clearLocaleTestValue);
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        progressRepositoryProvider.overrideWithValue(
          FakeProgressRepository(envelope),
        ),
      ],
      child: const MaterialApp(
        locale: Locale('tr', 'TR'),
        supportedLocales: KefeStrings.supportedLocales,
        localizationsDelegates: [
          KefeStringsDelegate(),
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        home: Scaffold(body: SingleChildScrollView(child: ProgressSection())),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('shows low-claim progress and a non-blocking guest account offer', (
    tester,
  ) async {
    await pumpProgress(tester, sampleProgress());

    expect(find.byKey(const ValueKey('my-kefe-progress')), findsOneWidget);
    expect(find.text('1'), findsNWidgets(3));
    expect(find.byKey(const ValueKey('account-offer')), findsOneWidget);
    expect(find.byType(FilledButton), findsNothing);
    expect(find.byKey(const ValueKey('account-offer-continue-guest')), findsOneWidget);
    expect(find.textContaining('kişilik veya ideoloji'), findsOneWidget);
  });

  testWidgets('continue as guest dismisses only the offer, never progress', (
    tester,
  ) async {
    await pumpProgress(tester, sampleProgress());

    await tester.tap(find.byKey(const ValueKey('account-offer-continue-guest')));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('account-offer')), findsNothing);
    expect(find.byKey(const ValueKey('my-kefe-progress')), findsOneWidget);
  });

  testWidgets('does not expose an offer before the first committed weigh', (
    tester,
  ) async {
    await pumpProgress(tester, sampleProgress(eligible: false));

    expect(find.byKey(const ValueKey('my-kefe-progress')), findsOneWidget);
    expect(find.byKey(const ValueKey('account-offer')), findsNothing);
  });
}
