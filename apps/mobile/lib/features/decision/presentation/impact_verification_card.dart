import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/impact_verification_models.dart';

class ImpactVerificationCard extends StatelessWidget {
  const ImpactVerificationCard({
    required this.verification,
    this.onTap,
    super.key,
  });

  final ImpactVerificationModel verification;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _verdictColor(visual, verification.outcomeVerdict);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('impact-verify-${verification.verificationId}'),
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
                  child: Icon(Icons.fact_check_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.impactVerEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _verdictLabel(strings, verification.outcomeVerdict),
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
                    strings.impactVerScoreLabel((verification.resolutionScore * 100).toInt()),
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.w800,
                      color: accent,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              strings.impactVerAuditorsLabel(verification.auditorConsensusCount),
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w700,
                color: visual.gold,
              ),
            ),
            const SizedBox(height: 6),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: visual.border.withValues(alpha: 0.5)),
              ),
              child: Text(
                verification.verificationNotes,
                style: TextStyle(
                  fontSize: 11.5,
                  color: visual.foreground,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _verdictColor(KefeVisualSystem visual, OutcomeVerdictModel verdict) => switch (verdict) {
    OutcomeVerdictModel.fullResolution => visual.rules,
    OutcomeVerdictModel.substantialProgress => visual.gold,
    OutcomeVerdictModel.partialSymbolicOnly => visual.empathy,
    OutcomeVerdictModel.rejectedNonCompliant => visual.burgundy,
  };

  String _verdictLabel(KefeStrings strings, OutcomeVerdictModel verdict) => switch (verdict) {
    OutcomeVerdictModel.fullResolution => strings.impactVerVerdictFull,
    OutcomeVerdictModel.substantialProgress => strings.impactVerVerdictProgress,
    OutcomeVerdictModel.partialSymbolicOnly => strings.impactVerVerdictSymbolic,
    OutcomeVerdictModel.rejectedNonCompliant => strings.impactVerVerdictRejected,
  };
}
