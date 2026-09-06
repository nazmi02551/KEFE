import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/civic_literacy_workshop_models.dart';

class CivicLiteracyWorkshopCard extends StatelessWidget {
  const CivicLiteracyWorkshopCard({
    required this.workshop,
    this.onTap,
    super.key,
  });

  final CivicLiteracyWorkshopModel workshop;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _moduleColor(visual, workshop.moduleType);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('civic-workshop-${workshop.workshopId}'),
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
                  child: Icon(Icons.school_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.civicWorkEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _moduleLabel(strings, workshop.moduleType),
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
                    strings.civicWorkScoreLabel((workshop.comprehensionScore * 100).toInt()),
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
              workshop.moduleTitle,
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
                strings.civicWorkProgressLabel(
                  workshop.completedDrills,
                  workshop.totalDrills,
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

  Color _moduleColor(KefeVisualSystem visual, LiteracyModuleTypeModel module) => switch (module) {
    LiteracyModuleTypeModel.fallacySpotting => visual.burgundy,
    LiteracyModuleTypeModel.ethicalFrameworks => visual.rules,
    LiteracyModuleTypeModel.evidenceEvaluation => visual.gold,
    LiteracyModuleTypeModel.bridgeSynthesis => visual.empathy,
  };

  String _moduleLabel(KefeStrings strings, LiteracyModuleTypeModel module) => switch (module) {
    LiteracyModuleTypeModel.fallacySpotting => strings.civicWorkModFallacy,
    LiteracyModuleTypeModel.ethicalFrameworks => strings.civicWorkModEthics,
    LiteracyModuleTypeModel.evidenceEvaluation => strings.civicWorkModEvidence,
    LiteracyModuleTypeModel.bridgeSynthesis => strings.civicWorkModBridge,
  };
}
