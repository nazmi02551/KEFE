import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('phone-preview entrypoint enables visual media review mode', () {
    final source = File('lib/main_preview.dart').readAsStringSync();

    expect(
      source,
      contains('productPreviewVisualModeProvider.overrideWithValue(true)'),
    );
    expect(source, contains('caseMediaRepositoryProvider.overrideWithValue('));
    expect(source, contains('const PreviewCaseMediaRepository()'));
    expect(source, contains('runApp('));
    expect(source, contains('const ProductPreviewApp()'));
  });

  test('Product Preview retains the generic Case route', () {
    final source = File('lib/app/product_preview_app.dart').readAsStringSync();
    final experience = File(
      'lib/features/decision/presentation/decision_experience_screen.dart',
    ).readAsStringSync();

    expect(source, contains("path: '/case/:caseId'"));
    expect(source, contains('DecisionExperienceScreen('));
    expect(source, contains("state.pathParameters['caseId']!"));
    expect(experience, contains('DecisionFlowScreen('));
    expect(
      source,
      isNot(contains("caseId == '11111111-1111-4111-8111-111111111113'")),
    );
    expect(experience, isNot(contains('caseId ==')));
  });
}
