import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/vulnerable_groups_shield_models.dart';

class VulnerableGroupsShieldCard extends StatelessWidget {
  const VulnerableGroupsShieldCard({
    required this.shield,
    this.onTap,
    super.key,
  });

  final VulnerableGroupsShieldModel shield;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _statusColor(visual, shield.overallProtectionStatus);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('vulnerable-shield-${shield.optionCode}'),
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
                  child: Icon(Icons.shield_rounded, color: accent, size: 20),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.vulnerableEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _statusLabel(strings, shield.overallProtectionStatus),
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
                    strings.vulnerableFloorLabel((shield.safetyNetFloorScore * 100).toInt()),
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.w800,
                      color: accent,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Column(
              children: shield.cohortEvaluations.map((item) {
                final isPositive = item.impactScore >= 0.0;
                final cohortColor = isPositive ? visual.rules : visual.attention;

                return Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: visual.surfaceSunken,
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
                              _cohortLabel(strings, item.cohort),
                              style: TextStyle(
                                fontSize: 11.5,
                                fontWeight: FontWeight.w800,
                                color: cohortColor,
                              ),
                            ),
                            Text(
                              '${isPositive ? "+" : ""}${(item.impactScore * 100).toInt()}%',
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w700,
                                color: cohortColor,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          item.assessment,
                          style: TextStyle(
                            fontSize: 11,
                            color: visual.foreground,
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Color _statusColor(KefeVisualTheme visual, ProtectionStatusModel status) =>
      switch (status) {
        ProtectionStatusModel.strongProtectiveFloor => visual.rules,
        ProtectionStatusModel.neutralNoDisproportion => visual.gold,
        ProtectionStatusModel.severeDisproportionateBurden => visual.attention,
      };

  String _statusLabel(KefeStrings strings, ProtectionStatusModel status) =>
      switch (status) {
        ProtectionStatusModel.strongProtectiveFloor =>
            strings.vulnerableStatusStrong,
        ProtectionStatusModel.neutralNoDisproportion =>
            strings.vulnerableStatusNeutral,
        ProtectionStatusModel.severeDisproportionateBurden =>
            strings.vulnerableStatusSevere,
      };

  String _cohortLabel(KefeStrings strings, VulnerableCohortModel cohort) =>
      switch (cohort) {
        VulnerableCohortModel.childrenYouth => strings.vulnerableCohortChildren,
        VulnerableCohortModel.elderlyGeriatric =>
            strings.vulnerableCohortElderly,
        VulnerableCohortModel.lowIncomeImpoverished =>
            strings.vulnerableCohortLowIncome,
        VulnerableCohortModel.personsWithDisabilities =>
            strings.vulnerableCohortDisability,
        VulnerableCohortModel.minorityMarginalized =>
            strings.vulnerableCohortMinority,
      };
}
