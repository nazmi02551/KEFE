import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app/kefe_app.dart';
import 'features/decision/application/decision_controller.dart';
import 'features/decision/data/preview_decision_repository.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(
    ProviderScope(
      overrides: [
        decisionRepositoryProvider.overrideWithValue(PreviewDecisionRepository()),
      ],
      child: const KefeApp(),
    ),
  );
}
