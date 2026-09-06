import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/process_analysis_models.dart';

class ProcessAnalysisCard extends StatelessWidget {
  const ProcessAnalysisCard({
    required this.analysis,
    this.onTap,
    super.key,
  });

  final ProcessAnalysisModel analysis;
  final VoidCallback? onTap;

  Color _accentForScore(KefeVisualSystem visual, double score) {
    if (score >= 0.75) return visual.success;
    if (score >= 0.45) return visual.rules;
    return visual.attention;
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _accentForScore(visual, analysis.proceduralIntegrityScore);
    final pct = (analysis.proceduralIntegrityScore * 100).toInt();

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('process-analysis-${analysis.analysisId}'),
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
                  child: Icon(Icons.account_tree_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.processAnalysisEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        strings.processAnalysisIntegrityLabel(pct),
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w800,
                          color: visual.foreground,
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: visual.surfaceSunken,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                  ),
                  child: Text(
                    analysis.transparencyLevel,
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.w700,
                      color: accent,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: analysis.proceduralIntegrityScore.clamp(0.0, 1.0),
                backgroundColor: visual.surfaceSunken,
                valueColor: AlwaysStoppedAnimation<Color>(accent),
                minHeight: 6,
              ),
            ),
            const SizedBox(height: 14),
            Text(
              strings.processAnalysisCurrentStage(analysis.currentStage),
              style: TextStyle(
                fontSize: 11.5,
                fontWeight: FontWeight.w700,
                color: visual.mutedForeground,
              ),
            ),
            const SizedBox(height: 10),
            ...analysis.stages.map((stage) {
              final isDone = stage.isCompleted;
              final stageColor = isDone ? visual.success : visual.mutedForeground.withValues(alpha: 0.6);

              return Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(
                      isDone ? Icons.check_circle_rounded : Icons.radio_button_unchecked_rounded,
                      size: 16,
                      color: stageColor,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  stage.stageTitle,
                                  style: TextStyle(
                                    fontSize: 11.5,
                                    fontWeight: isDone ? FontWeight.w600 : FontWeight.w400,
                                    color: visual.foreground,
                                  ),
                                ),
                              ),
                              if (stage.durationDays > 0)
                                Text(
                                  strings.processAnalysisDays(stage.durationDays),
                                  style: TextStyle(
                                    fontSize: 10,
                                    color: visual.mutedForeground,
                                  ),
                                ),
                            ],
                          ),
                          if (stage.notes.isNotEmpty)
                            Padding(
                              padding: const EdgeInsets.only(top: 2),
                              child: Text(
                                stage.notes,
                                style: TextStyle(
                                  fontSize: 10.5,
                                  color: visual.mutedForeground,
                                ),
                              ),
                            ),
                        ],
                      ),
                    ),
                  ],
                ),
              );
            }),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: visual.border.withValues(alpha: 0.4)),
              ),
              child: Row(
                children: [
                  Icon(Icons.gavel_rounded, size: 14, color: visual.mutedForeground),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      strings.processAnalysisOversightLabel(analysis.oversightBody),
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
