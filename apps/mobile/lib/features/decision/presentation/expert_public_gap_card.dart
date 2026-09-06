import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/expert_public_gap_models.dart';

class ExpertPublicGapCard extends StatelessWidget {
  const ExpertPublicGapCard({
    required this.gap,
    this.onTap,
    super.key,
  });

  final ExpertPublicGapModel gap;
  final VoidCallback? onTap;

  Color _classificationColor(KefeVisualSystem visual, String classification) =>
      switch (classification) {
        'CONVERGENT' => visual.success,
        'TECHNICAL_TRANSLATION_GAP' => visual.gold,
        'NORMATIVE_VALUE_DIVERGENCE' => visual.empathy,
        'TRUST_DEFICIT_SKEPTICISM' => visual.attention,
        _ => visual.mutedForeground,
      };

  String _classificationLabel(KefeStrings strings, String classification) =>
      switch (classification) {
        'CONVERGENT' => strings.expertGapClassConvergent,
        'TECHNICAL_TRANSLATION_GAP' => strings.expertGapClassTechnical,
        'NORMATIVE_VALUE_DIVERGENCE' => strings.expertGapClassNormative,
        'TRUST_DEFICIT_SKEPTICISM' => strings.expertGapClassTrust,
        _ => classification,
      };

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = visual.rules;
    final classColor = _classificationColor(visual, gap.gapClassification);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('expert-gap-${gap.caseVersionId}'),
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
                    color: accent.withValues(alpha: visual.isDark ? 0.18 : 0.10),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: accent.withValues(alpha: 0.3)),
                  ),
                  child: Icon(Icons.school_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.expertGapEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        strings.expertGapTitle,
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                          color: visual.foreground,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 6,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: classColor.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: classColor.withValues(alpha: 0.28)),
                  ),
                  child: Text(
                    _classificationLabel(strings, gap.gapClassification),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: classColor,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: visual.mutedForeground.withValues(alpha: 0.08),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    strings.expertGapMagnitude(gap.gapMagnitudePoints),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: visual.foreground,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            // Comparison Bars (Experts vs Public)
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: visual.isDark
                    ? Colors.white.withValues(alpha: 0.03)
                    : Colors.black.withValues(alpha: 0.02),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: visual.rules.withValues(alpha: 0.20)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        strings.expertGapExpertsSample(gap.expertSampleSize),
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: visual.foreground,
                        ),
                      ),
                      Text(
                        'A: %${((gap.expertDistribution['A'] ?? 0.0) * 100).toInt()}',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          color: visual.rules,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: Row(
                      children: gap.expertDistribution.entries.map((e) {
                        final color = e.key == 'A' ? visual.rules : visual.empathy;
                        return Expanded(
                          flex: (e.value * 1000).toInt(),
                          child: Container(
                            height: 7,
                            color: color.withValues(alpha: 0.85),
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        strings.expertGapPublicSample(gap.publicSampleSize),
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: visual.foreground,
                        ),
                      ),
                      Text(
                        'A: %${((gap.publicDistribution['A'] ?? 0.0) * 100).toInt()}',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          color: visual.empathy,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: Row(
                      children: gap.publicDistribution.entries.map((e) {
                        final color = e.key == 'A' ? visual.rules : visual.empathy;
                        return Expanded(
                          flex: (e.value * 1000).toInt(),
                          child: Container(
                            height: 7,
                            color: color.withValues(alpha: 0.85),
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                ],
              ),
            ),
            if (gap.keyDivergenceDrivers.isNotEmpty) ...[
              const SizedBox(height: 14),
              Text(
                strings.expertGapDriversTitle,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: visual.gold,
                ),
              ),
              const SizedBox(height: 6),
              ...gap.keyDivergenceDrivers.map(
                (driver) => Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('• ', style: TextStyle(color: visual.gold, fontSize: 13)),
                      Expanded(
                        child: Text(
                          driver,
                          style: TextStyle(
                            fontSize: 11,
                            height: 1.35,
                            color: visual.foreground.withValues(alpha: 0.90),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
            if (gap.epistemicBridges.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(
                strings.expertGapBridgesTitle,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: visual.success,
                ),
              ),
              const SizedBox(height: 6),
              ...gap.epistemicBridges.map(
                (bridge) => Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.check_circle_outline_rounded,
                          color: visual.success, size: 14),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          bridge,
                          style: TextStyle(
                            fontSize: 11,
                            height: 1.35,
                            color: visual.foreground.withValues(alpha: 0.90),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
