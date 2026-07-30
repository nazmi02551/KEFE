import 'package:flutter/material.dart';

import 'kefe_visual_system.dart';

enum KefeSurfaceTone { standard, raised, sunken, premium }

class KefeSurface extends StatelessWidget {
  const KefeSurface({
    required this.child,
    this.tone = KefeSurfaceTone.standard,
    this.padding = const EdgeInsets.all(18),
    this.borderRadius = 22,
    this.accent,
    this.semanticContainer = true,
    super.key,
  });

  final Widget child;
  final KefeSurfaceTone tone;
  final EdgeInsetsGeometry padding;
  final double borderRadius;
  final Color? accent;
  final bool semanticContainer;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final premium = tone == KefeSurfaceTone.premium;
    final background = switch (tone) {
      KefeSurfaceTone.standard => visual.surface,
      KefeSurfaceTone.raised => visual.surfaceRaised,
      KefeSurfaceTone.sunken => visual.surfaceSunken,
      KefeSurfaceTone.premium => visual.surfaceStrong,
    };
    final resolvedAccent = accent ?? visual.gold;

    return Semantics(
      container: semanticContainer,
      child: Container(
        padding: padding,
        decoration: BoxDecoration(
          color: premium ? null : background,
          gradient: premium
              ? LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: visual.premiumGradient,
                )
              : null,
          borderRadius: BorderRadius.circular(borderRadius),
          border: Border.all(
            color: premium
                ? resolvedAccent.withValues(alpha: 0.34)
                : visual.border.withValues(alpha: 0.88),
          ),
          boxShadow: [
            BoxShadow(
              color: visual.shadow.withValues(alpha: premium ? 0.20 : 0.07),
              blurRadius: premium ? 28 : 14,
              offset: Offset(0, premium ? 12 : 6),
            ),
            if (premium)
              BoxShadow(
                color: resolvedAccent.withValues(alpha: 0.08),
                blurRadius: 34,
                spreadRadius: 1,
              ),
          ],
        ),
        child: premium
            ? DefaultTextStyle.merge(
                style: TextStyle(color: visual.onSurfaceStrong),
                child: IconTheme.merge(
                  data: IconThemeData(color: visual.onSurfaceStrong),
                  child: child,
                ),
              )
            : child,
      ),
    );
  }
}

class KefeEyebrow extends StatelessWidget {
  const KefeEyebrow(
    this.text, {
    this.color,
    this.icon,
    super.key,
  });

  final String text;
  final Color? color;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final resolvedColor = color ?? context.kefeVisual.goldSoft;
    final label = Text(
      text,
      style: Theme.of(context).textTheme.labelMedium?.copyWith(
        color: resolvedColor,
        fontWeight: FontWeight.w900,
        letterSpacing: 0.9,
      ),
    );
    if (icon == null) return label;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 16, color: resolvedColor),
        const SizedBox(width: 7),
        Flexible(child: label),
      ],
    );
  }
}
