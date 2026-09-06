import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/civic_petition_simulator_models.dart';

class CivicPetitionSimulatorCard extends StatelessWidget {
  const CivicPetitionSimulatorCard({
    required this.petition,
    this.onTap,
    super.key,
  });

  final CivicPetitionModel petition;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _stageColor(visual, petition.stage);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('civic-petition-${petition.petitionId}'),
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
                  child: Icon(Icons.description_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.civPetEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _stageLabel(strings, petition.stage),
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
                    strings.civPetBenefitLabel((petition.projectedNetBenefitScore * 100).toInt()),
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
              petition.billTitle,
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
                strings.civPetSigsLabel(
                  petition.signaturesCount,
                  petition.signatureTargetThreshold,
                ),
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

  Color _stageColor(KefeVisualSystem visual, PetitionStageModel stage) => switch (stage) {
    PetitionStageModel.draftImpactSimulation => visual.gold,
    PetitionStageModel.signatureGatheringCampaign => visual.rules,
    PetitionStageModel.submittedToParliament => const Color(0xFF10B981),
  };

  String _stageLabel(KefeStrings strings, PetitionStageModel stage) => switch (stage) {
    PetitionStageModel.draftImpactSimulation => strings.civPetStDraft,
    PetitionStageModel.signatureGatheringCampaign => strings.civPetStCampaign,
    PetitionStageModel.submittedToParliament => strings.civPetStSubmitted,
  };
}
