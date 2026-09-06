import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/impact_action_tracking_models.dart';

class ImpactActionTrackingCard extends StatelessWidget {
  const ImpactActionTrackingCard({
    required this.action,
    this.onTap,
    super.key,
  });

  final ImpactActionModel action;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _statusColor(visual, action.milestoneStatus);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('impact-action-${action.actionId}'),
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
                  child: Icon(Icons.track_changes_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.actionTrackEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        action.institutionName,
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
                    strings.actionTrackProgressLabel(action.completionPercentage),
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
              action.pledgeTitle,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w700,
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
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      _statusLabel(strings, action.milestoneStatus),
                      style: TextStyle(
                        fontSize: 11.5,
                        fontWeight: FontWeight.w800,
                        color: accent,
                      ),
                    ),
                  ),
                  Text(
                    '${strings.actionTrackTargetLabel} ${action.targetCompletionUtc.split('T').first}',
                    style: TextStyle(
                      fontSize: 10.5,
                      color: visual.mutedForeground,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _statusColor(KefeVisualSystem visual, MilestoneStatusModel status) => switch (status) {
    MilestoneStatusModel.promised => visual.rules,
    MilestoneStatusModel.inProgress => visual.gold,
    MilestoneStatusModel.deliveredVerified => visual.empathy,
    MilestoneStatusModel.delayedOrBroken => visual.burgundy,
  };

  String _statusLabel(KefeStrings strings, MilestoneStatusModel status) => switch (status) {
    MilestoneStatusModel.promised => strings.actionTrackStatusPromised,
    MilestoneStatusModel.inProgress => strings.actionTrackStatusProgress,
    MilestoneStatusModel.deliveredVerified => strings.actionTrackStatusDelivered,
    MilestoneStatusModel.delayedOrBroken => strings.actionTrackStatusBroken,
  };
}
