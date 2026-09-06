import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/ai_neutrality_facilitator_models.dart';

class AiNeutralityFacilitatorCard extends StatelessWidget {
  const AiNeutralityFacilitatorCard({
    required this.facilitation,
    this.onTap,
    super.key,
  });

  final FacilitationModel facilitation;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _modeColor(visual, facilitation.mode);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('ai-fac-${facilitation.interventionId}'),
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
                  child: Icon(Icons.forum_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.aiFacEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _modeLabel(strings, facilitation.mode),
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
                    strings.aiFacNeutralityLabel((facilitation.neutralityIndex * 100).toInt()),
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
                facilitation.facilitationPromptText,
                style: TextStyle(
                  fontSize: 11.5,
                  color: visual.foreground,
                ),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              strings.aiFacDeescalationLabel((facilitation.deescalationEfficacyScore * 100).toInt()),
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

  Color _modeColor(KefeVisualSystem visual, FacilitationModeModel mode) => switch (mode) {
    FacilitationModeModel.socraticInquiryPrompt => visual.rules,
    FacilitationModeModel.nonviolentReframingSynthesis => visual.gold,
    FacilitationModeModel.commonGroundSurfacing => const Color(0xFF10B981),
  };

  String _modeLabel(KefeStrings strings, FacilitationModeModel mode) => switch (mode) {
    FacilitationModeModel.socraticInquiryPrompt => strings.aiFacModeSocratic,
    FacilitationModeModel.nonviolentReframingSynthesis => strings.aiFacModeReframing,
    FacilitationModeModel.commonGroundSurfacing => strings.aiFacModeGround,
  };
}
