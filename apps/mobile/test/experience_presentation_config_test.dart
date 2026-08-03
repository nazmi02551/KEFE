import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/config/experience_presentation_config.dart';

void main() {
  test('environment-selected build defaults to progressive experience', () {
    final config = ExperiencePresentationConfig.fromEnvironment();

    expect(
      config.decisionJourneyMode,
      DecisionJourneyPresentationMode.progressive,
    );
    expect(config.onboardingVersion, OnboardingExperienceVersion.v2);
  });

  test('direct provider construction remains legacy safe', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    final config = container.read(experiencePresentationConfigProvider);

    expect(
      config.decisionJourneyMode,
      DecisionJourneyPresentationMode.legacyLongScroll,
    );
    expect(config.onboardingVersion, OnboardingExperienceVersion.legacyV1);
  });

  test('modes remain independently constructible for rollback builds', () {
    const decisionRollbackOnly = ExperiencePresentationConfig(
      decisionJourneyMode: DecisionJourneyPresentationMode.legacyLongScroll,
      onboardingVersion: OnboardingExperienceVersion.v2,
    );
    const onboardingRollbackOnly = ExperiencePresentationConfig(
      decisionJourneyMode: DecisionJourneyPresentationMode.progressive,
      onboardingVersion: OnboardingExperienceVersion.legacyV1,
    );

    expect(
      decisionRollbackOnly.decisionJourneyMode,
      DecisionJourneyPresentationMode.legacyLongScroll,
    );
    expect(
      decisionRollbackOnly.onboardingVersion,
      OnboardingExperienceVersion.v2,
    );
    expect(
      onboardingRollbackOnly.decisionJourneyMode,
      DecisionJourneyPresentationMode.progressive,
    );
    expect(
      onboardingRollbackOnly.onboardingVersion,
      OnboardingExperienceVersion.legacyV1,
    );
  });
}
