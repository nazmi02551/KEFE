import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../../core/design/kefe_visual_system.dart';
import '../../../core/visual_composition/kefe_visual_composition_flutter.dart';
import '../../../core/visual_composition/kefe_visual_composition_models.dart';

class SportsCallSceneVisual extends StatelessWidget {
  const SportsCallSceneVisual({
    required this.mediaKey,
    required this.aspectRatio,
    required this.borderRadius,
    required this.composition,
    this.attribution,
    super.key,
  });

  final Key mediaKey;
  final double aspectRatio;
  final double borderRadius;
  final KefeVisualCompositionPolicy composition;
  final String? attribution;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;

    return AspectRatio(
      aspectRatio: aspectRatio,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(borderRadius),
        child: DecoratedBox(
          key: mediaKey,
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                Color.lerp(visual.surfaceStrong, visual.success, 0.20)!,
                Color.lerp(visual.surfaceStrong, visual.success, 0.09)!,
                visual.surfaceSunken,
              ],
              stops: const [0.0, 0.54, 1.0],
            ),
          ),
          child: LayoutBuilder(
            builder: (context, constraints) {
              final size = Size(constraints.maxWidth, constraints.maxHeight);
              final safePadding = composition.safePaddingFor(size);
              return Stack(
                fit: StackFit.expand,
                children: [
                  RepaintBoundary(
                    child: CustomPaint(
                      painter: _SportsCallScenePainter(visual: visual),
                    ),
                  ),
                  if (attribution != null)
                    Align(
                      alignment: Alignment.bottomLeft,
                      child: Padding(
                        padding: safePadding,
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 5,
                          ),
                          decoration: BoxDecoration(
                            color: visual.surfaceStrong.withValues(alpha: 0.86),
                            borderRadius: BorderRadius.circular(99),
                            border: Border.all(
                              color: visual.goldSoft.withValues(alpha: 0.16),
                            ),
                          ),
                          child: Text(
                            attribution!,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: Theme.of(context).textTheme.labelSmall
                                ?.copyWith(
                                  color: visual.onSurfaceStrong.withValues(
                                    alpha: 0.72,
                                  ),
                                  fontSize: 9,
                                ),
                          ),
                        ),
                      ),
                    ),
                ],
              );
            },
          ),
        ),
      ),
    );
  }
}

class _SportsCallScenePainter extends CustomPainter {
  const _SportsCallScenePainter({required this.visual});

  final KefeVisualTheme visual;

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    final pitch = Path()
      ..moveTo(size.width * 0.08, size.height * 0.93)
      ..lineTo(size.width * 0.92, size.height * 0.93)
      ..lineTo(size.width * 0.73, size.height * 0.20)
      ..lineTo(size.width * 0.27, size.height * 0.20)
      ..close();

    _drawAmbientDepth(canvas, size);

    canvas.drawPath(
      pitch,
      Paint()
        ..shader = LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            Color.lerp(visual.surfaceStrong, visual.success, 0.22)!,
            Color.lerp(visual.surfaceSunken, visual.success, 0.28)!,
            Color.lerp(visual.surfaceSunken, visual.success, 0.13)!,
          ],
        ).createShader(rect),
    );

    canvas.save();
    canvas.clipPath(pitch);
    _drawPitchStripes(canvas, size);
    _drawPitchLines(canvas, size);
    _drawDecisionMoment(canvas, size);
    canvas.restore();

    _drawGoal(canvas, size);
    _drawPitchEdge(canvas, pitch);
  }

  void _drawAmbientDepth(Canvas canvas, Size size) {
    final topGlow = Paint()
      ..shader = RadialGradient(
        center: const Alignment(0, -0.85),
        radius: 1.10,
        colors: [
          visual.goldSoft.withValues(alpha: visual.isDark ? 0.10 : 0.07),
          Colors.transparent,
        ],
      ).createShader(Offset.zero & size);
    canvas.drawRect(Offset.zero & size, topGlow);

    final horizonPaint = Paint()
      ..color = visual.rules.withValues(alpha: visual.isDark ? 0.07 : 0.04)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 22);
    canvas.drawOval(
      Rect.fromCenter(
        center: Offset(size.width * 0.5, size.height * 0.18),
        width: size.width * 0.82,
        height: size.height * 0.26,
      ),
      horizonPaint,
    );

    final lightPaint = Paint()
      ..color = visual.goldSoft.withValues(alpha: visual.isDark ? 0.36 : 0.24)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 4);
    for (final x in <double>[0.14, 0.25, 0.75, 0.86]) {
      canvas.drawCircle(
        Offset(size.width * x, size.height * 0.09),
        math.max(1.2, size.shortestSide * 0.009),
        lightPaint,
      );
    }
  }

  void _drawPitchStripes(Canvas canvas, Size size) {
    for (var band = 0; band < 7; band++) {
      final t0 = band / 7;
      final t1 = (band + 1) / 7;
      final topY = size.height * 0.20;
      final bottomY = size.height * 0.93;
      final y0 = topY + (bottomY - topY) * t0;
      final y1 = topY + (bottomY - topY) * t1;
      final left0 = _pitchLeftAt(size, y0);
      final right0 = _pitchRightAt(size, y0);
      final left1 = _pitchLeftAt(size, y1);
      final right1 = _pitchRightAt(size, y1);
      final bandPath = Path()
        ..moveTo(left0, y0)
        ..lineTo(right0, y0)
        ..lineTo(right1, y1)
        ..lineTo(left1, y1)
        ..close();
      canvas.drawPath(
        bandPath,
        Paint()
          ..color = Colors.white.withValues(
            alpha: band.isEven
                ? (visual.isDark ? 0.025 : 0.035)
                : (visual.isDark ? 0.008 : 0.012),
          ),
      );
    }
  }

  void _drawPitchLines(Canvas canvas, Size size) {
    final line = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = math.max(0.85, size.shortestSide * 0.0045)
      ..color = Colors.white.withValues(alpha: visual.isDark ? 0.50 : 0.63);

    final pitch = Path()
      ..moveTo(size.width * 0.08, size.height * 0.93)
      ..lineTo(size.width * 0.92, size.height * 0.93)
      ..lineTo(size.width * 0.73, size.height * 0.20)
      ..lineTo(size.width * 0.27, size.height * 0.20)
      ..close();
    canvas.drawPath(pitch, line);

    final halfwayY = size.height * 0.56;
    canvas.drawLine(
      Offset(_pitchLeftAt(size, halfwayY), halfwayY),
      Offset(_pitchRightAt(size, halfwayY), halfwayY),
      line,
    );

    final center = Offset(size.width * 0.5, halfwayY);
    canvas.drawOval(
      Rect.fromCenter(
        center: center,
        width: size.width * 0.17,
        height: size.height * 0.12,
      ),
      line,
    );
    canvas.drawCircle(
      center,
      math.max(1.5, size.shortestSide * 0.007),
      Paint()..color = line.color,
    );

    final boxTop = size.height * 0.20;
    final boxBottom = size.height * 0.37;
    canvas.drawPath(
      Path()
        ..moveTo(size.width * 0.38, boxTop)
        ..lineTo(size.width * 0.62, boxTop)
        ..lineTo(size.width * 0.67, boxBottom)
        ..lineTo(size.width * 0.33, boxBottom),
      line,
    );
  }

  void _drawDecisionMoment(Canvas canvas, Size size) {
    final focal = Offset(size.width * 0.53, size.height * 0.64);
    final glow = Paint()
      ..color = visual.gold.withValues(alpha: visual.isDark ? 0.10 : 0.075)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 16);
    canvas.drawCircle(focal, size.shortestSide * 0.16, glow);

    _drawPlayer(
      canvas,
      size,
      center: Offset(size.width * 0.43, size.height * 0.62),
      color: visual.rules,
      scale: 1.0,
    );
    _drawPlayer(
      canvas,
      size,
      center: Offset(size.width * 0.61, size.height * 0.58),
      color: visual.empathy,
      scale: 0.94,
    );
    _drawPlayer(
      canvas,
      size,
      center: Offset(size.width * 0.32, size.height * 0.48),
      color: visual.rules.withValues(alpha: 0.74),
      scale: 0.72,
    );
    _drawPlayer(
      canvas,
      size,
      center: Offset(size.width * 0.70, size.height * 0.46),
      color: visual.empathy.withValues(alpha: 0.72),
      scale: 0.69,
    );

    final ballCenter = Offset(size.width * 0.53, size.height * 0.70);
    final ballRadius = math.max(3.8, size.shortestSide * 0.025);
    canvas.drawCircle(
      ballCenter,
      ballRadius * 1.8,
      Paint()
        ..color = visual.goldSoft.withValues(alpha: 0.13)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 8),
    );
    canvas.drawCircle(
      ballCenter,
      ballRadius,
      Paint()..color = visual.onSurfaceStrong.withValues(alpha: 0.92),
    );
    canvas.drawCircle(
      ballCenter + Offset(ballRadius * 0.18, -ballRadius * 0.10),
      ballRadius * 0.34,
      Paint()..color = visual.surfaceStrong.withValues(alpha: 0.72),
    );
  }

  void _drawPlayer(
    Canvas canvas,
    Size size, {
    required Offset center,
    required Color color,
    required double scale,
  }) {
    final unit = size.shortestSide * 0.028 * scale;
    final bodyPaint = Paint()
      ..color = color.withValues(alpha: 0.88)
      ..style = PaintingStyle.fill;
    final shadow = Paint()
      ..color = color.withValues(alpha: 0.15)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 7);

    canvas.drawOval(
      Rect.fromCenter(
        center: Offset(center.dx, center.dy + unit * 1.9),
        width: unit * 3.0,
        height: unit * 1.2,
      ),
      shadow,
    );
    canvas.drawCircle(
      Offset(center.dx, center.dy - unit * 1.8),
      unit * 0.62,
      bodyPaint,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromCenter(
          center: Offset(center.dx, center.dy - unit * 0.25),
          width: unit * 1.45,
          height: unit * 2.35,
        ),
        Radius.circular(unit * 0.44),
      ),
      bodyPaint,
    );
    final limb = Paint()
      ..color = color.withValues(alpha: 0.82)
      ..strokeWidth = math.max(1.5, unit * 0.34)
      ..strokeCap = StrokeCap.round;
    canvas.drawLine(
      Offset(center.dx - unit * 0.38, center.dy + unit * 0.72),
      Offset(center.dx - unit * 0.92, center.dy + unit * 1.90),
      limb,
    );
    canvas.drawLine(
      Offset(center.dx + unit * 0.38, center.dy + unit * 0.72),
      Offset(center.dx + unit * 0.92, center.dy + unit * 1.72),
      limb,
    );
  }

  void _drawGoal(Canvas canvas, Size size) {
    final goalPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = math.max(1.0, size.shortestSide * 0.005)
      ..color = visual.onSurfaceStrong.withValues(
        alpha: visual.isDark ? 0.58 : 0.68,
      );
    final topLeft = Offset(size.width * 0.42, size.height * 0.13);
    final topRight = Offset(size.width * 0.58, size.height * 0.13);
    final bottomLeft = Offset(size.width * 0.39, size.height * 0.21);
    final bottomRight = Offset(size.width * 0.61, size.height * 0.21);
    canvas.drawLine(topLeft, topRight, goalPaint);
    canvas.drawLine(topLeft, bottomLeft, goalPaint);
    canvas.drawLine(topRight, bottomRight, goalPaint);
    canvas.drawLine(bottomLeft, bottomRight, goalPaint);

    final net = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = math.max(0.5, size.shortestSide * 0.002)
      ..color = goalPaint.color.withValues(alpha: 0.42);
    for (var i = 1; i < 5; i++) {
      final t = i / 5;
      canvas.drawLine(
        Offset.lerp(topLeft, topRight, t)!,
        Offset.lerp(bottomLeft, bottomRight, t)!,
        net,
      );
    }
  }

  void _drawPitchEdge(Canvas canvas, Path pitch) {
    canvas.drawPath(
      pitch,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.2
        ..color = visual.goldSoft.withValues(
          alpha: visual.isDark ? 0.13 : 0.09,
        ),
    );
  }

  double _pitchLeftAt(Size size, double y) {
    final topY = size.height * 0.20;
    final bottomY = size.height * 0.93;
    final t = ((y - topY) / (bottomY - topY)).clamp(0.0, 1.0);
    return size.width * (0.27 + (0.08 - 0.27) * t);
  }

  double _pitchRightAt(Size size, double y) {
    final topY = size.height * 0.20;
    final bottomY = size.height * 0.93;
    final t = ((y - topY) / (bottomY - topY)).clamp(0.0, 1.0);
    return size.width * (0.73 + (0.92 - 0.73) * t);
  }

  @override
  bool shouldRepaint(covariant _SportsCallScenePainter oldDelegate) =>
      oldDelegate.visual != visual;
}
