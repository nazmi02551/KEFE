import 'package:flutter/material.dart';

import 'kefe_visual_system.dart';

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
  static ThemeData light() =>
      _build(brightness: Brightness.light, visual: KefeVisualTheme.light);

  static ThemeData dark() =>
      _build(brightness: Brightness.dark, visual: KefeVisualTheme.dark);

  static ThemeData _build({
    required Brightness brightness,
    required KefeVisualTheme visual,
  }) {
    final scheme =
        ColorScheme.fromSeed(
          seedColor: visual.gold,
          brightness: brightness,
          surface: visual.surface,
        ).copyWith(
          primary: visual.gold,
          secondary: visual.rules,
          tertiary: visual.empathy,
          error: const Color(0xFFFF6B6B),
          onSurface: visual.foreground,
          outline: visual.border,
          outlineVariant: visual.border.withValues(alpha: 0.72),
        );

    return ThemeData(
      useMaterial3: true,
      brightness: brightness,
      colorScheme: scheme,
      scaffoldBackgroundColor: visual.canvas,
      canvasColor: visual.canvas,
      extensions: [visual],
      appBarTheme: AppBarTheme(
        backgroundColor: visual.canvas,
        foregroundColor: visual.foreground,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        surfaceTintColor: Colors.transparent,
      ),
      cardTheme: CardThemeData(
        color: visual.surface,
        elevation: 0,
        margin: EdgeInsets.zero,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(22),
          side: BorderSide(color: visual.border.withValues(alpha: 0.78)),
        ),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: visual.surfaceRaised,
        selectedColor: visual.gold.withValues(
          alpha: visual.isDark ? 0.18 : 0.13,
        ),
        side: BorderSide(color: visual.border.withValues(alpha: 0.82)),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
        labelStyle: TextStyle(color: visual.foreground),
      ),
      navigationBarTheme: NavigationBarThemeData(
        height: 72,
        backgroundColor: visual.isDark
            ? const Color(0xFF081420)
            : visual.surface,
        indicatorColor: visual.gold.withValues(
          alpha: visual.isDark ? 0.18 : 0.13,
        ),
        elevation: 0,
        labelTextStyle: WidgetStateProperty.resolveWith(
          (states) => TextStyle(
            fontSize: 11,
            fontWeight: states.contains(WidgetState.selected)
                ? FontWeight.w700
                : FontWeight.w500,
            color: states.contains(WidgetState.selected)
                ? (visual.isDark ? visual.goldSoft : const Color(0xFFA8771E))
                : visual.mutedForeground,
          ),
        ),
        iconTheme: WidgetStateProperty.resolveWith(
          (states) => IconThemeData(
            color: states.contains(WidgetState.selected)
                ? (visual.isDark ? visual.goldSoft : const Color(0xFFA8771E))
                : visual.mutedForeground,
          ),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size.fromHeight(56),
          backgroundColor: visual.gold,
          foregroundColor: const Color(0xFF171106),
          textStyle: const TextStyle(
            fontWeight: FontWeight.w800,
            letterSpacing: 0.2,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(17),
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size.fromHeight(50),
          foregroundColor: visual.foreground,
          side: BorderSide(color: visual.borderStrong),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
      ),
      dividerTheme: DividerThemeData(
        color: visual.border.withValues(alpha: 0.72),
      ),
      textTheme: ThemeData(brightness: brightness).textTheme.apply(
        bodyColor: visual.foreground,
        displayColor: visual.foreground,
      ),
      visualDensity: VisualDensity.standard,
    );
  }
}
