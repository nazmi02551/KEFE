import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';

class KefeBalanceVisual extends StatelessWidget {
  const KefeBalanceVisual({
    required this.leftLabel,
    required this.rightLabel,
    this.selectedIndex,
    this.compact = false,
    super.key,
  });

  final String leftLabel;
  final String rightLabel;
  final int? selectedIndex;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final selectedLabel = switch (selectedIndex) {
      0 => leftLabel,
      1 => rightLabel,
      _ => strings.balanceNoSelection,
    };
    final targetTilt = switch (selectedIndex) {
      0 => -1.0,
      1 => 1.0,
      _ => 0.0,
    };
    final duration = KefeMotion.resolve(
      context,
      const Duration(milliseconds: 360),
    );

    return Semantics(
      image: true,
      label: strings.balanceSemantics(selectedLabel),
      child: Container(
        key: const ValueKey('kefe-balance-visual'),
        padding: EdgeInsets.fromLTRB(14, compact ? 10 : 16, 14, 12),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(compact ? 20 : 24),
          border: Border.all(
            color: visual.gold.withValues(alpha: visual.isDark ? 0.30 : 0.24),
          ),
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: visual.balanceGradient,
          ),
          boxShadow: [
            BoxShadow(
              color: visual.shadow.withValues(
                alpha: visual.isDark ? 0.18 : 0.07,
              ),
              blurRadius: compact ? 16 : 24,
              offset: const Offset(0, 10),
            ),
            if (selectedIndex != null)
              BoxShadow(
                color: (selectedIndex == 0 ? visual.rules : visual.empathy)
                    .withValues(alpha: 0.09),
                blurRadius: 26,
                spreadRadius: 1,
              ),
          ],
        ),
        child: Column(
          children: [
            SizedBox(
              height: compact ? 94 : 132,
              width: double.infinity,
              child: TweenAnimationBuilder<double>(
                duration: duration,
                curve: Curves.easeOutCubic,
                tween: Tween<double>(end: targetTilt),
                builder: (context, tilt, _) {
                  return CustomPaint(
                    painter: _KefeBalancePainter(
                      tilt: tilt,
                      selectedIndex: selectedIndex,
                      visual: visual,
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 6),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: _SideLabel(
                    label: leftLabel,
                    color: visual.rules,
                    selected: selectedIndex == 0,
                    alignment: TextAlign.left,
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 10),
                  child: AnimatedContainer(
                    duration: duration,
                    curve: Curves.easeOutCubic,
                    width: 34,
                    height: 24,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(999),
                      color: visual.gold.withValues(
                        alpha: selectedIndex == null ? 0.07 : 0.14,
                      ),
                      border: Border.all(
                        color: visual.gold.withValues(alpha: 0.28),
                      ),
                    ),
                    child: Text(
                      '≠',
                      style: TextStyle(
                        color: visual.goldSoft,
                        fontSize: 15,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                ),
                Expanded(
                  child: _SideLabel(
                    label: rightLabel,
                    color: visual.empathy,
                    selected: selectedIndex == 1,
                    alignment: TextAlign.right,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _SideLabel extends StatelessWidget {
  const _SideLabel({
    required this.label,
    required this.color,
    required this.selected,
    required this.alignment,
  });

  final String label;
  final Color color;
  final bool selected;
  final TextAlign alignment;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    return AnimatedDefaultTextStyle(
      duration: KefeMotion.resolve(context, const Duration(milliseconds: 220)),
      curve: Curves.easeOutCubic,
      style: Theme.of(context).textTheme.labelMedium!.copyWith(
        color: selected ? color : visual.mutedForeground,
        fontWeight: selected ? FontWeight.w900 : FontWeight.w700,
        height: 1.25,
      ),
      child: Text(
        label,
        textAlign: alignment,
        maxLines: 2,
        overflow: TextOverflow.ellipsis,
      ),
    );
  }
}

class _KefeBalancePainter extends CustomPainter {
  const _KefeBalancePainter({
    required this.tilt,
    required this.selectedIndex,
    required this.visual,
  });

  final double tilt;
  final int? selectedIndex;
  final KefeVisualTheme visual;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height * 0.30);
    final halfBeam = size.width * 0.31;
    final delta = tilt * size.height * 0.065;
    final left = Offset(center.dx - halfBeam, center.dy - delta);
    final right = Offset(center.dx + halfBeam, center.dy + delta);
    final selectedColor = selectedIndex == 0
        ? visual.rules
        : selectedIndex == 1
        ? visual.empathy
        : visual.gold;

    _drawAmbientArc(canvas, size, selectedColor);

    final glowPaint = Paint()
      ..color = visual.goldSoft.withValues(alpha: 0.13)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 12)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 7;
    final goldPaint = Paint()
      ..shader = LinearGradient(
        colors: [visual.gold, visual.goldSoft, visual.gold],
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height))
      ..strokeWidth = 3.4
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.stroke;
    final chainPaint = Paint()
      ..color = visual.gold.withValues(alpha: visual.isDark ? 0.66 : 0.54)
      ..strokeWidth = 1.7
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.stroke;

    final baseY = size.height * 0.90;
    final pedestalTop = center.dy + 3;
    final baseHalf = size.width * 0.16;

    canvas.drawLine(
      Offset(center.dx, pedestalTop),
      Offset(center.dx, baseY - 10),
      glowPaint,
    );
    canvas.drawLine(
      Offset(center.dx, pedestalTop),
      Offset(center.dx, baseY - 10),
      goldPaint,
    );
    canvas.drawLine(
      Offset(center.dx - baseHalf, baseY),
      Offset(center.dx + baseHalf, baseY),
      glowPaint,
    );
    canvas.drawLine(
      Offset(center.dx - baseHalf, baseY),
      Offset(center.dx + baseHalf, baseY),
      goldPaint,
    );

    final medallionRadius = size.height * 0.075;
    canvas.drawCircle(
      center,
      medallionRadius + 6,
      Paint()
        ..color = selectedColor.withValues(alpha: 0.12)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 11),
    );
    canvas.drawCircle(
      center,
      medallionRadius,
      Paint()
        ..shader =
            RadialGradient(
              colors: [visual.goldSoft, visual.gold, visual.surfaceStrong],
              stops: const [0.0, 0.46, 1.0],
            ).createShader(
              Rect.fromCircle(center: center, radius: medallionRadius),
            ),
    );
    canvas.drawCircle(
      center,
      medallionRadius,
      Paint()
        ..color = visual.goldSoft.withValues(alpha: 0.82)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.4,
    );

    canvas.drawLine(left, right, glowPaint);
    canvas.drawLine(left, right, goldPaint);

    _drawPan(
      canvas,
      anchor: left,
      size: size,
      color: visual.rules,
      selected: selectedIndex == 0,
      chainPaint: chainPaint,
    );
    _drawPan(
      canvas,
      anchor: right,
      size: size,
      color: visual.empathy,
      selected: selectedIndex == 1,
      chainPaint: chainPaint,
    );
  }

  void _drawAmbientArc(Canvas canvas, Size size, Color accent) {
    final rect = Rect.fromCenter(
      center: Offset(size.width / 2, size.height * 0.52),
      width: size.width * 0.78,
      height: size.height * 0.90,
    );
    canvas.drawArc(
      rect,
      math.pi * 1.08,
      math.pi * 0.84,
      false,
      Paint()
        ..color = accent.withValues(alpha: 0.055)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 18
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 16),
    );
  }

  void _drawPan(
    Canvas canvas, {
    required Offset anchor,
    required Size size,
    required Color color,
    required bool selected,
    required Paint chainPaint,
  }) {
    final chain = size.height * 0.25;
    final panY = anchor.dy + chain;
    final panHalfWidth = size.width * 0.115;

    canvas.drawLine(
      anchor,
      Offset(anchor.dx - panHalfWidth * 0.72, panY),
      chainPaint,
    );
    canvas.drawLine(
      anchor,
      Offset(anchor.dx + panHalfWidth * 0.72, panY),
      chainPaint,
    );

    if (selected) {
      canvas.drawCircle(
        Offset(anchor.dx, panY + size.height * 0.025),
        panHalfWidth * 1.18,
        Paint()
          ..color = color.withValues(alpha: 0.16)
          ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 13),
      );
    }

    final fill = Paint()
      ..color = color.withValues(alpha: selected ? 0.28 : 0.09)
      ..style = PaintingStyle.fill;
    final outline = Paint()
      ..color = color.withValues(alpha: selected ? 0.98 : 0.58)
      ..strokeWidth = selected ? 2.35 : 1.45
      ..style = PaintingStyle.stroke;

    final rect = Rect.fromCenter(
      center: Offset(anchor.dx, panY),
      width: panHalfWidth * 2,
      height: size.height * 0.14,
    );
    final panPath = Path()
      ..moveTo(rect.left, rect.top)
      ..quadraticBezierTo(
        rect.center.dx,
        rect.bottom + size.height * 0.085,
        rect.right,
        rect.top,
      )
      ..close();

    canvas.drawPath(panPath, fill);
    canvas.drawPath(panPath, outline);
  }

  @override
  bool shouldRepaint(covariant _KefeBalancePainter oldDelegate) =>
      oldDelegate.tilt != tilt ||
      oldDelegate.selectedIndex != selectedIndex ||
      oldDelegate.visual != visual;
}
