import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app/product_preview_app.dart';
import 'core/design/product_preview_visual_mode.dart';
import 'features/consensus/application/consensus_controller.dart';
import 'features/consensus/data/preview_consensus_repository.dart';
import 'features/decision/application/decision_controller.dart';
import 'features/decision/data/preview_journey_decision_repository.dart';
import 'features/media_presentation/application/case_media_provider.dart';
import 'features/media_presentation/data/preview_case_media_repository.dart';
import 'features/progress/application/progress_controller.dart';
import 'features/progress/data/preview_progress_repository.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(
    ProviderScope(
      overrides: [
        decisionRepositoryProvider.overrideWithValue(
          PreviewJourneyDecisionRepository(),
        ),
        consensusExperienceEnabledProvider.overrideWithValue(true),
        consensusRepositoryProvider.overrideWithValue(
          PreviewConsensusRepository(),
        ),
        caseMediaRepositoryProvider.overrideWithValue(
          const PreviewCaseMediaRepository(),
        ),
        progressRepositoryProvider.overrideWithValue(
          PreviewProgressRepository(),
        ),
        productPreviewVisualModeProvider.overrideWithValue(true),
      ],
      child: const ProductPreviewApp(),
    ),
  );
}
