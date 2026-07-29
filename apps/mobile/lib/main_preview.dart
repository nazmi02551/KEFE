import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app/product_preview_app.dart';
import 'core/design/product_preview_visual_mode.dart';
import 'features/decision/application/decision_controller.dart';
import 'features/decision/data/preview_journey_decision_repository.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(
    ProviderScope(
      overrides: [
        decisionRepositoryProvider.overrideWithValue(
          PreviewJourneyDecisionRepository(),
        ),
        productPreviewVisualModeProvider.overrideWithValue(true),
      ],
      child: const ProductPreviewApp(),
    ),
  );
}
