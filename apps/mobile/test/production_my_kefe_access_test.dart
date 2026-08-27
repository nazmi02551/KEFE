import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/kefe_app.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/preview_decision_repository.dart';
import 'package:kefe_mobile/features/progress/application/progress_controller.dart';
import 'package:kefe_mobile/features/progress/data/preview_progress_repository.dart';
import 'package:kefe_mobile/features/saved_cases/application/saved_cases_controller.dart';
import 'package:kefe_mobile/features/saved_cases/data/saved_case_store.dart';

void main() {
  testWidgets(
    'production exposes four canonical destinations without preview shell data',
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
            savedCaseStoreProvider.overrideWithValue(MemorySavedCaseStore()),
          ],
          child: const KefeApp(initialLocation: '/explore'),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('primary-navigation')), findsOneWidget);
      expect(find.byType(NavigationDestination), findsNWidgets(4));
      final destinations = tester
          .widgetList<NavigationDestination>(find.byType(NavigationDestination))
          .toList(growable: false);
      expect(destinations.length, 4);
      expect(destinations.last.label, 'My KEFE');
      expect(find.byKey(const ValueKey('preview-build-identity')), findsNothing);
      expect(find.byKey(const ValueKey('open-preview-radar')), findsNothing);
      expect(find.byKey(const ValueKey('open-preview-atlas')), findsNothing);

      await tester.tap(find.byIcon(Icons.person_outline_rounded));
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('my-kefe-journey')), findsOneWidget);
      expect(find.byKey(const ValueKey('saved-cases-section')), findsNothing);
      expect(find.byKey(const ValueKey('preview-build-identity')), findsNothing);

      await tester.tap(find.byIcon(Icons.history_outlined));
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('activity-screen')), findsOneWidget);
      expect(find.byKey(const ValueKey('saved-cases-section')), findsOneWidget);
      expect(find.byKey(const ValueKey('preview-build-identity')), findsNothing);
    },
  );
}
