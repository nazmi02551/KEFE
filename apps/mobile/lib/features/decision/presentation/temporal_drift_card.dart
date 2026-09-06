import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/temporal_drift_models.dart';

class TemporalDriftCard extends StatelessWidget {
  const TemporalDriftCard({
    required this.drift,
    this.onTap,
    super.key,
  });

  final TemporalDriftModel drift;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _driftColor(visual, drift.driftNature);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('temporal-drift-${drift.caseVersionId}'),
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
                  child: Icon(Icons.timelapse_rounded, color: accent, size: 20),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.driftEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _natureLabel(strings, drift.driftNature),
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
                  padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3.5),
                  decoration: BoxDecoration(
                    color: visual.surfaceSunken,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                  ),
                  child: Text(
                    strings.driftDaysElapsed(drift.timeElapsedDays),
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.w700,
                      color: visual.mutedForeground,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: visual.surfaceSunken.withValues(alpha: 0.6),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: visual.border.withValues(alpha: 0.5)),
              ),
              child: Text(
                drift.isShifted
                    ? strings.driftShiftedSummary(
                        drift.initialOptionCode,
                        drift.retestOptionCode,
                      )
                    : strings.driftUnchangedSummary,
                style: TextStyle(
                  fontSize: 12.5,
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

  Color _driftColor(KefeVisualTheme visual, DriftNatureModel nature) =>
      switch (nature) {
        DriftNatureModel.stableConviction => visual.rules,
        DriftNatureModel.maturedRevision => visual.gold,
        DriftNatureModel.reinforcedCertainty => visual.success,
        DriftNatureModel.exploratoryShift => visual.empathy,
      };

  String _natureLabel(KefeStrings strings, DriftNatureModel nature) =>
      switch (nature) {
        DriftNatureModel.stableConviction => strings.driftNatureStable,
        DriftNatureModel.maturedRevision => strings.driftNatureMatured,
        DriftNatureModel.reinforcedCertainty => strings.driftNatureReinforced,
        DriftNatureModel.exploratoryShift => strings.driftNatureExploratory,
      };
}
