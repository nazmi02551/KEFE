import 'dart:io';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';

double _luminance(Color c) {
  double channel(double v) =>
      v <= 0.03928 ? v / 12.92 : math.pow((v + 0.055) / 1.055, 2.4).toDouble();
  final r = channel(c.r);
  final g = channel(c.g);
  final b = channel(c.b);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

double _contrastRatio(Color c1, Color c2) {
  final l1 = _luminance(c1);
  final l2 = _luminance(c2);
  final lighter = math.max(l1, l2);
  final darker = math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

void main() {
  group('Dual-Theme Contrast and Accessibility Contract (CAP-077)', () {
    test('ADR-0157 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0157-dual-theme-and-reduce-motion-accessibility-contract.md');
      final contract = File('../../docs/contracts/accessibility-theme-motion.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-ACCESSIBILITY-THEME-MOTION-001'));
      expect(contract.readAsStringSync(), contains('wcag_aa_minimum_contrast'));
    });

    test('Dark theme satisfies WCAG AA contrast ratio (>= 4.5:1)', () {
      const dark = KefeVisualTheme.dark;
      final textOnCanvas = _contrastRatio(dark.foreground, dark.canvas);
      final textOnSurface = _contrastRatio(dark.foreground, dark.surface);

      expect(textOnCanvas, greaterThanOrEqualTo(4.5));
      expect(textOnSurface, greaterThanOrEqualTo(4.5));
    });

    test('Light theme satisfies WCAG AA contrast ratio (>= 4.5:1)', () {
      const light = KefeVisualTheme.light;
      final textOnCanvas = _contrastRatio(light.foreground, light.canvas);
      final textOnSurface = _contrastRatio(light.foreground, light.surface);

      expect(textOnCanvas, greaterThanOrEqualTo(4.5));
      expect(textOnSurface, greaterThanOrEqualTo(4.5));
    });
  });
}
