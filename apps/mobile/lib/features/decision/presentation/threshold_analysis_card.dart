import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/threshold_analysis_models.dart';

class ThresholdAnalysisCard extends StatelessWidget {
  const ThresholdAnalysisCard({
    required this.analysis,
    super.key,
  });

  final ThresholdAnalysisModel analysis;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = visual.rules;

    return KefeSurface(
      key: ValueKey('threshold-analysis-${analysis.caseVersionId}'),
      tone: KefeSurfaceTone.raised,
      padding: const EdgeInsets.all(18),
      borderRadius: 22,
      accent: accent,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: accent.withValues(alpha: visual.isDark ? 0.16 : 0.08),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: accent.withValues(alpha: 0.25)),
                ),
                child: Icon(Icons.tune_rounded, color: accent, size: 18),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    KefeEyebrow(strings.thresholdEyebrow, color: accent),
                    const SizedBox(height: 2),
                    Text(
                      analysis.parameterName,
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w800,
                        letterSpacing: -0.2,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
            decoration: BoxDecoration(
              color: visual.surfaceSunken,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: visual.border.withValues(alpha: 0.6)),
            ),
            child: Row(
              children: [
                Icon(Icons.flag_outlined, size: 15, color: visual.goldSoft),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    strings.thresholdTippingPoint(
                      analysis.tippingPointThreshold.toStringAsFixed(0),
                      analysis.unit,
                    ),
                    style: TextStyle(
                      fontSize: 11.5,
                      fontWeight: FontWeight.w800,
                      color: visual.goldSoft,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          ...analysis.curvePoints.map((point) {
            final isTipping = point.parameterValue == analysis.tippingPointThreshold;
            return Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        '${point.parameterValue.toStringAsFixed(0)} ${analysis.unit}',
                        style: TextStyle(
                          fontSize: 11.5,
                          fontWeight: isTipping ? FontWeight.w800 : FontWeight.w600,
                          color: isTipping ? visual.goldSoft : visual.foreground,
                        ),
                      ),
                      Text(
                        '%${(point.acceptanceRate * 100).toStringAsFixed(0)} kabul',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          color: visual.mutedForeground,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(3),
                    child: SizedBox(
                      height: 4,
                      child: LinearProgressIndicator(
                        value: point.acceptanceRate.clamp(0.0, 1.0),
                        backgroundColor: visual.surfaceSunken,
                        valueColor: AlwaysStoppedAnimation<Color>(
                          isTipping ? visual.goldSoft : visual.rules,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }
}
