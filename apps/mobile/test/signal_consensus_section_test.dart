import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/preview_decision_repository.dart';
import 'package:kefe_mobile/features/signal/data/preview_signal_repository.dart';
import 'package:kefe_mobile/features/signal/data/signal_repository.dart';
import 'package:kefe_mobile/features/signal/presentation/signal_consensus_card.dart';
import 'package:kefe_mobile/features/weigh/presentation/weigh_hub_screen.dart';

void main() {
  testWidgets(
    'WeighHubScreen enforces Blind First isolation: no consensus signals or institution responses before commit',
    (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            decisionRepositoryProvider.overrideWithValue(
              PreviewDecisionRepository(),
            ),
            signalRepositoryProvider.overrideWithValue(
              PreviewSignalRepository(),
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
            home: Scaffold(body: WeighHubScreen()),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Invariant: WeighHub must not contain pre-commit collective signals or institution responses
      expect(
        find.byKey(const ValueKey('signal-consensus-section')),
        findsNothing,
      );
      expect(
        find.byKey(const ValueKey('institution-response-section')),
        findsNothing,
      );
      expect(find.byType(SignalConsensusCard), findsNothing);

      // Featured weigh case is preserved for decision making
      expect(find.byKey(const ValueKey('weigh-hub-featured')), findsOneWidget);
    },
  );
}
