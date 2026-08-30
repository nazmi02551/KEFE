import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kefe_mobile/core/config/app_config.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/community_reason/application/community_reason_controller.dart';
import 'package:kefe_mobile/features/community_reason/data/community_reason_repository.dart';
import 'package:kefe_mobile/features/community_reason/data/http_community_reason_repository.dart';
import 'package:kefe_mobile/features/community_reason/presentation/community_reason_section.dart';
import 'package:kefe_mobile/features/decision/data/decision_repository.dart';
import 'package:kefe_mobile/features/decision/data/http_decision_repository.dart';

const _validBody = <String, Object?>{
  'items': <Object?>[],
  'tag_pattern_counts': <String, Object?>{
    'RULES': 2,
    'NEED': 3,
    'FAIRNESS': 3,
  },
  'sample_size': 5,
  'methodology_note': 'Descriptive post-Commit Community Reasons.',
};

void main() {
  test('CAP-032 contract preserves descriptive non-exclusive boundaries', () {
    final file = File(
      '../../docs/contracts/community-reason-pattern-distribution.v1.json',
    );
    expect(file.existsSync(), isTrue);
    final contract = jsonDecode(file.readAsStringSync()) as Map<String, Object?>;
    final eligibility = contract['eligibility']! as Map<String, Object?>;
    final aggregate = contract['aggregate']! as Map<String, Object?>;
    final presentation = contract['presentation']! as Map<String, Object?>;
    final forbidden = (contract['forbidden']! as List<Object?>).cast<String>();

    expect(eligibility['committed_actor_owned_session_required'], isTrue);
    expect(eligibility['pre_commit_exposure'], isFalse);
    expect(aggregate['sample_size_population_matches_counts'], isTrue);
    expect(aggregate['returned_items_window_independent'], isTrue);
    expect(aggregate['one_count_per_distinct_tag_per_contribution'], isTrue);
    expect(aggregate['multi_tag_non_exclusive'], isTrue);
    expect(presentation['exact_count_and_sample_visible'], isTrue);
    expect(presentation['exclusive_percentage_or_pie'], isFalse);
    expect(forbidden, containsAll(['TRUTH_RANKING', 'IDEOLOGY_INFERENCE']));
  });

  test('HTTP parser accepts internally consistent pattern aggregates', () async {
    final repository = await _httpRepository(_validBody);

    final snapshot = await repository.fetch('session-1');

    expect(snapshot.sampleSize, 5);
    expect(snapshot.tagPatternCounts, {
      'RULES': 2,
      'NEED': 3,
      'FAIRNESS': 3,
    });
  });

  for (final invalid in <Map<String, Object?>>[
    {..._validBody, 'sample_size': -1},
    {..._validBody, 'sample_size': 0},
    {
      ..._validBody,
      'tag_pattern_counts': <String, Object?>{'FAIRNESS': 6},
    },
    {
      ..._validBody,
      'tag_pattern_counts': <String, Object?>{'': 1},
    },
    {
      ..._validBody,
      'tag_pattern_counts': <String, Object?>{'FAIRNESS': 0},
    },
  ]) {
    test('HTTP parser rejects malformed pattern aggregate $invalid', () async {
      final repository = await _httpRepository(invalid);

      await expectLater(
        repository.fetch('session-1'),
        throwsA(
          isA<ClientTransportFailure>().having(
            (error) => error.code,
            'code',
            'INVALID_COMMUNITY_REASON_RESPONSE',
          ),
        ),
      );
    });
  }

  for (final configuration in <({Locale locale, bool dark, double scale})>[
    (locale: const Locale('en', 'US'), dark: true, scale: 1),
    (locale: const Locale('tr', 'TR'), dark: false, scale: 1.6),
  ]) {
    testWidgets(
      'pattern summary is ordered and accessible in ${configuration.locale.languageCode}',
      (tester) async {
        final semantics = tester.ensureSemantics();
        addTearDown(semantics.dispose);
        await _pumpSummary(
          tester,
          locale: configuration.locale,
          dark: configuration.dark,
          textScale: configuration.scale,
        );

        final card = find.byKey(const ValueKey('community-reason-patterns'));
        expect(card, findsOneWidget);
        await tester.ensureVisible(card);
        await tester.pumpAndSettle();

        final fairness = find.byKey(
          const ValueKey('community-reason-pattern-FAIRNESS'),
        );
        final need = find.byKey(
          const ValueKey('community-reason-pattern-NEED'),
        );
        final rules = find.byKey(
          const ValueKey('community-reason-pattern-RULES'),
        );
        expect(fairness, findsOneWidget);
        expect(need, findsOneWidget);
        expect(rules, findsOneWidget);
        expect(tester.getTopLeft(fairness).dy, lessThan(tester.getTopLeft(need).dy));
        expect(tester.getTopLeft(need).dy, lessThan(tester.getTopLeft(rules).dy));
        expect(find.text('3 / 5'), findsNWidgets(2));
        expect(find.text('2 / 5'), findsOneWidget);
        expect(
          tester.getSemantics(fairness).label,
          configuration.locale.languageCode == 'tr'
              ? contains('5 gerekçenin 3 tanesinde')
              : contains('3 of 5 published reasons'),
        );
        expect(tester.takeException(), isNull);
      },
    );
  }
}

Future<HttpCommunityReasonRepository> _httpRepository(
  Map<String, Object?> body,
) async {
  final credentials = MemoryCredentialStore();
  await credentials.write('access-token');
  return HttpCommunityReasonRepository(
    config: AppConfig(
      apiBaseUri: Uri.parse('https://api.example.com'),
      requestTimeout: const Duration(seconds: 2),
    ),
    client: MockClient(
      (request) async => http.Response(
        jsonEncode(body),
        200,
        headers: const {'content-type': 'application/json'},
      ),
    ),
    credentialStore: credentials,
  );
}

Future<void> _pumpSummary(
  WidgetTester tester, {
  required Locale locale,
  required bool dark,
  required double textScale,
}) async {
  tester.view.physicalSize = const Size(360, 800);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  final repository = _PatternRepository();

  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        communityReasonExperienceEnabledProvider.overrideWithValue(true),
        communityReasonRepositoryProvider.overrideWithValue(repository),
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
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(
            context,
          ).copyWith(textScaler: TextScaler.linear(textScale)),
          child: child!,
        ),
        home: const Scaffold(
          body: SafeArea(
            child: SingleChildScrollView(
              padding: EdgeInsets.all(12),
              child: CommunityReasonSection(
                sessionId: 'session-1',
                caseVersionId: 'case-version-1',
              ),
            ),
          ),
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

class _PatternRepository implements CommunityReasonRepository {
  @override
  Future<CommunityReasonSnapshot> fetch(String sessionId) async =>
      const CommunityReasonSnapshot(
        items: [],
        tagPatternCounts: {'RULES': 2, 'NEED': 3, 'FAIRNESS': 3},
        sampleSize: 5,
        methodologyNote: 'Descriptive post-Commit Community Reasons.',
      );

  @override
  Future<CommunityReasonReceipt> publish({
    required String sessionId,
    required List<String> tags,
    String? text,
  }) async => throw UnimplementedError();

  @override
  Future<void> react({required String reasonId, required String reaction}) async {
    throw UnimplementedError();
  }

  @override
  Future<void> report({required String reasonId, required String code}) async {
    throw UnimplementedError();
  }
}
