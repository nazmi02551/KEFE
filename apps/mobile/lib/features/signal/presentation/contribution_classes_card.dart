import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/contribution_classes_models.dart';

class ContributionClassesCard extends StatelessWidget {
  const ContributionClassesCard({
    required this.report,
    this.onTap,
    super.key,
  });

  final ContributionClassesReportModel report;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = visual.rules;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('contrib-classes-${report.caseVersionId}'),
        tone: KefeSurfaceTone.raised,
        padding: const EdgeInsets.all(18),
        borderRadius: 22,
        accent: accent,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header Row
            Row(
              children: [
                Container(
                  width: 38,
                  height: 38,
                  decoration: BoxDecoration(
                    color: accent.withValues(alpha: visual.isDark ? 0.18 : 0.10),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: accent.withValues(alpha: 0.3)),
                  ),
                  child: Icon(Icons.pie_chart_outline_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.contribClassesEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        strings.contribClassesTitle,
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w800,
                          color: visual.foreground,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Isolation Status & Total Badge
            Row(
              children: [
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                    decoration: BoxDecoration(
                      color: accent.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: accent.withValues(alpha: 0.3)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.shield_rounded, size: 14, color: accent),
                        const SizedBox(width: 6),
                        Flexible(
                          child: Text(
                            report.isolationAuditStatus == 'ENFORCED'
                                ? strings.contribClassesIsolationEnforced
                                : strings.contribClassesIsolationBreached,
                            style: TextStyle(
                              fontSize: 10.5,
                              fontWeight: FontWeight.w800,
                              color: accent,
                            ),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
                  decoration: BoxDecoration(
                    color: visual.surfaceSunken,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                  ),
                  child: Text(
                    strings.contribClassesTotalLabel(report.totalContributions),
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.w700,
                      color: visual.mutedForeground,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),

            // Classes Breakdown Cards
            ...report.classes.map((c) {
              final isCore = c.classId == ContributionClassIdModel.corePreResult;
              final classAccent = isCore ? visual.rules : (c.classId == ContributionClassIdModel.exposed ? visual.gold : visual.empathy);

              return Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: visual.surfaceSunken,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: isCore
                        ? accent.withValues(alpha: 0.4)
                        : visual.border.withValues(alpha: 0.4),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            strings.selectLocale(c.nameTr, c.nameEn),
                            style: TextStyle(
                              fontSize: 12.5,
                              fontWeight: FontWeight.w800,
                              color: visual.foreground,
                            ),
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: classAccent.withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(4),
                            border: Border.all(color: classAccent.withValues(alpha: 0.3)),
                          ),
                          child: Text(
                            c.isSignalEligible
                                ? strings.contribClassesEligibleBadge
                                : strings.contribClassesIsolatedBadge,
                            style: TextStyle(
                              fontSize: 9.5,
                              fontWeight: FontWeight.w800,
                              color: classAccent,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      c.description,
                      style: TextStyle(
                        fontSize: 10.5,
                        fontWeight: FontWeight.w500,
                        color: visual.mutedForeground,
                        height: 1.3,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(4),
                            child: LinearProgressIndicator(
                              value: c.percentage / 100.0,
                              backgroundColor: visual.surface,
                              valueColor: AlwaysStoppedAnimation(classAccent),
                              minHeight: 6,
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Text(
                          '${c.count} (%${c.percentage.toStringAsFixed(1)})',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w800,
                            color: visual.foreground,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              );
            }),

            const SizedBox(height: 6),

            // Proof Hash
            Text(
              strings.contribClassesProofLabel(report.isolationProofHash.substring(0, 16)),
              style: TextStyle(
                fontSize: 9.5,
                fontWeight: FontWeight.w600,
                color: visual.mutedForeground.withValues(alpha: 0.7),
                fontFamily: 'monospace',
              ),
            ),
          ],
        ),
      ),
    );
  }
}
