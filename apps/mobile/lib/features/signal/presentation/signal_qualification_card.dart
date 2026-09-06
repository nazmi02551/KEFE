import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/signal_qualification_models.dart';

class SignalQualificationCard extends StatelessWidget {
  const SignalQualificationCard({
    required this.report,
    this.onTap,
    super.key,
  });

  final SignalQualificationReportModel report;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _tierColor(visual, report.qualificationTier);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('signal-qualification-${report.signalId}'),
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
                  child: Icon(Icons.verified_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.signalQualEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        strings.signalQualTitle,
                        style: TextStyle(
                          fontSize: 14.5,
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

            // Tier & Status Badges
            Wrap(
              spacing: 8,
              runSpacing: 6,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: accent.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: accent.withValues(alpha: 0.4)),
                  ),
                  child: Text(
                    _tierLabel(strings, report.qualificationTier),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      color: accent,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: visual.surfaceSunken,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                  ),
                  child: Text(
                    _statusLabel(strings, report.qualificationStatus),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: visual.mutedForeground,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: visual.surfaceSunken,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                  ),
                  child: Text(
                    strings.signalQualScoreLabel((report.overallScore * 100).round()),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: visual.foreground,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: visual.surfaceSunken,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                  ),
                  child: Text(
                    strings.signalQualSampleLabel(report.sampleSize),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: visual.mutedForeground,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),

            // Criteria Breakdown
            Text(
              report.caseTitle,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w700,
                color: visual.foreground,
              ),
            ),
            const SizedBox(height: 10),

            ...report.criteria.map((c) => Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Row(
                children: [
                  Icon(
                    c.isPassed ? Icons.check_circle_rounded : Icons.cancel_rounded,
                    size: 15,
                    color: c.isPassed ? visual.rules : visual.burgundy,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      strings.selectLocale(c.nameTr, c.nameEn),
                      style: TextStyle(
                        fontSize: 11.5,
                        fontWeight: FontWeight.w600,
                        color: visual.foreground,
                      ),
                    ),
                  ),
                  Text(
                    '${(c.score * 100).toInt()}%',
                    style: TextStyle(
                      fontSize: 11.5,
                      fontWeight: FontWeight.w700,
                      color: c.isPassed ? visual.foreground : visual.burgundy,
                    ),
                  ),
                ],
              ),
            )),

            // Eligible Dissemination Channels
            if (report.eligibleChannels.isNotEmpty) ...[
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: visual.surfaceSunken,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: visual.border.withValues(alpha: 0.4)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      strings.signalQualChannelsTitle,
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        color: visual.gold,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Wrap(
                      spacing: 6,
                      runSpacing: 4,
                      children: report.eligibleChannels.map((channel) => Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: visual.surface,
                          borderRadius: BorderRadius.circular(4),
                          border: Border.all(color: visual.border.withValues(alpha: 0.3)),
                        ),
                        child: Text(
                          channel.replaceAll('_', ' '),
                          style: TextStyle(
                            fontSize: 9.5,
                            fontWeight: FontWeight.w700,
                            color: visual.mutedForeground,
                          ),
                        ),
                      )).toList(),
                    ),
                  ],
                ),
              ),
            ],

            const SizedBox(height: 10),

            // Audit Hash
            Text(
              strings.signalQualAuditHashLabel(report.qualificationAuditHash.substring(0, 16)),
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

  Color _tierColor(KefeVisualSystem visual, SignalQualificationTierModel tier) => switch (tier) {
    SignalQualificationTierModel.goldStandard => visual.gold,
    SignalQualificationTierModel.silverValidated => visual.rules,
    SignalQualificationTierModel.bronzeObserved => visual.empathy,
    SignalQualificationTierModel.unqualified => visual.mutedForeground,
  };

  String _tierLabel(KefeStrings strings, SignalQualificationTierModel tier) => switch (tier) {
    SignalQualificationTierModel.goldStandard => strings.signalQualTierGold,
    SignalQualificationTierModel.silverValidated => strings.signalQualTierSilver,
    SignalQualificationTierModel.bronzeObserved => strings.signalQualTierBronze,
    SignalQualificationTierModel.unqualified => strings.signalQualTierUnqualified,
  };

  String _statusLabel(KefeStrings strings, SignalQualificationStatusModel status) => switch (status) {
    SignalQualificationStatusModel.qualified => strings.signalQualStatusQualified,
    SignalQualificationStatusModel.provisional => strings.signalQualStatusProvisional,
    SignalQualificationStatusModel.disqualified => strings.signalQualStatusDisqualified,
  };
}
