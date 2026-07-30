import 'package:flutter/material.dart';

import '../../../core/design/kefe_theme.dart';

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
    final selectedLabel = switch (selectedIndex) {
      0 => leftLabel,
      1 => rightLabel,
      _ => 'Henüz seçim yok',
    };

    return Semantics(
      label: 'KEFE terazisi. $selectedLabel',
      child: Container(
        key: const ValueKey('kefe-balance-visual'),
        padding: EdgeInsets.fromLTRB(14, compact ? 10 : 16, 14, 12),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(compact ? 18 : 22),
          border: Border.all(
            color: KefeColorTokens.gold.withValues(alpha: 0.28),
          ),
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              KefeColorTokens.rules.withValues(alpha: 0.08),
              KefeColorTokens.surfaceElevatedDark.withValues(alpha: 0.72),
              KefeColorTokens.empathy.withValues(alpha: 0.08),
            ],
          ),
        ),
        child: Column(
          children: [
            SizedBox(
              height: compact ? 88 : 118,
              width: double.infinity,
              child: CustomPaint(
                painter: _KefeBalancePainter(selectedIndex: selectedIndex),
              ),
            ),
            const SizedBox(height: 4),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: _SideLabel(
                    label: leftLabel,
                    color: KefeColorTokens.rules,
                    selected: selectedIndex == 0,
                    alignment: TextAlign.left,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: _SideLabel(
                    label: rightLabel,
                    color: KefeColorTokens.empathy,
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
    return AnimatedDefaultTextStyle(
      duration: const Duration(milliseconds: 180),
      style: Theme.of(context).textTheme.labelMedium!.copyWith(
        color: selected ? color : KefeColorTokens.textMutedDark,
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
  const _KefeBalancePainter({required this.selectedIndex});

  final int? selectedIndex;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height * 0.34);
    final halfBeam = size.width * 0.31;
    final tilt = switch (selectedIndex) {
      0 => -1.0,
      1 => 1.0,
      _ => 0.0,
    };
    final delta = tilt * size.height * 0.055;
    final left = Offset(center.dx - halfBeam, center.dy - delta);
    final right = Offset(center.dx + halfBeam, center.dy + delta);

    final goldPaint = Paint()
      ..color = KefeColorTokens.goldSoft
      ..strokeWidth = 3.2
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.stroke;
    final mutedGold = Paint()
      ..color = KefeColorTokens.gold.withValues(alpha: 0.52)
      ..strokeWidth = 1.7
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.stroke;

    final baseY = size.height * 0.88;
    canvas.drawLine(
      Offset(center.dx, center.dy + 2),
      Offset(center.dx, baseY - 8),
      goldPaint,
    );
    canvas.drawLine(
      Offset(center.dx - size.width * 0.14, baseY),
      Offset(center.dx + size.width * 0.14, baseY),
      goldPaint,
    );
    canvas.drawCircle(center, 6.5, Paint()..color = KefeColorTokens.goldSoft);
    canvas.drawLine(left, right, goldPaint);

    _drawPan(
      canvas,
      anchor: left,
      size: size,
      color: KefeColorTokens.rules,
      selected: selectedIndex == 0,
      chainPaint: mutedGold,
    );
    _drawPan(
      canvas,
      anchor: right,
      size: size,
      color: KefeColorTokens.empathy,
      selected: selectedIndex == 1,
      chainPaint: mutedGold,
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

    final fill = Paint()
      ..color = color.withValues(alpha: selected ? 0.30 : 0.12)
      ..style = PaintingStyle.fill;
    final outline = Paint()
      ..color = color.withValues(alpha: selected ? 0.95 : 0.55)
      ..strokeWidth = selected ? 2.2 : 1.4
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
        rect.bottom + size.height * 0.08,
        rect.right,
        rect.top,
      )
      ..close();

    canvas.drawPath(panPath, fill);
    canvas.drawPath(panPath, outline);
  }

  @override
  bool shouldRepaint(covariant _KefeBalancePainter oldDelegate) =>
      oldDelegate.selectedIndex != selectedIndex;
}
