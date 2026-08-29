import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  group('phone candidate surface parity', () {
    late String productionApp;
    late String previewApp;
    late String productionMain;
    late String previewMain;

    setUpAll(() {
      productionApp = File('lib/app/kefe_app.dart').readAsStringSync();
      previewApp = File('lib/app/product_preview_app.dart').readAsStringSync();
      productionMain = File('lib/main.dart').readAsStringSync();
      previewMain = File('lib/main_preview.dart').readAsStringSync();
    });

    test('Product Preview exposes every production consumer route family', () {
      const sharedRoutes = <String>[
        '/welcome',
        '/explore',
        '/weigh',
        '/activity',
        '/my-kefe',
        '/my-kefe/report',
        '/account',
        '/settings',
        '/privacy',
        '/share/:token',
        '/case/:caseId',
      ];

      for (final route in sharedRoutes) {
        expect(
          productionApp,
          contains("path: '$route'"),
          reason: 'Production must expose $route',
        );
        expect(
          previewApp,
          contains("path: '$route'"),
          reason: 'Product Preview must expose production route $route',
        );
      }
    });

    test(
      'Preview-only surfaces stay explicit and out of production routing',
      () {
        const previewOnlyRoutes = <String>['/radar', '/atlas'];

        for (final route in previewOnlyRoutes) {
          expect(previewApp, contains("path: '$route'"));
          expect(
            productionApp,
            isNot(contains("path: '$route'")),
            reason: '$route is a secondary Product Preview surface',
          );
        }

        expect(previewApp, contains("initialLocation: '/explore'"));
        expect(productionApp, contains("initialLocation = '/welcome'"));
        expect(previewApp, contains("'/welcome?review=1'"));
        expect(previewApp, contains("ValueKey('open-preview-first-use')"));
      },
    );

    test('Shared routes render the same production presentation surfaces', () {
      const sharedScreens = <String>[
        'OnboardingExperienceScreen',
        'DiscoveryExploreScreen',
        'WeighHubScreen',
        'ActivityScreen',
        'MyKefeJourneyScreen',
        'MyKefePersonalReportScreen',
        'AccountConversionScreen',
        'SettingsScreen',
        'PrivacyScreen',
        'PublicShareScreen',
        'DecisionExperienceScreen',
      ];

      for (final screen in sharedScreens) {
        expect(
          productionApp,
          contains(screen),
          reason: 'Production router must use $screen',
        );
        expect(
          previewApp,
          contains(screen),
          reason: 'Preview router must reuse $screen instead of a silent fork',
        );
      }

      final decisionExperience = _readPresentationLibrary(
        'lib/features/decision/presentation/decision_experience_screen.dart',
      );
      final onboardingExperience = File(
        'lib/features/onboarding/presentation/onboarding_experience_screen.dart',
      ).readAsStringSync();
      expect(decisionExperience, contains('DecisionFlowScreen('));
      expect(onboardingExperience, contains('OnboardingGateScreen('));
    });

    test('Preview substitutions remain explicit and production-isolated', () {
      const previewRepositories = <String>[
        'PreviewJourneyDecisionRepository',
        'PreviewConsensusRepository',
        'PreviewCommunityReasonRepository',
        'PreviewShareRepository',
        'PreviewPrivacyRepository',
        'PreviewAccountRepository',
        'PreviewCaseMediaRepository',
        'PreviewProgressRepository',
        'MemoryOnboardingStore',
      ];

      for (final repository in previewRepositories) {
        expect(
          previewMain,
          contains(repository),
          reason: 'Preview composition must declare $repository explicitly',
        );
        expect(
          productionMain,
          isNot(contains(repository)),
          reason: '$repository must never leak into production composition',
        );
      }
    });

    test(
      'Governed conditional experiences are enabled in both compositions',
      () {
        const governedFlags = <String>[
          'consensusExperienceEnabledProvider.overrideWithValue(true)',
          'communityReasonExperienceEnabledProvider.overrideWithValue(true)',
          'shareExperienceEnabledProvider.overrideWithValue(true)',
          'privacyExperienceEnabledProvider.overrideWithValue(true)',
          'experiencePresentationConfigProvider.overrideWithValue(',
        ];

        for (final flag in governedFlags) {
          expect(productionMain, contains(flag));
          expect(previewMain, contains(flag));
        }
      },
    );
  });
}

String _readPresentationLibrary(String mainPath) {
  final mainFile = File(mainPath);
  final mainSource = mainFile.readAsStringSync();
  final parts = RegExp(r"part '([^']+)';")
      .allMatches(mainSource)
      .map((match) => File('${mainFile.parent.path}/${match.group(1)}'))
      .where((file) => file.existsSync())
      .map((file) => file.readAsStringSync());
  return ([mainSource, ...parts]).join('\n');
}
