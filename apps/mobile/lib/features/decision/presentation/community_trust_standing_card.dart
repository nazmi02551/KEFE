import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/community_trust_standing_models.dart';

class CommunityTrustStandingCard extends StatelessWidget {
  const CommunityTrustStandingCard({
    required this.standing,
    this.onTap,
    super.key,
  });

  final CommunityTrustStandingModel standing;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _tierColor(visual, standing.standingTier);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('trust-standing-${standing.userPseudonymId}'),
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
                  child: Icon(Icons.verified_user_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.trustStandEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _tierLabel(strings, standing.standingTier),
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
                    strings.trustStandScoreLabel((standing.trustScore * 100).toInt()),
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
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: visual.border.withValues(alpha: 0.5)),
              ),
              child: Text(
                strings.trustStandStatsLabel(
                  standing.bridgeArgumentCount,
                  standing.verifiedWeighCount,
                ),
                style: TextStyle(
                  fontSize: 11.5,
                  fontWeight: FontWeight.w700,
                  color: visual.foreground,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _tierColor(KefeVisualSystem visual, StandingTierModel tier) => switch (tier) {
    StandingTierModel.exemplaryContributor => visual.rules,
    StandingTierModel.establishedParticipant => visual.gold,
    StandingTierModel.activeExplorer => visual.empathy,
    StandingTierModel.restrictedOrProbationary => visual.burgundy,
  };

  String _tierLabel(KefeStrings strings, StandingTierModel tier) => switch (tier) {
    StandingTierModel.exemplaryContributor => strings.trustStandTierExemplary,
    StandingTierModel.establishedParticipant => strings.trustStandTierEstablished,
    StandingTierModel.activeExplorer => strings.trustStandTierActive,
    StandingTierModel.restrictedOrProbationary => strings.trustStandTierProbation,
  };
}
