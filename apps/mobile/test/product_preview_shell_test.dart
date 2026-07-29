import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/product_preview_app.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/preview_decision_repository.dart';

void main() {
  test('preview catalog contains multiple domains and cases', () async {
    final repository = PreviewDecisionRepository();
    final cases = await repository.fetchExploreCases();

    expect(cases.length, greaterThanOrEqualTo(5));
    expect(cases.map((item) => item.domain).toSet().length, greaterThanOrEqualTo(5));
  });

  testWidgets('Product Preview opens on rich Explore and navigates to Radar', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          decisionRepositoryProvider.overrideWithValue(PreviewDecisionRepository()),
        ],
        child: const ProductPreviewApp(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Bugün dünya\nneyi tartıyor?'), findsOneWidget);
    expect(find.text('Trend tartımlar'), findsOneWidget);
    expect(find.text('Radar'), findsOneWidget);

    await tester.tap(find.text('Radar'));
    await tester.pumpAndSettle();

    expect(find.text('Dünya şu an\nneyi tartışıyor?'), findsOneWidget);
    expect(find.textContaining('Canlı trend verisi değil'), findsOneWidget);
  });
}
