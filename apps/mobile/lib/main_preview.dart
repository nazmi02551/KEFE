import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app/product_preview/preview_content_localizer.dart';
import 'app/product_preview_app.dart';
import 'core/config/experience_presentation_config.dart';
import 'core/design/product_preview_visual_mode.dart';
import 'core/localization/kefe_content_localizer.dart';
import 'features/account/application/account_controller.dart';
import 'features/account/data/preview_account_repository.dart';
import 'features/community_reason/application/community_reason_controller.dart';
import 'features/community_reason/data/preview_community_reason_repository.dart';
import 'features/consensus/application/consensus_controller.dart';
import 'features/consensus/data/preview_consensus_repository.dart';
import 'features/decision/application/decision_controller.dart';
import 'features/decision/data/decision_draft_store.dart';
import 'features/decision/data/preview_journey_decision_repository.dart';
import 'features/media_presentation/application/case_media_provider.dart';
import 'features/media_presentation/data/preview_case_media_repository.dart';
import 'features/onboarding/application/onboarding_controller.dart';
import 'features/onboarding/data/onboarding_store.dart';
import 'features/privacy/application/privacy_controller.dart';
import 'features/privacy/data/preview_privacy_repository.dart';
import 'features/progress/application/progress_controller.dart';
import 'features/progress/data/preview_progress_repository.dart';
import 'features/sharing/application/share_controller.dart';
import 'features/sharing/data/preview_share_repository.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(
    ProviderScope(
      overrides: [
        experiencePresentationConfigProvider.overrideWithValue(
          ExperiencePresentationConfig.fromEnvironment(),
        ),
        decisionRepositoryProvider.overrideWithValue(
          PreviewJourneyDecisionRepository(),
        ),
        decisionDraftStoreProvider.overrideWithValue(
          MemoryDecisionDraftStore(),
        ),
        kefeContentLocalizerProvider.overrideWithValue(
          const PreviewContentLocalizer(),
        ),
        consensusExperienceEnabledProvider.overrideWithValue(true),
        consensusRepositoryProvider.overrideWithValue(
          PreviewConsensusRepository(),
        ),
        communityReasonExperienceEnabledProvider.overrideWithValue(true),
        communityReasonRepositoryProvider.overrideWithValue(
          PreviewCommunityReasonRepository(),
        ),
        shareExperienceEnabledProvider.overrideWithValue(true),
        shareRepositoryProvider.overrideWithValue(PreviewShareRepository()),
        privacyExperienceEnabledProvider.overrideWithValue(true),
        privacyRepositoryProvider.overrideWithValue(PreviewPrivacyRepository()),
        accountRepositoryProvider.overrideWithValue(PreviewAccountRepository()),
        caseMediaRepositoryProvider.overrideWithValue(
          const PreviewCaseMediaRepository(),
        ),
        progressRepositoryProvider.overrideWithValue(
          PreviewProgressRepository(),
        ),
        onboardingStoreProvider.overrideWithValue(MemoryOnboardingStore()),
        productPreviewVisualModeProvider.overrideWithValue(true),
      ],
      child: const ProductPreviewApp(),
    ),
  );
}
