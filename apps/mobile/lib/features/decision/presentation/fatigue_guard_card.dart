import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/fatigue_guard_models.dart';

class FatigueGuardCard extends StatelessWidget {
  const FatigueGuardCard({
    required this.guard,
    this.onTap,
    super.key,
  });

  final DecisionFatigueModel guard;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _statusColor(visual, guard.pacingStatus);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('fatigue-guard-${guard.sessionId}'),
        tone: KefeSurfaceTone.raised,
        padding: const EdgeInsets.all(18),
        borderRadius: 22,
        accent: accent,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: accent.withValues(alpha: visual.isDark ? 0.18 : 0.10),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: accent.withValues(alpha: 0.3)),
                  ),
                  child: Icon(Icons.self_improvement_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.fatigueEyebrow, color: accent),
                      const SizedBox(height: 3),
                      Text(
                        _statusLabel(strings, guard.pacingStatus),
                        style: TextStyle(
                          fontSize: 12.5,
                          fontWeight: FontWeight.w800,
                          color: visual.foreground,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
                        decoration: BoxDecoration(
                          color: visual.surfaceSunken,
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                        ),
                        child: Text(
                          strings.fatigueCountLabel(guard.consecutiveWeighCount),
                          style: TextStyle(
                            fontSize: 10.5,
                            fontWeight: FontWeight.w800,
                            color: accent,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              strings.fatigueDurationLabel(guard.sessionDurationMinutes.toInt()),
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w700,
                color: visual.mutedForeground,
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
                guard.gentleRecommendationPrompt,
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

  Color _statusColor(KefeVisualSystem visual, PacingStatusModel status) => switch (status) {
    PacingStatusModel.optimalPacing => visual.rules,
    PacingStatusModel.pacingRecommended => visual.gold,
    PacingStatusModel.restIntervalActive => visual.empathy,
  };

  String _statusLabel(KefeStrings strings, PacingStatusModel status) => switch (status) {
    PacingStatusModel.optimalPacing => strings.fatigueStatusOptimal,
    PacingStatusModel.pacingRecommended => strings.fatigueStatusRecommended,
    PacingStatusModel.restIntervalActive => strings.fatigueStatusRest,
  };
}
