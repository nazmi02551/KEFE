import 'package:flutter/material.dart';

abstract final class KefeColorTokens {
  static const backgroundDark = Color(0xFF07111F);
  static const surfaceDark = Color(0xFF0E1A2A);
  static const surfaceElevatedDark = Color(0xFF142235);
  static const surfaceSoftDark = Color(0xFF182A40);
  static const borderDark = Color(0xFF263A52);

  static const gold = Color(0xFFD9A441);
  static const goldSoft = Color(0xFFF0C56A);
  static const rules = Color(0xFF4E8DFF);
  static const empathy = Color(0xFFE65E68);
  static const attention = Color(0xFFFFB84D);
  static const success = Color(0xFF4FD19B);

  static const backgroundLight = Color(0xFFF7F8FC);
  static const surfaceLight = Colors.white;
  static const textDark = Color(0xFF111827);
  static const textLight = Color(0xFFF8FAFC);
  static const textMutedDark = Color(0xFF9FB0C4);
}

abstract final class KefeTheme {
  static ThemeData light() => _build(
        brightness: Brightness.light,
        background: KefeColorTokens.backgroundLight,
        surface: KefeColorTokens.surfaceLight,
        foreground: KefeColorTokens.textDark,
        outline: const Color(0xFFD8DEE8),
      );

  static ThemeData dark() => _build(
        brightness: Brightness.dark,
        background: KefeColorTokens.backgroundDark,
        surface: KefeColorTokens.surfaceDark,
        foreground: KefeColorTokens.textLight,
        outline: KefeColorTokens.borderDark,
      );

  static ThemeData _build({
    required Brightness brightness,
    required Color background,
    required Color surface,
    required Color foreground,
    required Color outline,
  }) {
    final scheme = ColorScheme.fromSeed(
      seedColor: KefeColorTokens.gold,
      brightness: brightness,
      surface: surface,
    ).copyWith(
      primary: KefeColorTokens.gold,
      secondary: KefeColorTokens.rules,
      tertiary: KefeColorTokens.empathy,
      error: const Color(0xFFFF6B6B),
      onSurface: foreground,
      outline: outline,
      outlineVariant: outline.withValues(alpha: 0.7),
    );

    final isDark = brightness == Brightness.dark;

    return ThemeData(
      useMaterial3: true,
      brightness: brightness,
      colorScheme: scheme,
      scaffoldBackgroundColor: background,
      canvasColor: background,
      appBarTheme: AppBarTheme(
        backgroundColor: background,
        foregroundColor: foreground,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        surfaceTintColor: Colors.transparent,
      ),
      cardTheme: CardThemeData(
        color: surface,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: BorderSide(color: outline.withValues(alpha: isDark ? 0.72 : 0.5)),
        ),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: isDark ? KefeColorTokens.surfaceElevatedDark : surface,
        selectedColor: KefeColorTokens.gold.withValues(alpha: 0.18),
        side: BorderSide(color: outline.withValues(alpha: 0.7)),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
        labelStyle: TextStyle(color: foreground),
      ),
      navigationBarTheme: NavigationBarThemeData(
        height: 70,
        backgroundColor: isDark ? const Color(0xFF091522) : surface,
        indicatorColor: KefeColorTokens.gold.withValues(alpha: 0.18),
        labelTextStyle: WidgetStateProperty.resolveWith(
          (states) => TextStyle(
            fontSize: 11,
            fontWeight: states.contains(WidgetState.selected)
                ? FontWeight.w700
                : FontWeight.w500,
            color: states.contains(WidgetState.selected)
                ? KefeColorTokens.goldSoft
                : (isDark ? KefeColorTokens.textMutedDark : foreground.withValues(alpha: 0.68)),
          ),
        ),
        iconTheme: WidgetStateProperty.resolveWith(
          (states) => IconThemeData(
            color: states.contains(WidgetState.selected)
                ? KefeColorTokens.goldSoft
                : (isDark ? KefeColorTokens.textMutedDark : foreground.withValues(alpha: 0.68)),
          ),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size.fromHeight(54),
          backgroundColor: KefeColorTokens.gold,
          foregroundColor: const Color(0xFF171106),
          textStyle: const TextStyle(fontWeight: FontWeight.w800, letterSpacing: 0.2),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size.fromHeight(50),
          side: BorderSide(color: outline),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
      ),
      dividerTheme: DividerThemeData(color: outline.withValues(alpha: 0.7)),
      textTheme: ThemeData(brightness: brightness).textTheme.apply(
            bodyColor: foreground,
            displayColor: foreground,
          ),
      visualDensity: VisualDensity.standard,
    );
  }
}
