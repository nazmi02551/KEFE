import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/revolving_door_monitor_models.dart';

class RevolvingDoorMonitorCard extends StatelessWidget {
  const RevolvingDoorMonitorCard({
    required this.transition,
    this.onTap,
    super.key,
  });

  final RevolvingDoorModel transition;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _statusColor(visual, transition.status);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('revolve-door-${transition.transitionId}'),
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
                  child: Icon(Icons.sync_alt_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.revolveEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _statusLabel(strings, transition.status),
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
                    strings.revolveCoolingLabel(transition.coolingOffMonthsObserved),
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
                '${transition.officialNameAnonymized} (${transition.regulatoryAgencySource})',
                style: TextStyle(
                  fontSize: 11.5,
                  color: visual.foreground,
                ),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              strings.revolveCaptureRiskLabel((transition.captureRiskScore * 100).toInt()),
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

  Color _statusColor(KefeVisualSystem visual, TransitionStatusModel status) => switch (status) {
    TransitionStatusModel.coolingOffCompliant => const Color(0xFF10B981),
    TransitionStatusModel.rapidRegulatoryTransitionAlert => visual.gold,
    TransitionStatusModel.provenCaptureVulnerability => visual.empathy,
  };

  String _statusLabel(KefeStrings strings, TransitionStatusModel status) => switch (status) {
    TransitionStatusModel.coolingOffCompliant => strings.revolveStCompliant,
    TransitionStatusModel.rapidRegulatoryTransitionAlert => strings.revolveStRapid,
    TransitionStatusModel.provenCaptureVulnerability => strings.revolveStCapture,
  };
}
