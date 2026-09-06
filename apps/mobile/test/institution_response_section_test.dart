import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/preview_decision_repository.dart';
import 'package:kefe_mobile/features/impact/data/institution_response_repository.dart';
import 'package:kefe_mobile/features/impact/data/preview_institution_response_repository.dart';
import 'package:kefe_mobile/features/impact/presentation/institution_response_card.dart';
import 'package:kefe_mobile/features/signal/data/preview_signal_repository.dart';
import 'package:kefe_mobile/features/signal/data/signal_repository.dart';
import 'package:kefe_mobile/features/weigh/presentation/weigh_hub_screen.dart';

import 'package:kefe_mobile/features/observatory/presentation/public_observatory_screen.dart';

void main() {
  group('Institution Response Section & Hub Integration (CAP-049/CAP-050)', () {
    testWidgets('enforces Blind First isolation: no institution responses in WeighHubScreen', (
      tester,
    ) async {
      tester.view.physicalSize = const Size(1080, 2400);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            decisionRepositoryProvider.overrideWithValue(
              PreviewDecisionRepository(),
            ),
            signalRepositoryProvider.overrideWithValue(
              PreviewSignalRepository(),
            ),
            institutionResponseRepositoryProvider.overrideWithValue(
              PreviewInstitutionResponseRepository(),
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

      // Blind First Invariant: pre-commit WeighHub must NOT display institutional responses
      expect(
        find.byKey(const ValueKey('institution-response-section')),
        findsNothing,
      );
      expect(find.byType(InstitutionResponseCard), findsNothing);
    });

    testWidgets('renders verified institution responses in PublicObservatoryScreen', (
      tester,
    ) async {
      tester.view.physicalSize = const Size(1080, 2400);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            institutionResponseRepositoryProvider.overrideWithValue(
              PreviewInstitutionResponseRepository(),
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

      expect(find.byType(InstitutionResponseCard), findsWidgets);
      expect(
        find.textContaining('DOĞRULANMIŞ KURUM YANITI'),
        findsWidgets,
      );
      expect(
        find.textContaining('Ulaştırma ve Altyapı Denetleme Kurulu'),
        findsOneWidget,
      );
    });
  });
}
