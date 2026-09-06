import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/perspective_clustering_models.dart';

class PerspectiveClusteringCard extends StatelessWidget {
  const PerspectiveClusteringCard({
    required this.clustering,
    this.onTap,
    super.key,
  });

  final CaseClusteringModel clustering;
  final VoidCallback? onTap;

  Color _archetypeColor(KefeVisualSystem visual, String archetype) => switch (archetype) {
    'NEAR_CONSENSUS' => visual.rules,
    'OPPOSING_PRINCIPLE' => visual.empathy,
    'BRIDGE_SYNTHESIS' => visual.gold,
    'ALTERNATIVE_PARADIGM' => visual.success,
    _ => visual.mutedForeground,
  };

  String _archetypeLabel(KefeStrings strings, String archetype) => switch (archetype) {
    'NEAR_CONSENSUS' => strings.argClusteringArchetypeNearConsensus,
    'OPPOSING_PRINCIPLE' => strings.argClusteringArchetypeOpposing,
    'BRIDGE_SYNTHESIS' => strings.argClusteringArchetypeBridge,
    'ALTERNATIVE_PARADIGM' => strings.argClusteringArchetypeAlternative,
    _ => archetype,
  };

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = visual.rules;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('clustering-${clustering.caseVersionId}'),
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
                  child: Icon(Icons.bubble_chart_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.argClusteringEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        strings.argClusteringTotalArgs(clustering.totalArgumentsClustered),
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w800,
                          color: visual.foreground,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            ...clustering.clusters.map((cluster) {
              final clusterColor = _archetypeColor(visual, cluster.archetype);
              final pct = cluster.supportPercentage.toInt();

              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                          decoration: BoxDecoration(
                            color: clusterColor.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(5),
                            border: Border.all(color: clusterColor.withValues(alpha: 0.3)),
                          ),
                          child: Text(
                            _archetypeLabel(strings, cluster.archetype),
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.w700,
                              color: clusterColor,
                            ),
                          ),
                        ),
                        const Spacer(),
                        Text(
                          '%$pct (${cluster.argumentCount})',
                          style: TextStyle(
                            fontSize: 11.5,
                            fontWeight: FontWeight.w800,
                            color: visual.foreground,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(3),
                      child: LinearProgressIndicator(
                        value: (cluster.supportPercentage / 100.0).clamp(0.0, 1.0),
                        backgroundColor: visual.surfaceSunken,
                        valueColor: AlwaysStoppedAnimation<Color>(clusterColor),
                        minHeight: 4.5,
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      cluster.coreThesis,
                      style: TextStyle(
                        fontSize: 11,
                        color: visual.foreground.withValues(alpha: 0.9),
                        height: 1.35,
                      ),
                    ),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}
