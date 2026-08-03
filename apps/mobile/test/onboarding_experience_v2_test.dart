import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/config/experience_presentation_config.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/onboarding/application/onboarding_controller.dart';
import 'package:kefe_mobile/features/onboarding/data/onboarding_store.dart';
import 'package:kefe_mobile/features/onboarding/presentation/onboarding_gate_screen.dart';

Future<void> pumpOnboarding(
  WidgetTester tester,
  ExperiencePresentationConfig config,
) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        onboardingStoreProvider.overrideWithValue(MemoryOnboardingStore()),
        experiencePresentationConfigProvider.overrideWithValue(config),
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
        home: OnboardingGateScreen(),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('onboarding v2 separates decision, community and perspectives', (
    tester,
  ) async {
    await pumpOnboarding(
      tester,
      const ExperiencePresentationConfig(
        decisionJourneyMode: DecisionJourneyPresentationMode.progressive,
        onboardingVersion: OnboardingExperienceVersion.v2,
      ),
    );

    expect(find.text('Önce kendi kararını tart.'), findsOneWidget);
    expect(find.byKey(const ValueKey('onboarding-promise-3')), findsNothing);

    await tester.tap(find.byKey(const ValueKey('onboarding-primary-button')));
    await tester.pumpAndSettle();

    expect(find.text('Kararının toplumdaki yerini gör.'), findsOneWidget);
    expect(find.textContaining('seni sınıflandırmaz'), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('onboarding-primary-button')));
    await tester.pumpAndSettle();

    expect(
      find.text('Farklı bakışları ve karar yolculuğunu keşfet.'),
      findsOneWidget,
    );
    expect(find.byKey(const ValueKey('onboarding-promise-3')), findsOneWidget);
    expect(find.text('İlk tartımı yap'), findsOneWidget);
  });

  testWidgets('legacy onboarding remains available through provider override', (
    tester,
  ) async {
    await pumpOnboarding(
      tester,
      const ExperiencePresentationConfig(
        decisionJourneyMode: DecisionJourneyPresentationMode.legacyLongScroll,
        onboardingVersion: OnboardingExperienceVersion.legacyV1,
      ),
    );

    expect(find.text('Önce kendi kararını gör.'), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('onboarding-primary-button')));
    await tester.pumpAndSettle();

    expect(find.text('Sonra neden ayrıştığını keşfet.'), findsOneWidget);
    expect(find.byKey(const ValueKey('onboarding-promise-3')), findsNothing);
    expect(find.text('İlk tartımı yap'), findsOneWidget);
  });
}
