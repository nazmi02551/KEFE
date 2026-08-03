import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app/kefe_app.dart';
import 'core/config/experience_presentation_config.dart';
import 'features/community_reason/application/community_reason_controller.dart';
import 'features/consensus/application/consensus_controller.dart';
import 'features/decision/application/decision_controller.dart';
import 'features/decision/data/http_reflection_decision_repository.dart';
import 'features/privacy/application/privacy_controller.dart';
import 'features/sharing/application/share_controller.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(
    ProviderScope(
      overrides: [
        experiencePresentationConfigProvider.overrideWithValue(
          ExperiencePresentationConfig.fromEnvironment(),
        ),
        decisionRepositoryProvider.overrideWith(
          (ref) => HttpReflectionDecisionRepository(
            config: ref.watch(appConfigProvider),
            client: ref.watch(httpClientProvider),
            credentialStore: ref.watch(credentialStoreProvider),
          ),
        ),
        consensusExperienceEnabledProvider.overrideWithValue(true),
        communityReasonExperienceEnabledProvider.overrideWithValue(true),
        shareExperienceEnabledProvider.overrideWithValue(true),
        privacyExperienceEnabledProvider.overrideWithValue(true),
      ],
      child: const KefeApp(),
    ),
  );
}
