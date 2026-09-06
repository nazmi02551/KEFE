import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/responsibility_analysis_models.dart';

class ResponsibilityAnalysisCard extends StatelessWidget {
  const ResponsibilityAnalysisCard({
    required this.analysis,
    this.onTap,
    super.key,
  });

  final ResponsibilityAnalysisModel analysis;
  final VoidCallback? onTap;

  String _dutyLabel(KefeStrings strings, String duty) => switch (duty) {
    'LEGAL_LIABILITY' => strings.respAnalysisDutyLegal,
    'REGULATORY_OVERSIGHT' => strings.respAnalysisDutyOversight,
    'OPERATIONAL_EXECUTION' => strings.respAnalysisDutyExecution,
    'FIDUCIARY_ETHICAL_DUTY' => strings.respAnalysisDutyEthical,
    _ => duty,
  };

  Color _dutyColor(KefeVisualSystem visual, String duty) => switch (duty) {
    'LEGAL_LIABILITY' => visual.rules,
    'REGULATORY_OVERSIGHT' => visual.gold,
    'OPERATIONAL_EXECUTION' => visual.success,
    'FIDUCIARY_ETHICAL_DUTY' => visual.empathy,
    _ => visual.mutedForeground,
  };

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = analysis.hasAccountabilityGap ? visual.attention : visual.rules;
    final clarityPct = (analysis.clarityScore * 100).toInt();

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('resp-analysis-${analysis.analysisId}'),
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
                  child: Icon(Icons.balance_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.respAnalysisEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        strings.respAnalysisClarityLabel(clarityPct),
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
            if (analysis.hasAccountabilityGap) ...[
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                decoration: BoxDecoration(
                  color: visual.attention.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: visual.attention.withValues(alpha: 0.35)),
                ),
                child: Row(
                  children: [
                    Icon(Icons.warning_amber_rounded, size: 16, color: visual.attention),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        analysis.gapExplanation ?? strings.respAnalysisGapWarning,
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: visual.attention,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
            const SizedBox(height: 14),
            ...analysis.actorAllocations.map((actor) {
              final sharePct = (actor.responsibilityShare * 100).toInt();
              final dutyColor = _dutyColor(visual, actor.dutyNature);

              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            actor.actorName,
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                              color: visual.foreground,
                            ),
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2.5),
                          decoration: BoxDecoration(
                            color: dutyColor.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(4),
                            border: Border.all(color: dutyColor.withValues(alpha: 0.3)),
                          ),
                          child: Text(
                            _dutyLabel(strings, actor.dutyNature),
                            style: TextStyle(
                              fontSize: 9.5,
                              fontWeight: FontWeight.w700,
                              color: dutyColor,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          '%$sharePct',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w800,
                            color: visual.foreground,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 5),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(3),
                      child: LinearProgressIndicator(
                        value: actor.responsibilityShare.clamp(0.0, 1.0),
                        backgroundColor: visual.surfaceSunken,
                        valueColor: AlwaysStoppedAnimation<Color>(dutyColor),
                        minHeight: 4.5,
                      ),
                    ),
                    if (actor.jurisdictionScope.isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.only(top: 4),
                        child: Text(
                          actor.jurisdictionScope,
                          style: TextStyle(
                            fontSize: 10,
                            color: visual.mutedForeground,
                          ),
                        ),
                      ),
                  ],
                ),
              );
            }),
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: visual.border.withValues(alpha: 0.4)),
              ),
              child: Row(
                children: [
                  Icon(Icons.account_balance_rounded, size: 14, color: visual.mutedForeground),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      strings.respAnalysisRedressLabel(analysis.legalRedressChannel),
                      style: TextStyle(
                        fontSize: 10.5,
                        fontWeight: FontWeight.w600,
                        color: visual.mutedForeground,
                      ),
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
}
