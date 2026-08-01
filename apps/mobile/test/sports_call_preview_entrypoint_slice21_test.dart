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

    expect(source, contains("path: '/case/:caseId'"));
    expect(source, contains('DecisionFlowScreen('));
    expect(source, contains("state.pathParameters['caseId']!"));
    expect(
      source,
      isNot(contains("caseId == '11111111-1111-4111-8111-111111111113'")),
    );
  });
}
