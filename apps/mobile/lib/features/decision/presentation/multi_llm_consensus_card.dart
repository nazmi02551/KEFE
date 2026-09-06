import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/multi_llm_consensus_models.dart';

class MultiLlmConsensusCard extends StatelessWidget {
  const MultiLlmConsensusCard({
    required this.consensus,
    this.onTap,
    super.key,
  });

  final MultiLlmConsensusModel consensus;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _levelColor(visual, consensus.agreementLevel);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('multi-llm-${consensus.consensusId}'),
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
                  child: Icon(Icons.join_inner_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.multiLlmEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _levelLabel(strings, consensus.agreementLevel),
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
                    strings.multiLlmConvergenceLabel((consensus.semanticConvergenceScore * 100).toInt()),
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
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: visual.border.withValues(alpha: 0.5)),
              ),
              child: Text(
                consensus.synthesizedConsensusOutput,
                style: TextStyle(
                  fontSize: 11.5,
                  color: visual.foreground,
                ),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              strings.multiLlmModelsLabel(consensus.modelsEvaluatedCount),
              style: TextStyle(
                fontSize: 10.5,
                fontWeight: FontWeight.w700,
                color: visual.gold,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _levelColor(KefeVisualSystem visual, ModelAgreementLevelModel level) => switch (level) {
    ModelAgreementLevelModel.unanimousCrossModelConsensus => const Color(0xFF10B981),
    ModelAgreementLevelModel.majorityConvergentSynthesis => visual.gold,
    ModelAgreementLevelModel.modelDivergenceReviewRequired => visual.empathy,
  };

  String _levelLabel(KefeStrings strings, ModelAgreementLevelModel level) => switch (level) {
    ModelAgreementLevelModel.unanimousCrossModelConsensus => strings.multiLlmLvlUnanimous,
    ModelAgreementLevelModel.majorityConvergentSynthesis => strings.multiLlmLvlMajority,
    ModelAgreementLevelModel.modelDivergenceReviewRequired => strings.multiLlmLvlDivergence,
  };
}
