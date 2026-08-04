import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';
import 'package:kefe_mobile/features/decision/presentation/decision_subjourney.dart';

const _multiQuestionCase = DecisionCase(
  id: 'case-subjourney',
  versionId: 'version-subjourney',
  title: 'Alt yolculuk testi',
  summary: 'Sorular tek tek ilerler.',
  format: 'DILEMMA',
  domain: 'DAILY_LIFE',
  risk: 'L0',
  questions: [
    DecisionQuestion(
      id: 'q1',
      prompt: 'İlk kararın ne?',
      responseType: 'SINGLE_CHOICE',
      options: ['A', 'B'],
      responseSchema: {
        'reason': {
          'tags': ['FAIRNESS', 'EMPATHY'],
          'max_tags': 2,
          'text_enabled': true,
          'text_max_length': 120,
        },
      },
    ),
    DecisionQuestion(
      id: 'q2',
      prompt: 'İkinci ölçüt?',
      responseType: 'SINGLE_CHOICE',
      required: false,
      options: ['X', 'Y'],
    ),
  ],
);

const _oneQuestionCase = DecisionCase(
  id: 'case-one',
  versionId: 'version-one',
  title: 'Tek soru',
  summary: 'Tek soru ve Commit.',
  format: 'DILEMMA',
  domain: 'DAILY_LIFE',
  risk: 'L0',
  questions: [
    DecisionQuestion(
      id: 'only',
      prompt: 'Seçimin?',
      responseType: 'SINGLE_CHOICE',
      options: ['YES', 'NO'],
    ),
  ],
);

Future<void> _tapVisible(WidgetTester tester, Finder finder) async {
  await tester.scrollUntilVisible(
    finder,
    260,
    scrollable: find.byType(Scrollable).first,
  );
  await tester.pump();
  await tester.tap(finder);
  await tester.pumpAndSettle();
}

void main() {
  test(
    'resolver composes questions, optional reason and review generically',
    () {
      final stages = DecisionSubjourneyResolver.stages(_multiQuestionCase);
      expect(stages.map((stage) => stage.kind), [
        DecisionSubjourneyStageKind.question,
        DecisionSubjourneyStageKind.question,
        DecisionSubjourneyStageKind.reason,
        DecisionSubjourneyStageKind.review,
      ]);
      expect(
        DecisionSubjourneyResolver.initialIndex(
          caseData: _multiQuestionCase,
          responses: const {},
        ),
        0,
      );
      expect(
        DecisionSubjourneyResolver.initialIndex(
          caseData: _multiQuestionCase,
          responses: const {'q1': 'A'},
        ),
        1,
      );
      expect(
        DecisionSubjourneyResolver.initialIndex(
          caseData: _multiQuestionCase,
          responses: const {'q1': 'A'},
          skippedQuestionIds: const {'q2'},
        ),
        2,
      );
    },
  );

  test('resolver omits reason stage when CaseVersion has no ReasonPolicy', () {
    final stages = DecisionSubjourneyResolver.stages(_oneQuestionCase);
    expect(stages.length, 2);
    expect(stages.last.kind, DecisionSubjourneyStageKind.review);
    expect(
      DecisionSubjourneyResolver.initialIndex(
        caseData: _oneQuestionCase,
        responses: const {'only': 'YES'},
      ),
      1,
    );
  });

  testWidgets(
    'progressive Decision shows one card, supports skip/back and gates Commit to review',
    (tester) async {
      await tester.pumpWidget(const _SubjourneyTestApp());
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('question-q1')), findsOneWidget);
      expect(find.byKey(const ValueKey('question-q2')), findsNothing);
      expect(find.byKey(const ValueKey('reason-card')), findsNothing);
      expect(
        find.byKey(const ValueKey('subjourney-commit-proof')),
        findsNothing,
      );

      await _tapVisible(tester, find.byKey(const ValueKey('option-A')));
      await _tapVisible(
        tester,
        find.byKey(const ValueKey('decision-subjourney-next')),
      );

      expect(find.byKey(const ValueKey('question-q1')), findsNothing);
      expect(find.byKey(const ValueKey('question-q2')), findsOneWidget);

      await _tapVisible(
        tester,
        find.byKey(const ValueKey('decision-subjourney-next')),
      );
      expect(find.byKey(const ValueKey('reason-card')), findsOneWidget);

      await _tapVisible(
        tester,
        find.byKey(const ValueKey('decision-subjourney-back')),
      );
      expect(find.byKey(const ValueKey('question-q2')), findsOneWidget);

      await _tapVisible(
        tester,
        find.byKey(const ValueKey('decision-subjourney-next')),
      );
      await _tapVisible(
        tester,
        find.byKey(const ValueKey('decision-subjourney-next')),
      );

      expect(
        find.byKey(const ValueKey('decision-subjourney-review')),
        findsOneWidget,
      );
      expect(
        find.byKey(const ValueKey('subjourney-commit-proof')),
        findsOneWidget,
      );
    },
  );
}

class _SubjourneyTestApp extends StatelessWidget {
  const _SubjourneyTestApp();

  @override
  Widget build(BuildContext context) {
    return ProviderScope(
      child: MaterialApp(
        locale: const Locale('tr', 'TR'),
        theme: KefeTheme.light(),
        localizationsDelegates: const [
          KefeStringsDelegate(),
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: KefeStrings.supportedLocales,
        home: const Scaffold(body: SafeArea(child: _SubjourneyHarness())),
      ),
    );
  }
}

class _SubjourneyHarness extends StatefulWidget {
  const _SubjourneyHarness();

  @override
  State<_SubjourneyHarness> createState() => _SubjourneyHarnessState();
}

class _SubjourneyHarnessState extends State<_SubjourneyHarness> {
  final Map<String, Object?> _responses = {};
  final Set<String> _reasonTags = {};
  String _reasonText = '';

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        DecisionSubjourney(
          caseData: _multiQuestionCase,
          flowStepCode: 'decision-1',
          responses: _responses,
          selectedReasonTags: _reasonTags,
          reasonText: _reasonText,
          enabled: true,
          onResponseChanged: (questionId, value) async {
            setState(() => _responses[questionId] = value);
          },
          onReasonTagToggled: (tag) async {
            setState(() {
              if (!_reasonTags.remove(tag)) _reasonTags.add(tag);
            });
          },
          onReasonTextChanged: (value) async {
            setState(() => _reasonText = value);
          },
          reviewAction: const FilledButton(
            key: ValueKey('subjourney-commit-proof'),
            onPressed: null,
            child: Text('Commit proof'),
          ),
        ),
      ],
    );
  }
}
