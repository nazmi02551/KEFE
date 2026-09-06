import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/observe_mode_exploration_models.dart';
import 'package:kefe_mobile/features/decision/presentation/observe_mode_exploration_card.dart';

void main() {
  group('Observe Mode & Non-Binding Exploration (CAP-029)', () {
    test('ADR-0199 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0199-observe-mode-exploration.md');
      final contract = File('../../docs/contracts/observe-mode-exploration.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-OBSERVE-MODE-001'));
      expect(contract.readAsStringSync(), contains('OBSERVE_ONLY'));
    });

    test('ObserveModeSessionModel instantiates properly', () {
      const model = ObserveModeSessionModel(
        sessionId: 'obs_1',
        caseVersionId: 'case-1',
        explorationMode: ExplorationModeModel.studyAndLearn,
        isBindingVote: false,
        viewedArgumentCount: 6,
        viewedEvidenceCount: 3,
      );

      expect(model.isBindingVote, isFalse);
      expect(model.explorationMode, ExplorationModeModel.studyAndLearn);
    });

    test('InternalAlphaStrings contains Observe Mode localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.observeModeEyebrow, contains('GÖZLEMCİ MODU'));
      expect(tr.observeModeNonBindingBadge, contains('BAĞLAYICI'));

      const en = KefeStrings(Locale('en'));
      expect(en.observeModeEyebrow, contains('OBSERVE MODE'));
      expect(en.observeModeNonBindingBadge, contains('NON-BINDING'));
    });

    testWidgets('ObserveModeExplorationCard renders correctly', (tester) async {
      const model = ObserveModeSessionModel(
        sessionId: 'obs_1',
        caseVersionId: 'case-1',
        explorationMode: ExplorationModeModel.studyAndLearn,
        isBindingVote: false,
        viewedArgumentCount: 6,
        viewedEvidenceCount: 3,
      );

      await tester.pumpWidget(
        MaterialApp(
          theme: ThemeData.dark().copyWith(
            extensions: const [KefeVisualTheme.dark],
          ),
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
              child: ObserveModeExplorationCard(session: model),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(ObserveModeExplorationCard), findsOneWidget);
      expect(find.textContaining('GÖZLEMCİ MODU'), findsOneWidget);
    });
  });
}


