import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../../../core/visual_composition/kefe_visual_composition_flutter.dart';
import '../../../core/visual_composition/kefe_visual_composition_models.dart';

enum KefeBalanceHeroState { neutral, leftSelected, rightSelected }

class KefeBalanceVisual extends StatelessWidget {
  const KefeBalanceVisual({
    required this.leftLabel,
    required this.rightLabel,
    this.selectedIndex,
    this.compact = false,
    super.key,
  }) : assert(selectedIndex == null || selectedIndex == 0 || selectedIndex == 1);

  final String leftLabel;
  final String rightLabel;
  final int? selectedIndex;
  final bool compact;

  KefeBalanceHeroState get heroState => switch (selectedIndex) {
    0 => KefeBalanceHeroState.leftSelected,
    1 => KefeBalanceHeroState.rightSelected,
    _ => KefeBalanceHeroState.neutral,
  };

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final selectedLabel = switch (heroState) {
      KefeBalanceHeroState.leftSelected => leftLabel,
      KefeBalanceHeroState.rightSelected => rightLabel,
      KefeBalanceHeroState.neutral => strings.balanceNoSelection,
    };
    final targetTilt = switch (heroState) {
      KefeBalanceHeroState.leftSelected => -0.72,
      KefeBalanceHeroState.rightSelected => 0.72,
      KefeBalanceHeroState.neutral => 0.0,
    };
    final duration = KefeVisualCompositionPolicy.hero.resolveMotionDuration(
      context,
      const Duration(milliseconds: 360),
    );

    return Semantics(
      image: true,
      label: strings.balanceSemantics(selectedLabel),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final compactLayout = compact || constraints.maxWidth < 300;
          return Container(
            key: const ValueKey('kefe-balance-visual'),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(compactLayout ? 20 : 26),
              border: Border.all(
                color: visual.gold.withValues(
                  alpha: visual.isDark ? 0.34 : 0.25,
                ),
              ),
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  visual.surfaceStrong,
                  Color.lerp(visual.surfaceStrong, visual.rules, 0.10)!,
                  Color.lerp(visual.surfaceStrong, visual.empathy, 0.11)!,
                ],
                stops: const [0.0, 0.48, 1.0],
              ),
              boxShadow: [
                BoxShadow(
                  color: visual.shadow.withValues(
                    alpha: visual.isDark ? 0.34 : 0.10,
                  ),
                  blurRadius: compactLayout ? 18 : 30,
                  offset: const Offset(0, 14),
                ),
                if (selectedIndex != null)
                  BoxShadow(
                    color: (selectedIndex == 0 ? visual.rules : visual.empathy)
                        .withValues(alpha: visual.isDark ? 0.12 : 0.08),
                    blurRadius: 34,
                    spreadRadius: 1,
                  ),
              ],
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(compactLayout ? 20 : 26),
              child: Stack(
                children: [
                  Positioned.fill(
                    child: CustomPaint(
                      painter: _BalanceBackdropPainter(
                        visual: visual,
                        state: heroState,
                      ),
                    ),
                  ),
                  Padding(
                    padding: EdgeInsets.fromLTRB(
                      compactLayout ? 10 : 14,
                      compactLayout ? 10 : 14,
                      compactLayout ? 10 : 14,
                      compactLayout ? 11 : 14,
                    ),
                    child: Column(
                      children: [
                        SizedBox(
                          key: const ValueKey('signature-balance-hero'),
                          height: compactLayout ? 122 : 202,
                          width: double.infinity,
                          child: TweenAnimationBuilder<double>(
                            key: ValueKey('balance-state-${heroState.name}'),
                            duration: duration,
                            curve: Curves.easeOutCubic,
                            tween: Tween<double>(end: targetTilt),
                            builder: (context, tilt, _) {
                              return RepaintBoundary(
                                child: CustomPaint(
                                  painter: _SignatureBalancePainter(
                                    tilt: tilt,
                                    state: heroState,
                                    visual: visual,
                                  ),
                                ),
                              );
                            },
                          ),
                        ),
                        SizedBox(height: compactLayout ? 4 : 7),
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Expanded(
                              child: _SideLabel(
                                label: leftLabel,
                                color: visual.rules,
                                selected:
                                    heroState ==
                                    KefeBalanceHeroState.leftSelected,
                                alignment: TextAlign.left,
                              ),
                            ),
                            Padding(
                              padding: EdgeInsets.symmetric(
                                horizontal: compactLayout ? 7 : 12,
                              ),
                              child: AnimatedContainer(
                                key: const ValueKey('balance-neutrality-mark'),
                                duration: duration,
                                curve: Curves.easeOutCubic,
                                width: compactLayout ? 31 : 38,
                                height: compactLayout ? 23 : 27,
                                alignment: Alignment.center,
                                decoration: BoxDecoration(
                                  borderRadius: BorderRadius.circular(999),
                                  color: visual.gold.withValues(
                                    alpha: selectedIndex == null ? 0.07 : 0.15,
                                  ),
                                  border: Border.all(
                                    color: visual.gold.withValues(alpha: 0.34),
                                  ),
                                  boxShadow: selectedIndex == null
                                      ? const []
                                      : [
                                          BoxShadow(
                                            color: visual.gold.withValues(
                                              alpha: 0.13,
                                            ),
                                            blurRadius: 12,
                                          ),
                                        ],
                                ),
                                child: Text(
                                  '≠',
                                  style: TextStyle(
                                    color: visual.goldSoft,
                                    fontSize: compactLayout ? 14 : 16,
                                    fontWeight: FontWeight.w900,
                                  ),
                                ),
                              ),
                            ),
                            Expanded(
                              child: _SideLabel(
                                label: rightLabel,
                                color: visual.empathy,
                                selected:
                                    heroState ==
                                    KefeBalanceHeroState.rightSelected,
                                alignment: TextAlign.right,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          );
        },
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
      duration: KefeVisualCompositionPolicy.hero.resolveMotionDuration(
        context,
        const Duration(milliseconds: 220),
      ),
      curve: Curves.easeOutCubic,
      style: Theme.of(context).textTheme.labelMedium!.copyWith(
        color: selected ? color : visual.mutedForeground,
        fontWeight: selected ? FontWeight.w900 : FontWeight.w700,
        height: 1.25,
      ),
      child: Text(
        label,
        textAlign: alignment,
        maxLines: 3,
        overflow: TextOverflow.ellipsis,
      ),
    );
  }
}

class _BalanceBackdropPainter extends CustomPainter {
  const _BalanceBackdropPainter({required this.visual, required this.state});

  final KefeVisualTheme visual;
  final KefeBalanceHeroState state;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width * 0.5, size.height * 0.52);
    final active = switch (state) {
      KefeBalanceHeroState.leftSelected => visual.rules,
      KefeBalanceHeroState.rightSelected => visual.empathy,
      KefeBalanceHeroState.neutral => visual.gold,
    };

    canvas.drawCircle(
      center,
      size.shortestSide * 0.42,
      Paint()
        ..shader = RadialGradient(
          colors: [
            active.withValues(alpha: visual.isDark ? 0.13 : 0.08),
            Colors.transparent,
          ],
        ).createShader(
          Rect.fromCircle(center: center, radius: size.shortestSide * 0.42),
        ),
    );

    final horizonY = size.height * 0.76;
    canvas.drawOval(
      Rect.fromCenter(
        center: Offset(size.width / 2, horizonY),
        width: size.width * 0.78,
        height: size.height * 0.12,
      ),
      Paint()
        ..color = visual.gold.withValues(alpha: visual.isDark ? 0.06 : 0.045)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 18),
    );

    final constellation = Paint()
      ..color = visual.goldSoft.withValues(alpha: visual.isDark ? 0.18 : 0.12)
      ..strokeWidth = 1;
    for (final point in <Offset>[
      Offset(size.width * 0.08, size.height * 0.22),
      Offset(size.width * 0.18, size.height * 0.12),
      Offset(size.width * 0.82, size.height * 0.17),
      Offset(size.width * 0.92, size.height * 0.34),
      Offset(size.width * 0.12, size.height * 0.68),
      Offset(size.width * 0.88, size.height * 0.72),
    ]) {
      canvas.drawCircle(point, 1.25, constellation);
    }
  }

  @override
  bool shouldRepaint(covariant _BalanceBackdropPainter oldDelegate) =>
      oldDelegate.visual != visual || oldDelegate.state != state;
}

class _SignatureBalancePainter extends CustomPainter {
  const _SignatureBalancePainter({
    required this.tilt,
    required this.state,
    required this.visual,
  });

  final double tilt;
  final KefeBalanceHeroState state;
  final KefeVisualTheme visual;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height * 0.25);
    final halfBeam = size.width * 0.34;
    final delta = tilt * size.height * 0.070;
    final leftAnchor = Offset(center.dx - halfBeam, center.dy - delta);
    final rightAnchor = Offset(center.dx + halfBeam, center.dy + delta);
    final activeColor = switch (state) {
      KefeBalanceHeroState.leftSelected => visual.rules,
      KefeBalanceHeroState.rightSelected => visual.empathy,
      KefeBalanceHeroState.neutral => visual.gold,
    };

    _drawFloor(canvas, size, activeColor);
    _drawPedestal(canvas, size, center, activeColor);
    _drawPivot(canvas, size, center, activeColor);
    _drawBeam(canvas, size, leftAnchor, rightAnchor);
    _drawPan(
      canvas,
      anchor: leftAnchor,
      size: size,
      color: visual.rules,
      selected: state == KefeBalanceHeroState.leftSelected,
    );
    _drawPan(
      canvas,
      anchor: rightAnchor,
      size: size,
      color: visual.empathy,
      selected: state == KefeBalanceHeroState.rightSelected,
    );
  }

  void _drawFloor(Canvas canvas, Size size, Color activeColor) {
    final baseCenter = Offset(size.width / 2, size.height * 0.91);
    canvas.drawOval(
      Rect.fromCenter(
        center: baseCenter.translate(0, 2),
        width: size.width * 0.34,
        height: size.height * 0.075,
      ),
      Paint()
        ..color = visual.shadow.withValues(alpha: visual.isDark ? 0.48 : 0.16)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 9),
    );
    canvas.drawOval(
      Rect.fromCenter(
        center: baseCenter,
        width: size.width * 0.28,
        height: size.height * 0.050,
      ),
      Paint()
        ..color = activeColor.withValues(alpha: 0.10)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 14),
    );
  }

  void _drawPedestal(
    Canvas canvas,
    Size size,
    Offset center,
    Color activeColor,
  ) {
    final stemTop = center.dy + size.height * 0.055;
    final stemBottom = size.height * 0.83;
    final stemHalfTop = size.width * 0.018;
    final stemHalfBottom = size.width * 0.050;
    final stem = Path()
      ..moveTo(center.dx - stemHalfTop, stemTop)
      ..cubicTo(
        center.dx - stemHalfTop * 1.4,
        size.height * 0.48,
        center.dx - stemHalfBottom,
        size.height * 0.72,
        center.dx - stemHalfBottom,
        stemBottom,
      )
      ..lineTo(center.dx + stemHalfBottom, stemBottom)
      ..cubicTo(
        center.dx + stemHalfBottom,
        size.height * 0.72,
        center.dx + stemHalfTop * 1.4,
        size.height * 0.48,
        center.dx + stemHalfTop,
        stemTop,
      )
      ..close();

    canvas.drawPath(
      stem,
      Paint()
        ..color = visual.gold.withValues(alpha: 0.17)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 10),
    );
    canvas.drawPath(
      stem,
      Paint()
        ..shader = LinearGradient(
          begin: Alignment.centerLeft,
          end: Alignment.centerRight,
          colors: [
            _bronzeDark,
            visual.gold,
            visual.goldSoft,
            visual.gold,
            _bronzeDark,
          ],
          stops: const [0.0, 0.22, 0.50, 0.76, 1.0],
        ).createShader(stem.getBounds()),
    );
    canvas.drawPath(
      stem,
      Paint()
        ..color = visual.goldSoft.withValues(alpha: 0.42)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.2,
    );

    final baseY = size.height * 0.86;
    for (final layer in <({double width, double height, double dy, double alpha})>[
      (width: 0.26, height: 0.055, dy: 0.000, alpha: 1.0),
      (width: 0.22, height: 0.040, dy: -0.026, alpha: 0.90),
      (width: 0.15, height: 0.030, dy: -0.048, alpha: 0.82),
    ]) {
      final rect = Rect.fromCenter(
        center: Offset(center.dx, baseY + size.height * layer.dy),
        width: size.width * layer.width,
        height: size.height * layer.height,
      );
      canvas.drawOval(
        rect,
        Paint()
          ..shader = LinearGradient(
            colors: [
              _bronzeDark,
              visual.gold.withValues(alpha: layer.alpha),
              visual.goldSoft.withValues(alpha: layer.alpha),
              _bronzeDark,
            ],
          ).createShader(rect),
      );
      canvas.drawOval(
        rect,
        Paint()
          ..color = visual.goldSoft.withValues(alpha: 0.28)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1,
      );
    }

    canvas.drawCircle(
      Offset(center.dx, size.height * 0.56),
      size.height * 0.026,
      Paint()
        ..color = activeColor.withValues(alpha: 0.14)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 9),
    );
  }

  void _drawPivot(
    Canvas canvas,
    Size size,
    Offset center,
    Color activeColor,
  ) {
    final radius = size.height * 0.078;
    canvas.drawCircle(
      center,
      radius * 1.45,
      Paint()
        ..color = activeColor.withValues(alpha: 0.12)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 15),
    );
    canvas.drawCircle(
      center,
      radius,
      Paint()
        ..shader = RadialGradient(
          colors: [
            visual.goldSoft,
            visual.gold,
            _bronzeDark,
          ],
          stops: const [0.0, 0.50, 1.0],
        ).createShader(Rect.fromCircle(center: center, radius: radius)),
    );
    canvas.drawCircle(
      center,
      radius * 0.72,
      Paint()..color = visual.surfaceStrong.withValues(alpha: 0.90),
    );
    canvas.drawCircle(
      center,
      radius,
      Paint()
        ..color = visual.goldSoft.withValues(alpha: 0.78)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.3,
    );

    final mark = TextPainter(
      text: TextSpan(
        text: '≠',
        style: TextStyle(
          color: visual.goldSoft,
          fontSize: radius * 0.85,
          fontWeight: FontWeight.w900,
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    mark.paint(
      canvas,
      Offset(center.dx - mark.width / 2, center.dy - mark.height / 2),
    );

    final crownY = center.dy - radius * 1.55;
    final crown = Path()
      ..moveTo(center.dx, crownY - radius * 0.62)
      ..lineTo(center.dx - radius * 0.45, crownY)
      ..lineTo(center.dx + radius * 0.45, crownY)
      ..close();
    canvas.drawPath(
      crown,
      Paint()
        ..shader = LinearGradient(
          colors: [_bronzeDark, visual.goldSoft, visual.gold],
        ).createShader(crown.getBounds()),
    );
    canvas.drawCircle(
      Offset(center.dx, crownY + radius * 0.22),
      radius * 0.31,
      Paint()..color = visual.gold,
    );
  }

  void _drawBeam(
    Canvas canvas,
    Size size,
    Offset leftAnchor,
    Offset rightAnchor,
  ) {
    final beamPath = Path()
      ..moveTo(leftAnchor.dx, leftAnchor.dy)
      ..cubicTo(
        size.width * 0.34,
        leftAnchor.dy + size.height * 0.010,
        size.width * 0.42,
        rightAnchor.dy - size.height * 0.010,
        size.width / 2,
        (leftAnchor.dy + rightAnchor.dy) / 2,
      )
      ..cubicTo(
        size.width * 0.58,
        leftAnchor.dy + size.height * 0.010,
        size.width * 0.66,
        rightAnchor.dy - size.height * 0.010,
        rightAnchor.dx,
        rightAnchor.dy,
      );

    canvas.drawPath(
      beamPath,
      Paint()
        ..color = visual.gold.withValues(alpha: 0.18)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 10
        ..strokeCap = StrokeCap.round
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 8),
    );
    canvas.drawPath(
      beamPath,
      Paint()
        ..shader = LinearGradient(
          colors: [
            _bronzeDark,
            visual.gold,
            visual.goldSoft,
            visual.gold,
            _bronzeDark,
          ],
        ).createShader(Rect.fromLTWH(0, 0, size.width, size.height))
        ..style = PaintingStyle.stroke
        ..strokeWidth = 5.2
        ..strokeCap = StrokeCap.round,
    );
    canvas.drawPath(
      beamPath,
      Paint()
        ..color = visual.goldSoft.withValues(alpha: 0.55)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.1
        ..strokeCap = StrokeCap.round,
    );

    for (final anchor in [leftAnchor, rightAnchor]) {
      canvas.drawCircle(
        anchor,
        size.height * 0.024,
        Paint()
          ..shader = RadialGradient(
            colors: [visual.goldSoft, visual.gold, _bronzeDark],
          ).createShader(
            Rect.fromCircle(center: anchor, radius: size.height * 0.024),
          ),
      );
    }
  }

  void _drawPan(
    Canvas canvas, {
    required Offset anchor,
    required Size size,
    required Color color,
    required bool selected,
  }) {
    final chainLength = size.height * 0.28;
    final panY = anchor.dy + chainLength;
    final panHalfWidth = size.width * 0.128;
    final chainSpread = panHalfWidth * 0.72;
    final chainPaint = Paint()
      ..shader = LinearGradient(
        colors: [_bronzeDark, visual.goldSoft, visual.gold],
      ).createShader(Rect.fromLTWH(0, anchor.dy, size.width, chainLength))
      ..strokeWidth = 1.55
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.stroke;

    canvas.drawLine(
      anchor,
      Offset(anchor.dx - chainSpread, panY),
      chainPaint,
    );
    canvas.drawLine(
      anchor,
      Offset(anchor.dx + chainSpread, panY),
      chainPaint,
    );

    if (selected) {
      canvas.drawCircle(
        Offset(anchor.dx, panY + size.height * 0.018),
        panHalfWidth * 1.25,
        Paint()
          ..color = color.withValues(alpha: 0.20)
          ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 17),
      );
    }

    final panRect = Rect.fromCenter(
      center: Offset(anchor.dx, panY),
      width: panHalfWidth * 2,
      height: size.height * 0.13,
    );
    final panPath = Path()
      ..moveTo(panRect.left, panRect.top)
      ..cubicTo(
        panRect.left + panRect.width * 0.18,
        panRect.bottom + size.height * 0.055,
        panRect.right - panRect.width * 0.18,
        panRect.bottom + size.height * 0.055,
        panRect.right,
        panRect.top,
      )
      ..quadraticBezierTo(
        panRect.center.dx,
        panRect.top + size.height * 0.028,
        panRect.left,
        panRect.top,
      )
      ..close();

    canvas.drawPath(
      panPath,
      Paint()
        ..shader = LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            color.withValues(alpha: selected ? 0.46 : 0.18),
            visual.surfaceStrong.withValues(alpha: 0.88),
            _bronzeDark.withValues(alpha: 0.94),
          ],
        ).createShader(panPath.getBounds()),
    );
    canvas.drawPath(
      panPath,
      Paint()
        ..color = (selected ? color : visual.goldSoft).withValues(
          alpha: selected ? 0.94 : 0.58,
        )
        ..style = PaintingStyle.stroke
        ..strokeWidth = selected ? 2.2 : 1.35,
    );

    final rim = Rect.fromCenter(
      center: Offset(anchor.dx, panY),
      width: panHalfWidth * 2.02,
      height: size.height * 0.032,
    );
    canvas.drawOval(
      rim,
      Paint()
        ..shader = LinearGradient(
          colors: [
            _bronzeDark,
            selected ? color : visual.gold,
            visual.goldSoft,
            _bronzeDark,
          ],
        ).createShader(rim),
    );

    final orbCenter = Offset(anchor.dx, panY - size.height * 0.06);
    final orbRadius = size.height * (selected ? 0.052 : 0.044);
    canvas.drawCircle(
      orbCenter,
      orbRadius * 1.35,
      Paint()
        ..color = color.withValues(alpha: selected ? 0.20 : 0.08)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 12),
    );
    canvas.drawCircle(
      orbCenter,
      orbRadius,
      Paint()
        ..shader = RadialGradient(
          colors: [
            color.withValues(alpha: selected ? 0.35 : 0.15),
            visual.surfaceStrong.withValues(alpha: 0.94),
          ],
        ).createShader(Rect.fromCircle(center: orbCenter, radius: orbRadius)),
    );
    canvas.drawCircle(
      orbCenter,
      orbRadius,
      Paint()
        ..color = color.withValues(alpha: selected ? 0.95 : 0.68)
        ..style = PaintingStyle.stroke
        ..strokeWidth = selected ? 1.8 : 1.2,
    );

    if (selected) {
      canvas.drawCircle(
        orbCenter,
        orbRadius * 0.27,
        Paint()..color = color.withValues(alpha: 0.90),
      );
    }
  }

  Color get _bronzeDark => Color.lerp(
    visual.surfaceStrong,
    visual.gold,
    visual.isDark ? 0.30 : 0.38,
  )!;

  @override
  bool shouldRepaint(covariant _SignatureBalancePainter oldDelegate) =>
      oldDelegate.tilt != tilt ||
      oldDelegate.state != state ||
      oldDelegate.visual != visual;
}
