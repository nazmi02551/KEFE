import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/config/experience_presentation_config.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/onboarding/presentation/onboarding_experience_screen.dart';

Future<void> pumpExperience(
  WidgetTester tester,
  ExperiencePresentationConfig config,
) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        experiencePresentationConfigProvider.overrideWithValue(config),
      ],
      child: MaterialApp(
        locale: const Locale('tr', 'TR'),
        theme: KefeTheme.light(),
        darkTheme: KefeTheme.dark(),
        supportedLocales: KefeStrings.supportedLocales,
        localizationsDelegates: const [
          KefeStringsDelegate(),
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        home: const OnboardingExperienceScreen(reviewMode: true),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('v2 separates own decision community position and perspectives', (
    tester,
  ) async {
    await pumpExperience(
      tester,
      const ExperiencePresentationConfig.progressive(),
    );

    expect(find.text('Önce kendi kararını tart.'), findsOneWidget);
    expect(find.byKey(const ValueKey('onboarding-promise-1')), findsOneWidget);

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
    expect(find.textContaining('nedenini varsaymaz'), findsOneWidget);
    expect(find.text('İlk tartımı yap'), findsOneWidget);
    expect(find.byKey(const ValueKey('onboarding-promise-3')), findsOneWidget);
  });

  testWidgets('legacy onboarding remains available independently', (
    tester,
  ) async {
    await pumpExperience(
      tester,
      const ExperiencePresentationConfig(
        decisionJourneyMode: DecisionJourneyPresentationMode.progressive,
        onboardingVersion: OnboardingExperienceVersion.legacyV1,
      ),
    );

    expect(find.text('Önce kendi kararını gör.'), findsOneWidget);
    expect(find.byKey(const ValueKey('onboarding-promise-3')), findsNothing);
  });
}
