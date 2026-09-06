import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/cross_cultural_norm_framework_models.dart';

class CrossCulturalNormFrameworkCard extends StatelessWidget {
  const CrossCulturalNormFrameworkCard({
    required this.framework,
    this.onTap,
    super.key,
  });

  final CulturalNormModel framework;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _dimColor(visual, framework.primaryDimension);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('cross-cultural-${framework.frameworkId}'),
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
                  child: Icon(Icons.public_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.cultNormEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _dimLabel(strings, framework.primaryDimension),
                        style: TextStyle(
                          fontSize: 12.5,
                          fontWeight: FontWeight.w800,
                          color: visual.foreground,
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
                  decoration: BoxDecoration(
                    color: visual.surfaceSunken,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                  ),
                  child: Text(
                    framework.regionIdentifier,
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                      color: accent,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: visual.border.withValues(alpha: 0.5)),
              ),
              child: Text(
                framework.normSynthesisSummary,
                style: TextStyle(
                  fontSize: 11.5,
                  color: visual.foreground,
                ),
              ),
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  strings.cultNormAlignmentLabel((framework.culturalAlignmentScore * 100).toInt()),
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: visual.gold,
                  ),
                ),
                if (framework.universalBaselineCompliance)
                  Text(
                    strings.cultNormComplianceLabel,
                    style: const TextStyle(
                      fontSize: 9.5,
                      fontWeight: FontWeight.w800,
                      color: Color(0xFF10B981),
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Color _dimColor(KefeVisualSystem visual, CulturalNormDimensionModel dim) => switch (dim) {
    CulturalNormDimensionModel.communitySolidarityAndMutuality => visual.empathy,
    CulturalNormDimensionModel.individualAutonomyAndLiberty => visual.rules,
    CulturalNormDimensionModel.intergenerationalStewardship => const Color(0xFF10B981),
    CulturalNormDimensionModel.proceduralJusticeAndEquity => visual.gold,
  };

  String _dimLabel(KefeStrings strings, CulturalNormDimensionModel dim) => switch (dim) {
    CulturalNormDimensionModel.communitySolidarityAndMutuality => strings.cultNormDimSolidarity,
    CulturalNormDimensionModel.individualAutonomyAndLiberty => strings.cultNormDimAutonomy,
    CulturalNormDimensionModel.intergenerationalStewardship => strings.cultNormDimStewardship,
    CulturalNormDimensionModel.proceduralJusticeAndEquity => strings.cultNormDimJustice,
  };
}
