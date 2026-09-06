import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/citizen_jury_chamber_models.dart';

class CitizenJuryChamberCard extends StatelessWidget {
  const CitizenJuryChamberCard({
    required this.jury,
    this.onTap,
    super.key,
  });

  final CitizenJuryModel jury;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _stageColor(visual, jury.stage);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('citizen-jury-${jury.juryId}'),
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
                  child: Icon(Icons.gavel_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.citJuryEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _stageLabel(strings, jury.stage),
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
                    strings.citJuryConsensusLabel((jury.verdictConsensusRate * 100).toInt()),
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
            Text(
              jury.dilemmaTitle,
              style: TextStyle(
                fontSize: 12.5,
                fontWeight: FontWeight.w800,
                color: visual.foreground,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: visual.border.withValues(alpha: 0.5)),
              ),
              child: Text(
                strings.citJuryPanelLabel(jury.jurorCount, jury.expertWitnessesCount),
                style: TextStyle(
                  fontSize: 11.5,
                  fontWeight: FontWeight.w700,
                  color: visual.gold,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _stageColor(KefeVisualSystem visual, CitizenJuryStageModel stage) => switch (stage) {
    CitizenJuryStageModel.stratifiedPanelAssembly => visual.rules,
    CitizenJuryStageModel.expertHearingsInSession => visual.gold,
    CitizenJuryStageModel.consensusVerdictEmitted => visual.empathy,
  };

  String _stageLabel(KefeStrings strings, CitizenJuryStageModel stage) => switch (stage) {
    CitizenJuryStageModel.stratifiedPanelAssembly => strings.citJuryStAssembly,
    CitizenJuryStageModel.expertHearingsInSession => strings.citJuryStHearings,
    CitizenJuryStageModel.consensusVerdictEmitted => strings.citJuryStVerdict,
  };
}
