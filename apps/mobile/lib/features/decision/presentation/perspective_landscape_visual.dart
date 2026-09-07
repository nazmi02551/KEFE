import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/decision_models.dart';

class PerspectiveLandscapeVisual extends StatelessWidget {
  const PerspectiveLandscapeVisual({required this.slots, super.key});

  final List<PerspectiveSlot> slots;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final textScale = MediaQuery.textScalerOf(context).scale(1);
    final mediaSize = MediaQuery.sizeOf(context);
    final compact = mediaSize.width < 340 || mediaSize.height < 700;
    final presentSlots = _uniqueSlots(slots);

    return ExcludeSemantics(
      child: KefeSurface(
        key: const ValueKey('perspective-landscape'),
        tone: KefeSurfaceTone.premium,
        accent: visual.gold,
        padding: EdgeInsets.fromLTRB(
          compact ? 10 : 14,
          compact ? 10 : 14,
          compact ? 10 : 14,
          compact ? 10 : 12,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            SizedBox(
              key: const ValueKey('perspective-landscape-canvas'),
              height: compact ? 176 : 226,
              child: RepaintBoundary(
                child: CustomPaint(
                  painter: _PerspectiveLandscapePainter(
                    visual: visual,
                    presentSlots: presentSlots.toSet(),
                  ),
                ),
              ),
            ),
            SizedBox(height: compact ? 5 : 8),
            _SlotLegend(
              slots: presentSlots,
              compact: compact,
              enlargedText: textScale > 1.28,
            ),
          ],
        ),
      ),
    );
  }
}

class _SlotLegend extends StatelessWidget {
  const _SlotLegend({
    required this.slots,
    required this.compact,
    required this.enlargedText,
  });

  final List<PerspectiveSlot> slots;
  final bool compact;
  final bool enlargedText;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;

    return Wrap(
      alignment: WrapAlignment.center,
      spacing: compact ? 6 : 8,
      runSpacing: 7,
      children: [
        for (final slot in slots)
          Container(
            key: ValueKey('perspective-landscape-slot-${slot.name}'),
            constraints: BoxConstraints(
              minHeight: enlargedText ? 38 : 30,
              maxWidth: enlargedText ? double.infinity : 180,
            ),
            padding: EdgeInsets.symmetric(
              horizontal: compact ? 9 : 11,
              vertical: enlargedText ? 8 : 6,
            ),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(999),
              color: _slotColor(
                visual,
                slot,
              ).withValues(alpha: visual.isDark ? 0.11 : 0.07),
              border: Border.all(
                color: _slotColor(visual, slot).withValues(alpha: 0.30),
              ),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  _slotIcon(slot),
                  size: enlargedText ? 17 : 14,
                  color: _slotColor(visual, slot),
                ),
                const SizedBox(width: 6),
                Flexible(
                  child: Text(
                    strings.perspectiveSlotLabel(slot),
                    maxLines: enlargedText ? 2 : 1,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: visual.onSurfaceStrong,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }
}

class _PerspectiveLandscapePainter extends CustomPainter {
  const _PerspectiveLandscapePainter({
    required this.visual,
    required this.presentSlots,
  });

  final KefeVisualTheme visual;
  final Set<PerspectiveSlot> presentSlots;

  static const _slotAnchors = <PerspectiveSlot, Offset>{
    PerspectiveSlot.near: Offset(0.22, 0.56),
    PerspectiveSlot.bridge: Offset(0.47, 0.38),
    PerspectiveSlot.alternativeContext: Offset(0.66, 0.58),
    PerspectiveSlot.opposing: Offset(0.80, 0.43),
  };

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    final center = rect.center;

    canvas.drawRect(
      rect,
      Paint()
        ..shader = LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            visual.rules.withValues(alpha: visual.isDark ? 0.08 : 0.045),
            Colors.transparent,
            visual.gold.withValues(alpha: visual.isDark ? 0.07 : 0.04),
            visual.empathy.withValues(alpha: visual.isDark ? 0.07 : 0.04),
          ],
          stops: const [0.0, 0.36, 0.66, 1.0],
        ).createShader(rect),
    );

    final horizon = size.height * 0.78;
    canvas.drawOval(
      Rect.fromCenter(
        center: Offset(center.dx, horizon),
        width: size.width * 0.92,
        height: size.height * 0.20,
      ),
      Paint()
        ..color = visual.gold.withValues(alpha: visual.isDark ? 0.055 : 0.035)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 18),
    );

    for (var layer = 0; layer < 8; layer++) {
      final normalizedLayer = layer / 7;
      final yBase = size.height * (0.83 - normalizedLayer * 0.055);
      final terrain = _terrainPath(
        size,
        baseline: yBase,
        amplitudeScale: 1 - normalizedLayer * 0.065,
      );
      final alpha =
          (visual.isDark ? 0.24 : 0.18) * (1 - normalizedLayer * 0.55);
      final lineColor = Color.lerp(
        visual.rules,
        visual.goldSoft,
        normalizedLayer,
      )!.withValues(alpha: alpha);
      canvas.drawPath(
        terrain,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = layer == 0 ? 1.35 : 0.72
          ..color = lineColor,
      );
    }

    final frontTerrain = _terrainPath(
      size,
      baseline: size.height * 0.83,
      amplitudeScale: 1,
    );
    final fillPath = Path.from(frontTerrain)
      ..lineTo(size.width, size.height)
      ..lineTo(0, size.height)
      ..close();
    canvas.drawPath(
      fillPath,
      Paint()
        ..shader = LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            visual.rules.withValues(alpha: visual.isDark ? 0.10 : 0.07),
            visual.surfaceSunken.withValues(alpha: 0.18),
          ],
        ).createShader(rect),
    );

    _drawMesh(canvas, size);
    _drawSlotBeacons(canvas, size);

    canvas.drawCircle(
      Offset(size.width * 0.5, size.height * 0.50),
      size.shortestSide * 0.40,
      Paint()
        ..shader =
            RadialGradient(
              colors: [
                visual.gold.withValues(alpha: visual.isDark ? 0.045 : 0.025),
                Colors.transparent,
              ],
            ).createShader(
              Rect.fromCircle(
                center: Offset(size.width * 0.5, size.height * 0.50),
                radius: size.shortestSide * 0.40,
              ),
            ),
    );
  }

  Path _terrainPath(
    Size size, {
    required double baseline,
    required double amplitudeScale,
  }) {
    const segments = 72;
    final path = Path();
    for (var i = 0; i <= segments; i++) {
      final xNorm = i / segments;
      final x = size.width * xNorm;
      var elevation = 0.0;
      for (final entry in _slotAnchors.entries) {
        if (!presentSlots.contains(entry.key)) continue;
        final anchor = entry.value;
        final dx = xNorm - anchor.dx;
        final width = switch (entry.key) {
          PerspectiveSlot.near => 0.13,
          PerspectiveSlot.bridge => 0.11,
          PerspectiveSlot.alternativeContext => 0.12,
          PerspectiveSlot.opposing => 0.13,
        };
        final baseAmplitude = (0.79 - anchor.dy) * size.height * 1.08;
        elevation +=
            baseAmplitude *
            math.exp(-(dx * dx) / (2 * width * width)) *
            amplitudeScale;
      }
      final ripple =
          math.sin(xNorm * math.pi * 6.0) *
          size.height *
          0.008 *
          amplitudeScale;
      final y = baseline - elevation - ripple;
      if (i == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
    }
    return path;
  }

  void _drawMesh(Canvas canvas, Size size) {
    final meshPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 0.6
      ..color = visual.rules.withValues(alpha: visual.isDark ? 0.095 : 0.065);

    for (var row = 0; row < 6; row++) {
      final y = size.height * (0.48 + row * 0.075);
      canvas.drawPath(
        Path()
          ..moveTo(size.width * 0.04, y)
          ..quadraticBezierTo(
            size.width * 0.50,
            y - size.height * 0.055,
            size.width * 0.96,
            y,
          ),
        meshPaint,
      );
    }
    for (var column = 1; column < 10; column++) {
      final x = size.width * column / 10;
      canvas.drawLine(
        Offset(x, size.height * 0.47),
        Offset(x, size.height * 0.87),
        meshPaint,
      );
    }
  }

  void _drawSlotBeacons(Canvas canvas, Size size) {
    for (final entry in _slotAnchors.entries) {
      if (!presentSlots.contains(entry.key)) continue;
      final color = _slotColor(visual, entry.key);
      final anchor = Offset(
        size.width * entry.value.dx,
        size.height * entry.value.dy,
      );
      final glowRadius = size.shortestSide * 0.055;

      canvas.drawCircle(
        anchor,
        glowRadius,
        Paint()
          ..color = color.withValues(alpha: visual.isDark ? 0.14 : 0.09)
          ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 12),
      );
      canvas.drawLine(
        Offset(anchor.dx, anchor.dy + 2),
        Offset(anchor.dx, size.height * 0.80),
        Paint()
          ..strokeWidth = 0.8
          ..color = color.withValues(alpha: 0.30),
      );
      canvas.drawCircle(
        anchor,
        5.5,
        Paint()..color = color.withValues(alpha: 0.95),
      );
      canvas.drawCircle(
        anchor,
        9.0,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.2
          ..color = color.withValues(alpha: 0.48),
      );
    }
  }

  @override
  bool shouldRepaint(covariant _PerspectiveLandscapePainter oldDelegate) =>
      oldDelegate.visual != visual ||
      !_setEquals(oldDelegate.presentSlots, presentSlots);
}

List<PerspectiveSlot> _uniqueSlots(List<PerspectiveSlot> slots) {
  final seen = <PerspectiveSlot>{};
  return [
    for (final slot in slots)
      if (seen.add(slot)) slot,
  ];
}

bool _setEquals(Set<PerspectiveSlot> a, Set<PerspectiveSlot> b) =>
    a.length == b.length && a.containsAll(b);

Color _slotColor(KefeVisualTheme visual, PerspectiveSlot slot) =>
    switch (slot) {
      PerspectiveSlot.near => visual.success,
      PerspectiveSlot.opposing => visual.empathy,
      PerspectiveSlot.bridge => visual.gold,
      PerspectiveSlot.alternativeContext => visual.rules,
    };

IconData _slotIcon(PerspectiveSlot slot) => switch (slot) {
  PerspectiveSlot.near => Icons.near_me_outlined,
  PerspectiveSlot.opposing => Icons.swap_horiz_rounded,
  PerspectiveSlot.bridge => Icons.hub_outlined,
  PerspectiveSlot.alternativeContext => Icons.change_circle_outlined,
};
