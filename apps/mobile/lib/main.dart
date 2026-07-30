import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app/kefe_app.dart';
import 'features/consensus/application/consensus_controller.dart';
import 'features/decision/application/decision_controller.dart';
import 'features/decision/data/http_reflection_decision_repository.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(
    ProviderScope(
      overrides: [
        decisionRepositoryProvider.overrideWith(
          (ref) => HttpReflectionDecisionRepository(
            config: ref.watch(appConfigProvider),
            client: ref.watch(httpClientProvider),
            credentialStore: ref.watch(credentialStoreProvider),
          ),
        ),
        consensusExperienceEnabledProvider.overrideWithValue(true),
      ],
      child: const KefeApp(),
    ),
  );
}
