import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('phone-preview entrypoint enables visual media review mode', () {
    final source = File('lib/main_preview.dart').readAsStringSync();

    expect(
      source,
      contains('productPreviewVisualModeProvider.overrideWithValue(true)'),
    );
    expect(
      source,
      contains('caseMediaRepositoryProvider.overrideWithValue('),
    );
    expect(source, contains('const PreviewCaseMediaRepository()'));
    expect(source, contains('runApp('));
    expect(source, contains('const ProductPreviewApp()'));
  });
}
