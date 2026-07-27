import 'package:flutter/material.dart';

abstract final class KefeColorTokens {
  static const backgroundDark = Color(0xFF0B132B);
  static const surfaceDark = Color(0xFF1C2541);
  static const rules = Color(0xFF5B7C99);
  static const empathy = Color(0xFFF4A261);
  static const attention = Color(0xFFE63946);
  static const backgroundLight = Color(0xFFF7F8FC);
  static const surfaceLight = Colors.white;
  static const textDark = Color(0xFF111827);
  static const textLight = Color(0xFFF9FAFB);
}

abstract final class KefeTheme {
  static ThemeData light() => _build(
        brightness: Brightness.light,
        background: KefeColorTokens.backgroundLight,
        surface: KefeColorTokens.surfaceLight,
        foreground: KefeColorTokens.textDark,
      );

  static ThemeData dark() => _build(
        brightness: Brightness.dark,
        background: KefeColorTokens.backgroundDark,
        surface: KefeColorTokens.surfaceDark,
        foreground: KefeColorTokens.textLight,
      );

  static ThemeData _build({
    required Brightness brightness,
    required Color background,
    required Color surface,
    required Color foreground,
  }) {
    final scheme = ColorScheme.fromSeed(
      seedColor: KefeColorTokens.empathy,
      brightness: brightness,
      surface: surface,
    ).copyWith(
      primary: KefeColorTokens.empathy,
      secondary: KefeColorTokens.rules,
      error: KefeColorTokens.attention,
      onSurface: foreground,
    );

    return ThemeData(
      useMaterial3: true,
      brightness: brightness,
      colorScheme: scheme,
      scaffoldBackgroundColor: background,
      cardTheme: CardThemeData(
        color: surface,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size.fromHeight(52),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
      ),
      visualDensity: VisualDensity.standard,
    );
  }
}
