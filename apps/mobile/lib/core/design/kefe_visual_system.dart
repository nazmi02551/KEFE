import 'package:flutter/material.dart';

@immutable
class KefeVisualTheme extends ThemeExtension<KefeVisualTheme> {
  const KefeVisualTheme({
    required this.isDark,
    required this.canvas,
    required this.surface,
    required this.surfaceRaised,
    required this.surfaceSunken,
    required this.surfaceStrong,
    required this.onSurfaceStrong,
    required this.foreground,
    required this.mutedForeground,
    required this.border,
    required this.borderStrong,
    required this.gold,
    required this.goldSoft,
    required this.rules,
    required this.empathy,
    required this.attention,
    required this.success,
    required this.burgundy,
    required this.shadow,
  });

  final bool isDark;
  final Color canvas;
  final Color surface;
  final Color surfaceRaised;
  final Color surfaceSunken;
  final Color surfaceStrong;
  final Color onSurfaceStrong;
  final Color foreground;
  final Color mutedForeground;
  final Color border;
  final Color borderStrong;
  final Color gold;
  final Color goldSoft;
  final Color rules;
  final Color empathy;
  final Color attention;
  final Color success;
  final Color burgundy;
  final Color shadow;

  static const light = KefeVisualTheme(
    isDark: false,
    canvas: Color(0xFFF4F6FA),
    surface: Color(0xFFFFFFFF),
    surfaceRaised: Color(0xFFFBFCFF),
    surfaceSunken: Color(0xFFF0F3F8),
    surfaceStrong: Color(0xFF0A1728),
    onSurfaceStrong: Color(0xFFF8FAFC),
    foreground: Color(0xFF101827),
    mutedForeground: Color(0xFF67778B),
    border: Color(0xFFD9E1EC),
    borderStrong: Color(0xFFBCC8D8),
    gold: Color(0xFFDBA63F),
    goldSoft: Color(0xFFEFC56A),
    rules: Color(0xFF3B8EF3),
    empathy: Color(0xFFE96773),
    attention: Color(0xFFF1A93A),
    success: Color(0xFF2FAE7D),
    burgundy: Color(0xFF6F2B3A),
    shadow: Color(0xFF07111F),
  );

  static const dark = KefeVisualTheme(
    isDark: true,
    canvas: Color(0xFF06101D),
    surface: Color(0xFF0C1827),
    surfaceRaised: Color(0xFF122238),
    surfaceSunken: Color(0xFF091421),
    surfaceStrong: Color(0xFF07111F),
    onSurfaceStrong: Color(0xFFF8FAFC),
    foreground: Color(0xFFF8FAFC),
    mutedForeground: Color(0xFFA7B7CA),
    border: Color(0xFF263A52),
    borderStrong: Color(0xFF3A516E),
    gold: Color(0xFFD9A441),
    goldSoft: Color(0xFFF0C56A),
    rules: Color(0xFF58A6FF),
    empathy: Color(0xFFF06A78),
    attention: Color(0xFFFFB84D),
    success: Color(0xFF4FD19B),
    burgundy: Color(0xFF7B3143),
    shadow: Color(0xFF00050B),
  );

  List<Color> get premiumGradient => isDark
      ? const [Color(0xFF102B4B), Color(0xFF0A1626), Color(0xFF381D29)]
      : const [Color(0xFF122F51), Color(0xFF0B1728), Color(0xFF45202D)];

  List<Color> get balanceGradient => isDark
      ? [
          rules.withValues(alpha: 0.16),
          surfaceRaised,
          empathy.withValues(alpha: 0.14),
        ]
      : [
          rules.withValues(alpha: 0.11),
          const Color(0xFFF8FAFD),
          empathy.withValues(alpha: 0.10),
        ];

  Color get subtleGoldSurface => gold.withValues(alpha: isDark ? 0.12 : 0.09);
  Color get subtleRulesSurface => rules.withValues(alpha: isDark ? 0.14 : 0.09);
  Color get subtleEmpathySurface => empathy.withValues(alpha: isDark ? 0.14 : 0.09);

  @override
  KefeVisualTheme copyWith({
    bool? isDark,
    Color? canvas,
    Color? surface,
    Color? surfaceRaised,
    Color? surfaceSunken,
    Color? surfaceStrong,
    Color? onSurfaceStrong,
    Color? foreground,
    Color? mutedForeground,
    Color? border,
    Color? borderStrong,
    Color? gold,
    Color? goldSoft,
    Color? rules,
    Color? empathy,
    Color? attention,
    Color? success,
    Color? burgundy,
    Color? shadow,
  }) {
    return KefeVisualTheme(
      isDark: isDark ?? this.isDark,
      canvas: canvas ?? this.canvas,
      surface: surface ?? this.surface,
      surfaceRaised: surfaceRaised ?? this.surfaceRaised,
      surfaceSunken: surfaceSunken ?? this.surfaceSunken,
      surfaceStrong: surfaceStrong ?? this.surfaceStrong,
      onSurfaceStrong: onSurfaceStrong ?? this.onSurfaceStrong,
      foreground: foreground ?? this.foreground,
      mutedForeground: mutedForeground ?? this.mutedForeground,
      border: border ?? this.border,
      borderStrong: borderStrong ?? this.borderStrong,
      gold: gold ?? this.gold,
      goldSoft: goldSoft ?? this.goldSoft,
      rules: rules ?? this.rules,
      empathy: empathy ?? this.empathy,
      attention: attention ?? this.attention,
      success: success ?? this.success,
      burgundy: burgundy ?? this.burgundy,
      shadow: shadow ?? this.shadow,
    );
  }

  @override
  KefeVisualTheme lerp(covariant KefeVisualTheme? other, double t) {
    if (other == null) return this;
    return KefeVisualTheme(
      isDark: t < 0.5 ? isDark : other.isDark,
      canvas: Color.lerp(canvas, other.canvas, t)!,
      surface: Color.lerp(surface, other.surface, t)!,
      surfaceRaised: Color.lerp(surfaceRaised, other.surfaceRaised, t)!,
      surfaceSunken: Color.lerp(surfaceSunken, other.surfaceSunken, t)!,
      surfaceStrong: Color.lerp(surfaceStrong, other.surfaceStrong, t)!,
      onSurfaceStrong: Color.lerp(onSurfaceStrong, other.onSurfaceStrong, t)!,
      foreground: Color.lerp(foreground, other.foreground, t)!,
      mutedForeground: Color.lerp(mutedForeground, other.mutedForeground, t)!,
      border: Color.lerp(border, other.border, t)!,
      borderStrong: Color.lerp(borderStrong, other.borderStrong, t)!,
      gold: Color.lerp(gold, other.gold, t)!,
      goldSoft: Color.lerp(goldSoft, other.goldSoft, t)!,
      rules: Color.lerp(rules, other.rules, t)!,
      empathy: Color.lerp(empathy, other.empathy, t)!,
      attention: Color.lerp(attention, other.attention, t)!,
      success: Color.lerp(success, other.success, t)!,
      burgundy: Color.lerp(burgundy, other.burgundy, t)!,
      shadow: Color.lerp(shadow, other.shadow, t)!,
    );
  }
}

extension KefeVisualThemeContext on BuildContext {
  KefeVisualTheme get kefeVisual =>
      Theme.of(this).extension<KefeVisualTheme>() ??
      (Theme.of(this).brightness == Brightness.dark
          ? KefeVisualTheme.dark
          : KefeVisualTheme.light);
}

abstract final class KefeMotion {
  static Duration resolve(BuildContext context, Duration preferred) {
    final media = MediaQuery.maybeOf(context);
    if (media?.disableAnimations == true || media?.accessibleNavigation == true) {
      return Duration.zero;
    }
    return preferred;
  }
}
