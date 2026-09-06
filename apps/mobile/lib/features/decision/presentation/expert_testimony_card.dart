import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/expert_testimony_models.dart';

class ExpertTestimonyCard extends StatelessWidget {
  const ExpertTestimonyCard({
    required this.testimony,
    this.onTap,
    super.key,
  });

  final ExpertTestimonyModel testimony;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _tierColor(visual, testimony.epistemicAuthorityTier);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('expert-testimony-${testimony.testimonyId}'),
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
                  child: Icon(Icons.psychology_alt_rounded, color: accent, size: 20),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.expertEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        testimony.sourceName,
                        style: TextStyle(
                          fontSize: 12.5,
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
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: visual.border.withValues(alpha: 0.5)),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    _tierLabel(strings, testimony.epistemicAuthorityTier),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: accent,
                    ),
                  ),
                  Text(
                    strings.expertCoiLabel((testimony.conflictOfInterestScore * 100).toInt()),
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.w600,
                      color: visual.mutedForeground,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 10),
            Text(
              testimony.testimonyStatement,
              style: TextStyle(
                fontSize: 12,
                color: visual.foreground,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _tierColor(KefeVisualTheme visual, EpistemicAuthorityTierModel tier) =>
      switch (tier) {
        EpistemicAuthorityTierModel.highPeerReviewed => visual.rules,
        EpistemicAuthorityTierModel.officialRegulatory => visual.gold,
        EpistemicAuthorityTierModel.partisanSpecialInterest => visual.attention,
      };

  String _tierLabel(KefeStrings strings, EpistemicAuthorityTierModel tier) =>
      switch (tier) {
        EpistemicAuthorityTierModel.highPeerReviewed => strings.expertTierAcademic,
        EpistemicAuthorityTierModel.officialRegulatory => strings.expertTierRegulatory,
        EpistemicAuthorityTierModel.partisanSpecialInterest =>
            strings.expertTierPartisan,
      };
}
