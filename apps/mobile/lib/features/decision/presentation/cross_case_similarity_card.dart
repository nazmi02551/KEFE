import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/cross_case_similarity_models.dart';

class CrossCaseSimilarityCard extends StatelessWidget {
  const CrossCaseSimilarityCard({
    required this.similarity,
    this.onTap,
    super.key,
  });

  final CrossCaseSimilarityModel similarity;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _tierColor(visual, similarity.alignmentTier);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('cross-sim-${similarity.targetCaseId}'),
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
                  child: Icon(Icons.auto_stories_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.crossSimEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _tierLabel(strings, similarity.alignmentTier),
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
                    strings.crossSimSimilarityLabel((similarity.similarityScore * 100).toInt()),
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
            Text(
              similarity.targetCaseTitle,
              style: TextStyle(
                fontSize: 12.5,
                fontWeight: FontWeight.w800,
                color: visual.foreground,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: visual.border.withValues(alpha: 0.5)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    strings.crossSimTensionLabel,
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      color: visual.gold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    similarity.sharedTensionSummary,
                    style: TextStyle(
                      fontSize: 11.5,
                      color: visual.foreground,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _tierColor(KefeVisualSystem visual, SimilarityAlignmentTierModel tier) => switch (tier) {
    SimilarityAlignmentTierModel.highTopologicalAnalogue => visual.rules,
    SimilarityAlignmentTierModel.partialDomainOverlap => visual.gold,
    SimilarityAlignmentTierModel.distantPrecedent => visual.empathy,
  };

  String _tierLabel(KefeStrings strings, SimilarityAlignmentTierModel tier) => switch (tier) {
    SimilarityAlignmentTierModel.highTopologicalAnalogue => strings.crossSimTierHigh,
    SimilarityAlignmentTierModel.partialDomainOverlap => strings.crossSimTierPartial,
    SimilarityAlignmentTierModel.distantPrecedent => strings.crossSimTierDistant,
  };
}
