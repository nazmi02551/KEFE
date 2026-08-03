import 'package:flutter_riverpod/flutter_riverpod.dart';

enum DecisionJourneyPresentationMode { progressive, legacyLongScroll }

enum OnboardingExperienceVersion { v2, legacyV1 }

class ExperiencePresentationConfig {
  const ExperiencePresentationConfig({
    required this.decisionJourneyMode,
    required this.onboardingVersion,
  });

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

final experiencePresentationConfigProvider =
    Provider<ExperiencePresentationConfig>(
      (ref) => ExperiencePresentationConfig.fromEnvironment(),
    );
