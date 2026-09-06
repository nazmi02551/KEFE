import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/observatory/presentation/public_observatory_screen.dart';
import 'package:kefe_mobile/features/signal/data/preview_signal_repository.dart';
import 'package:kefe_mobile/features/signal/data/signal_repository.dart';
import 'package:kefe_mobile/features/signal/presentation/signal_consensus_card.dart';

void main() {
  testWidgets(
    'PublicObservatoryScreen renders qualified consensus signals and institution responses',
    (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
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
            home: PublicObservatoryScreen(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('public-observatory-screen')), findsOneWidget);
      expect(find.text('Kamusal Gözlemevi'), findsOneWidget);
      expect(find.textContaining('KAMUSAL GÖZLEMEVİ'), findsOneWidget);

      // Verify consensus cards are displayed here in the Observatory
      expect(find.byType(SignalConsensusCard), findsWidgets);
      expect(find.text('Son koltuk kime verilmeli?'), findsWidgets);
    },
  );
}
