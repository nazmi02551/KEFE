import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/config/experience_presentation_config.dart';

void main() {
  test('new experience is the default build presentation', () {
    final config = ExperiencePresentationConfig.fromEnvironment();

    expect(
      config.decisionJourneyMode,
      DecisionJourneyPresentationMode.progressive,
    );
    expect(config.onboardingVersion, OnboardingExperienceVersion.v2);
  });

  test('legacy modes remain explicitly constructible for provider overrides', () {
    const config = ExperiencePresentationConfig(
      decisionJourneyMode: DecisionJourneyPresentationMode.legacyLongScroll,
      onboardingVersion: OnboardingExperienceVersion.legacyV1,
    );

    expect(
      config.decisionJourneyMode,
      DecisionJourneyPresentationMode.legacyLongScroll,
    );
    expect(config.onboardingVersion, OnboardingExperienceVersion.legacyV1);
  });
}
