import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/stakeholder_impact_models.dart';

class StakeholderImpactCard extends StatelessWidget {
  const StakeholderImpactCard({
    required this.matrix,
    super.key,
  });

  final StakeholderImpactMatrixModel matrix;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = visual.rules;

    return KefeSurface(
      key: ValueKey('stakeholder-impact-${matrix.caseVersionId}-${matrix.optionCode}'),
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
                child: Icon(Icons.groups_3_outlined, color: accent, size: 18),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    KefeEyebrow(strings.stakeholderMatrixEyebrow, color: accent),
                    const SizedBox(height: 2),
                    Text(
                      strings.stakeholderMatrixNetScore(matrix.netEquityScore),
                      style: TextStyle(
                        fontSize: 11.5,
                        fontWeight: FontWeight.w800,
                        color: matrix.netEquityScore >= 0 ? visual.success : visual.empathy,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          ...matrix.impactItems.map((item) {
            final isPositive = item.impactScore > 0;
            final isZero = item.impactScore == 0;
            final color = isZero ? visual.mutedForeground : (isPositive ? visual.success : visual.empathy);

            return Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: visual.surfaceSunken.withValues(alpha: 0.6),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          _groupLabel(strings, item.group),
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w800,
                            color: visual.foreground,
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: color.withValues(alpha: visual.isDark ? 0.2 : 0.1),
                            borderRadius: BorderRadius.circular(6),
                            border: Border.all(color: color.withValues(alpha: 0.3)),
                          ),
                          child: Text(
                            item.impactScore >= 0 ? '+${item.impactScore}' : '${item.impactScore}',
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w900,
                              color: color,
                            ),
                          ),
                        ),
                      ],
                    ),
                    if (item.description.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Text(
                        item.description,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: visual.mutedForeground,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            );
          }),
        ],
      ),
    );
  }

  String _groupLabel(KefeStrings strings, StakeholderGroupTypeModel group) =>
      switch (group) {
        StakeholderGroupTypeModel.directUsers => strings.stakeholderGroupDirectUsers,
        StakeholderGroupTypeModel.workers => strings.stakeholderGroupWorkers,
        StakeholderGroupTypeModel.vulnerableGroups =>
            strings.stakeholderGroupVulnerable,
        StakeholderGroupTypeModel.taxpayers => strings.stakeholderGroupTaxpayers,
        StakeholderGroupTypeModel.futureGenerations => strings.stakeholderGroupFuture,
      };
}
