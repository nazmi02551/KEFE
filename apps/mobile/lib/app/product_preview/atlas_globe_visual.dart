import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../core/design/kefe_visual_system.dart';

class AtlasGlobeMarker {
  const AtlasGlobeMarker({
    required this.countryCode,
    required this.value,
    required this.normalizedPosition,
  }) : assert(value >= 0 && value <= 10);

  final String countryCode;
  final double value;
  final Offset normalizedPosition;
}

class AtlasGlobeVisual extends StatelessWidget {
  const AtlasGlobeVisual({
    required this.markers,
    this.compact = false,
    super.key,
  });

  final List<AtlasGlobeMarker> markers;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final height = compact ? 218.0 : 292.0;

    return ExcludeSemantics(
      child: SizedBox(
        key: const ValueKey('atlas-world-globe'),
        height: height,
        child: LayoutBuilder(
          builder: (context, constraints) {
            final side = math.min(constraints.maxWidth, constraints.maxHeight);
            final globeDiameter = side * (compact ? 0.78 : 0.84);
            final left = (constraints.maxWidth - globeDiameter) / 2;
            final top = (constraints.maxHeight - globeDiameter) / 2;
            final globeRect = Rect.fromLTWH(
              left,
              top,
              globeDiameter,
              globeDiameter,
            );

            return RepaintBoundary(
              child: Stack(
                clipBehavior: Clip.none,
                children: [
                  Positioned.fill(
                    child: CustomPaint(
                      painter: _AtlasAtmospherePainter(visual: visual),
                    ),
                  ),
                  Positioned.fromRect(
                    rect: globeRect,
                    child: CustomPaint(
                      painter: _AtlasSpherePainter(visual: visual),
                    ),
                  ),
                  for (final marker in markers)
                    _PositionedMarker(
                      marker: marker,
                      globeRect: globeRect,
                      compact: compact,
                    ),
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}

class _PositionedMarker extends StatelessWidget {
  const _PositionedMarker({
    required this.marker,
    required this.globeRect,
    required this.compact,
  });

  final AtlasGlobeMarker marker;
  final Rect globeRect;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final color = _continuumColor(visual, marker.value);
    final markerSize = compact ? 27.0 : 33.0;
    final x = globeRect.left + globeRect.width * marker.normalizedPosition.dx;
    final y = globeRect.top + globeRect.height * marker.normalizedPosition.dy;

    return Positioned(
      left: x - markerSize / 2,
      top: y - markerSize / 2,
      child: Container(
        key: ValueKey('atlas-country-marker-${marker.countryCode}'),
        width: markerSize,
        height: markerSize,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: visual.surfaceStrong.withValues(alpha: 0.92),
          border: Border.all(color: color.withValues(alpha: 0.92), width: 1.5),
          boxShadow: [
            BoxShadow(
              color: color.withValues(alpha: visual.isDark ? 0.34 : 0.20),
              blurRadius: compact ? 8 : 13,
              spreadRadius: compact ? 1 : 2,
            ),
          ],
        ),
        child: Text(
          marker.countryCode,
          maxLines: 1,
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
            color: color,
            fontSize: compact ? 8 : 9,
            fontWeight: FontWeight.w900,
            letterSpacing: 0.1,
          ),
        ),
      ),
    );
  }
}

class _AtlasAtmospherePainter extends CustomPainter {
  const _AtlasAtmospherePainter({required this.visual});

  final KefeVisualTheme visual;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = math.min(size.width, size.height) * 0.44;

    canvas.drawCircle(
      center,
      radius * 1.08,
      Paint()
        ..color = visual.rules.withValues(alpha: visual.isDark ? 0.08 : 0.05)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 24),
    );
    canvas.drawCircle(
      center,
      radius * 0.92,
      Paint()
        ..color = visual.gold.withValues(alpha: visual.isDark ? 0.05 : 0.035)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 28),
    );

    final orbit = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.1
      ..color = visual.goldSoft.withValues(alpha: visual.isDark ? 0.22 : 0.16);
    final secondaryOrbit = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 0.9
      ..color = visual.rules.withValues(alpha: visual.isDark ? 0.18 : 0.12);

    canvas.save();
    canvas.translate(center.dx, center.dy);
    canvas.rotate(-0.20);
    canvas.drawOval(
      Rect.fromCenter(
        center: Offset.zero,
        width: radius * 2.42,
        height: radius * 0.94,
      ),
      orbit,
    );
    canvas.rotate(0.46);
    canvas.drawOval(
      Rect.fromCenter(
        center: Offset.zero,
        width: radius * 2.18,
        height: radius * 0.72,
      ),
      secondaryOrbit,
    );
    canvas.restore();

    final star = Paint()
      ..color = visual.goldSoft.withValues(alpha: visual.isDark ? 0.30 : 0.18);
    for (final point in <Offset>[
      Offset(size.width * 0.10, size.height * 0.25),
      Offset(size.width * 0.18, size.height * 0.76),
      Offset(size.width * 0.80, size.height * 0.16),
      Offset(size.width * 0.89, size.height * 0.66),
      Offset(size.width * 0.71, size.height * 0.84),
    ]) {
      canvas.drawCircle(point, 1.25, star);
    }
  }

  @override
  bool shouldRepaint(covariant _AtlasAtmospherePainter oldDelegate) =>
      oldDelegate.visual != visual;
}

class _AtlasSpherePainter extends CustomPainter {
  const _AtlasSpherePainter({required this.visual});

  final KefeVisualTheme visual;

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    final center = rect.center;
    final radius = size.shortestSide / 2;
    final sphere = Path()..addOval(rect.deflate(2));

    canvas.drawCircle(
      center,
      radius * 0.98,
      Paint()
        ..shader = RadialGradient(
          center: const Alignment(-0.34, -0.40),
          radius: 1.12,
          colors: [
            Color.lerp(visual.surfaceStrong, visual.rules, 0.36)!,
            Color.lerp(visual.surfaceStrong, visual.rules, 0.16)!,
            visual.surfaceSunken,
            Color.lerp(visual.surfaceSunken, visual.gold, 0.09)!,
          ],
          stops: const [0.0, 0.34, 0.74, 1.0],
        ).createShader(rect),
    );

    canvas.save();
    canvas.clipPath(sphere);
    _drawLandmasses(canvas, size);
    _drawGraticule(canvas, size);
    _drawNetwork(canvas, size);

    canvas.drawCircle(
      Offset(size.width * 0.31, size.height * 0.27),
      radius * 0.45,
      Paint()
        ..color = Colors.white.withValues(alpha: visual.isDark ? 0.055 : 0.10)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 18),
    );
    canvas.restore();

    canvas.drawCircle(
      center,
      radius * 0.98,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.5
        ..shader = SweepGradient(
          colors: [
            visual.rules.withValues(alpha: 0.68),
            visual.goldSoft.withValues(alpha: 0.34),
            visual.empathy.withValues(alpha: 0.56),
            visual.rules.withValues(alpha: 0.68),
          ],
        ).createShader(rect),
    );

    canvas.drawArc(
      rect.deflate(5),
      -2.52,
      1.46,
      false,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeCap = StrokeCap.round
        ..strokeWidth = 3.0
        ..color = visual.rules.withValues(alpha: 0.55),
    );
    canvas.drawArc(
      rect.deflate(6),
      0.14,
      1.18,
      false,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeCap = StrokeCap.round
        ..strokeWidth = 2.5
        ..color = visual.goldSoft.withValues(alpha: 0.48),
    );
  }

  void _drawGraticule(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.shortestSide / 2;
    final gridPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 0.75
      ..color = visual.rules.withValues(alpha: visual.isDark ? 0.20 : 0.14);

    for (final factor in <double>[0.34, 0.66]) {
      canvas.drawOval(
        Rect.fromCenter(
          center: center,
          width: radius * 2 * factor,
          height: radius * 1.96,
        ),
        gridPaint,
      );
      canvas.drawOval(
        Rect.fromCenter(
          center: center,
          width: radius * 1.96,
          height: radius * 2 * factor,
        ),
        gridPaint,
      );
    }

    canvas.drawLine(
      Offset(center.dx, center.dy - radius),
      Offset(center.dx, center.dy + radius),
      gridPaint,
    );
    canvas.drawLine(
      Offset(center.dx - radius, center.dy),
      Offset(center.dx + radius, center.dy),
      gridPaint,
    );
  }

  void _drawLandmasses(Canvas canvas, Size size) {
    final landPaint = Paint()
      ..style = PaintingStyle.fill
      ..shader = LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [
          visual.goldSoft.withValues(alpha: visual.isDark ? 0.22 : 0.20),
          visual.rules.withValues(alpha: visual.isDark ? 0.18 : 0.13),
        ],
      ).createShader(Offset.zero & size);
    final coastPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 0.8
      ..color = visual.goldSoft.withValues(alpha: visual.isDark ? 0.28 : 0.20);

    final americas = Path()
      ..moveTo(size.width * 0.18, size.height * 0.27)
      ..cubicTo(
        size.width * 0.10,
        size.height * 0.34,
        size.width * 0.15,
        size.height * 0.48,
        size.width * 0.24,
        size.height * 0.49,
      )
      ..cubicTo(
        size.width * 0.31,
        size.height * 0.55,
        size.width * 0.26,
        size.height * 0.70,
        size.width * 0.34,
        size.height * 0.82,
      )
      ..cubicTo(
        size.width * 0.23,
        size.height * 0.76,
        size.width * 0.18,
        size.height * 0.64,
        size.width * 0.18,
        size.height * 0.55,
      )
      ..cubicTo(
        size.width * 0.08,
        size.height * 0.48,
        size.width * 0.09,
        size.height * 0.34,
        size.width * 0.18,
        size.height * 0.27,
      )
      ..close();

    final eurasiaAfrica = Path()
      ..moveTo(size.width * 0.43, size.height * 0.24)
      ..cubicTo(
        size.width * 0.54,
        size.height * 0.15,
        size.width * 0.77,
        size.height * 0.20,
        size.width * 0.85,
        size.height * 0.35,
      )
      ..cubicTo(
        size.width * 0.80,
        size.height * 0.42,
        size.width * 0.68,
        size.height * 0.39,
        size.width * 0.64,
        size.height * 0.47,
      )
      ..cubicTo(
        size.width * 0.61,
        size.height * 0.55,
        size.width * 0.63,
        size.height * 0.73,
        size.width * 0.54,
        size.height * 0.79,
      )
      ..cubicTo(
        size.width * 0.45,
        size.height * 0.69,
        size.width * 0.46,
        size.height * 0.54,
        size.width * 0.39,
        size.height * 0.48,
      )
      ..cubicTo(
        size.width * 0.35,
        size.height * 0.39,
        size.width * 0.36,
        size.height * 0.30,
        size.width * 0.43,
        size.height * 0.24,
      )
      ..close();

    final island = Path()
      ..moveTo(size.width * 0.77, size.height * 0.60)
      ..quadraticBezierTo(
        size.width * 0.90,
        size.height * 0.64,
        size.width * 0.84,
        size.height * 0.76,
      )
      ..quadraticBezierTo(
        size.width * 0.73,
        size.height * 0.74,
        size.width * 0.77,
        size.height * 0.60,
      )
      ..close();

    for (final path in [americas, eurasiaAfrica, island]) {
      canvas.drawPath(path, landPaint);
      canvas.drawPath(path, coastPaint);
    }
  }

  void _drawNetwork(Canvas canvas, Size size) {
    final line = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 0.85
      ..color = visual.goldSoft.withValues(alpha: visual.isDark ? 0.20 : 0.13);
    final paths = <Path>[
      Path()
        ..moveTo(size.width * 0.20, size.height * 0.36)
        ..quadraticBezierTo(
          size.width * 0.48,
          size.height * 0.17,
          size.width * 0.76,
          size.height * 0.38,
        ),
      Path()
        ..moveTo(size.width * 0.31, size.height * 0.66)
        ..quadraticBezierTo(
          size.width * 0.52,
          size.height * 0.43,
          size.width * 0.72,
          size.height * 0.67,
        ),
      Path()
        ..moveTo(size.width * 0.43, size.height * 0.30)
        ..quadraticBezierTo(
          size.width * 0.56,
          size.height * 0.52,
          size.width * 0.62,
          size.height * 0.38,
        ),
    ];
    for (final path in paths) {
      canvas.drawPath(path, line);
    }
  }

  @override
  bool shouldRepaint(covariant _AtlasSpherePainter oldDelegate) =>
      oldDelegate.visual != visual;
}

Color _continuumColor(KefeVisualTheme visual, double value) {
  final normalized = (value / 10).clamp(0.0, 1.0);
  if (normalized <= 0.5) {
    return Color.lerp(visual.rules, visual.goldSoft, normalized * 2)!;
  }
  return Color.lerp(visual.goldSoft, visual.empathy, (normalized - 0.5) * 2)!;
}
