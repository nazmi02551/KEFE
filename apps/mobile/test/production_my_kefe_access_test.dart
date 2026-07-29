import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/kefe_app.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/preview_decision_repository.dart';
import 'package:kefe_mobile/features/progress/application/progress_controller.dart';
import 'package:kefe_mobile/features/progress/data/preview_progress_repository.dart';

void main() {
  testWidgets(
    'standalone production Explore opens actor-scoped My KEFE without preview shell',
    (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            decisionRepositoryProvider.overrideWithValue(
              PreviewDecisionRepository(),
            ),
            progressRepositoryProvider.overrideWithValue(
              PreviewProgressRepository(),
            ),
          ],
          child: const KefeApp(initialLocation: '/explore'),
        ),
      );
      await tester.pumpAndSettle();

      final openMyKefe = find.byKey(const ValueKey('open-my-kefe'));
      expect(openMyKefe, findsOneWidget);
      expect(find.byKey(const ValueKey('preview-build-identity')), findsNothing);

      await tester.tap(openMyKefe);
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('my-kefe-journey')), findsOneWidget);
      expect(find.text('My KEFE'), findsOneWidget);
      expect(find.byKey(const ValueKey('preview-build-identity')), findsNothing);

      await tester.tap(find.byType(BackButton));
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('open-my-kefe')), findsOneWidget);
    },
  );
}
