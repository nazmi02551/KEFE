import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/stakeholder_distribution_models.dart';

class StakeholderDistributionCard extends StatelessWidget {
  const StakeholderDistributionCard({
    required this.distribution,
    this.onTap,
    super.key,
  });

  final StakeholderDistributionModel distribution;
  final VoidCallback? onTap;

  Color _categoryColor(KefeVisualSystem visual, String category) => switch (category) {
    'DIRECTLY_IMPACTED' => visual.rules,
    'FRONTLINE_PRACTITIONERS' => visual.gold,
    'COMMERCIAL_ENTERPRISES' => visual.empathy,
    'REGULATORY_OVERSIGHT' => visual.success,
    'CIVIC_COMMUNITY' => visual.attention,
    _ => visual.mutedForeground,
  };

  String _categoryLabel(KefeStrings strings, String category) => switch (category) {
    'DIRECTLY_IMPACTED' => strings.stakeholderDistRoleDirectlyImpacted,
    'FRONTLINE_PRACTITIONERS' => strings.stakeholderDistRoleFrontline,
    'COMMERCIAL_ENTERPRISES' => strings.stakeholderDistRoleCommercial,
    'REGULATORY_OVERSIGHT' => strings.stakeholderDistRoleRegulatory,
    'CIVIC_COMMUNITY' => strings.stakeholderDistRoleCivic,
    _ => category,
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
        key: ValueKey('stakeholder-dist-${distribution.caseVersionId}'),
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
                  child: Icon(Icons.groups_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.stakeholderDistEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        strings.stakeholderDistTitle,
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
                    color: accent.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: accent.withValues(alpha: 0.28)),
                  ),
                  child: Text(
                    strings.stakeholderDistTotalRepresented(
                      distribution.totalStakeholdersRepresented,
                    ),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: accent,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: visual.gold.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: visual.gold.withValues(alpha: 0.28)),
                  ),
                  child: Text(
                    strings.stakeholderDistPluralismScore(
                      '${(distribution.pluralismScore * 100).toInt()}%',
                    ),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: visual.gold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            ...distribution.stakeholderDistributions.map((item) {
              final color = _categoryColor(visual, item.category);
              final isPositive = item.divergenceFromOverallPoints >= 0;

              return Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: visual.isDark
                      ? Colors.white.withValues(alpha: 0.03)
                      : Colors.black.withValues(alpha: 0.02),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: color.withValues(alpha: 0.25)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Row(
                      children: [
                        Container(
                          width: 8,
                          height: 8,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: color,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                _categoryLabel(strings, item.category).toUpperCase(),
                                style: TextStyle(
                                  fontSize: 9,
                                  fontWeight: FontWeight.w700,
                                  letterSpacing: 0.6,
                                  color: color,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                item.name,
                                style: TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.w600,
                                  color: visual.foreground,
                                ),
                              ),
                            ],
                          ),
                        ),
                        Text(
                          '${item.participantCount} (%${(item.sampleShare * 100).toInt()})',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w500,
                            color: visual.mutedForeground,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          isPositive
                              ? strings.stakeholderDistDivergencePositive(
                                  item.divergenceFromOverallPoints,
                                )
                              : strings.stakeholderDistDivergenceNegative(
                                  item.divergenceFromOverallPoints.abs(),
                                ),
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: isPositive ? visual.rules : visual.empathy,
                          ),
                        ),
                        Text(
                          strings.stakeholderDistCohesionLabel(
                            '${(item.cohesionIndex * 100).toInt()}%',
                          ),
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w500,
                            color: visual.mutedForeground,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: Row(
                        children: item.optionShares.entries.map((entry) {
                          final share = entry.value;
                          final optColor = entry.key == 'A'
                              ? visual.rules
                              : visual.empathy;
                          return Expanded(
                            flex: (share * 1000).toInt(),
                            child: Container(
                              height: 8,
                              color: optColor.withValues(alpha: 0.85),
                            ),
                          );
                        }).toList(),
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
