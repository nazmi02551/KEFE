import 'package:flutter_riverpod/flutter_riverpod.dart';

enum DecisionJourneyPresentationMode { progressive, legacyLongScroll }

enum OnboardingExperienceVersion { v2, legacyV1 }

class ExperiencePresentationConfig {
  const ExperiencePresentationConfig({
    required this.decisionJourneyMode,
    required this.onboardingVersion,
  });

  const ExperiencePresentationConfig.legacy()
    : decisionJourneyMode = DecisionJourneyPresentationMode.legacyLongScroll,
      onboardingVersion = OnboardingExperienceVersion.legacyV1;

  const ExperiencePresentationConfig.progressive()
    : decisionJourneyMode = DecisionJourneyPresentationMode.progressive,
      onboardingVersion = OnboardingExperienceVersion.v2;

  factory ExperiencePresentationConfig.fromEnvironment() {
    const progressiveDecisionJourney = bool.fromEnvironment(
      'KEFE_PROGRESSIVE_DECISION_JOURNEY',
      defaultValue: true,
    );
    const onboardingV2 = bool.fromEnvironment(
      'KEFE_ONBOARDING_V2',
      defaultValue: true,
    );

    return const ExperiencePresentationConfig(
      decisionJourneyMode: progressiveDecisionJourney
          ? DecisionJourneyPresentationMode.progressive
          : DecisionJourneyPresentationMode.legacyLongScroll,
      onboardingVersion: onboardingV2
          ? OnboardingExperienceVersion.v2
          : OnboardingExperienceVersion.legacyV1,
    );
  }

  final DecisionJourneyPresentationMode decisionJourneyMode;
  final OnboardingExperienceVersion onboardingVersion;
}

/// Direct app/widget construction remains legacy-safe. Real entrypoints install
/// [ExperiencePresentationConfig.fromEnvironment] explicitly so a build can
/// select the new experience or either rollback path independently.
final experiencePresentationConfigProvider =
    Provider<ExperiencePresentationConfig>(
      (ref) => const ExperiencePresentationConfig.legacy(),
    );
