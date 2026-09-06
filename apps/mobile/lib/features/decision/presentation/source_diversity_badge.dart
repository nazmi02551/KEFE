import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/source_diversity_models.dart';

class SourceDiversityBadge extends StatelessWidget {
  const SourceDiversityBadge({
    required this.diversity,
    this.onTap,
    super.key,
  });

  final SourceDiversityModel diversity;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final levelColor = _levelColor(visual, diversity.diversityLevel);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(18),
      child: KefeSurface(
        key: ValueKey('source-diversity-${diversity.caseVersionId}'),
        tone: KefeSurfaceTone.raised,
        padding: const EdgeInsets.all(14),
        borderRadius: 18,
        accent: levelColor,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Container(
                  width: 32,
                  height: 32,
                  decoration: BoxDecoration(
                    color: levelColor.withValues(alpha: visual.isDark ? 0.18 : 0.10),
                    borderRadius: BorderRadius.circular(9),
                    border: Border.all(color: levelColor.withValues(alpha: 0.3)),
                  ),
                  child: Icon(Icons.hub_outlined, color: levelColor, size: 16),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.diversityEyebrow, color: levelColor),
                      const SizedBox(height: 2),
                      Text(
                        _levelLabel(strings, diversity.diversityLevel),
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w800,
                          color: visual.foreground,
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                  decoration: BoxDecoration(
                    color: visual.surfaceSunken,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: visual.border.withValues(alpha: 0.6)),
                  ),
                  child: Text(
                    '${diversity.totalSources} kaynak',
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.w700,
                      color: visual.mutedForeground,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: diversity.breakdown.map((cat) {
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: visual.surfaceSunken,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(_categoryIcon(cat.category), size: 12, color: visual.rules),
                      const SizedBox(width: 4),
                      Text(
                        _categoryLabel(strings, cat.category),
                        style: TextStyle(
                          fontSize: 10.5,
                          fontWeight: FontWeight.w600,
                          color: visual.foreground,
                        ),
                      ),
                      const SizedBox(width: 4),
                      Text(
                        '(%${cat.percentage.toStringAsFixed(0)})',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w800,
                          color: visual.goldSoft,
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Color _levelColor(KefeVisualTheme visual, DiversityLevelModel level) =>
      switch (level) {
        DiversityLevelModel.highDiversity => visual.rules,
        DiversityLevelModel.balancedDiversity => visual.gold,
        DiversityLevelModel.limitedDiversity => visual.attention,
      };

  String _levelLabel(KefeStrings strings, DiversityLevelModel level) =>
      switch (level) {
        DiversityLevelModel.highDiversity => strings.diversityLevelHigh,
        DiversityLevelModel.balancedDiversity => strings.diversityLevelBalanced,
        DiversityLevelModel.limitedDiversity => strings.diversityLevelLimited,
      };

  IconData _categoryIcon(SourcePluralityCategoryModel cat) => switch (cat) {
    SourcePluralityCategoryModel.academicScientific => Icons.school_outlined,
    SourcePluralityCategoryModel.officialGovernment => Icons.account_balance_outlined,
    SourcePluralityCategoryModel.civicIndependent => Icons.groups_2_outlined,
    SourcePluralityCategoryModel.mainstreamJournalism => Icons.newspaper_outlined,
    SourcePluralityCategoryModel.technicalIndustry => Icons.precision_manufacturing_outlined,
  };

  String _categoryLabel(
    KefeStrings strings,
    SourcePluralityCategoryModel cat,
  ) =>
      switch (cat) {
        SourcePluralityCategoryModel.academicScientific => strings.diversityCatAcademic,
        SourcePluralityCategoryModel.officialGovernment => strings.diversityCatGov,
        SourcePluralityCategoryModel.civicIndependent => strings.diversityCatCivic,
        SourcePluralityCategoryModel.mainstreamJournalism =>
            strings.diversityCatJournalism,
        SourcePluralityCategoryModel.technicalIndustry => strings.diversityCatIndustry,
      };
}
