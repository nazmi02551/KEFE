import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/action_follow_through_models.dart';

class ActionFollowThroughCard extends StatelessWidget {
  const ActionFollowThroughCard({
    required this.action,
    this.onEvidenceTap,
    super.key,
  });

  final ActionFollowThroughItem action;
  final VoidCallback? onEvidenceTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final statusColor = _statusColor(visual, action.status);

    return KefeSurface(
      key: ValueKey('action-milestone-${action.id}'),
      tone: KefeSurfaceTone.raised,
      padding: const EdgeInsets.all(18),
      borderRadius: 22,
      accent: statusColor,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: statusColor.withValues(alpha: visual.isDark ? 0.16 : 0.08),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: statusColor.withValues(alpha: 0.22)),
                ),
                child: Icon(_statusIcon(action.status), color: statusColor, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        KefeEyebrow(strings.actionEyebrow, color: statusColor),
                        const Spacer(),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2.5),
                          decoration: BoxDecoration(
                            color: statusColor.withValues(alpha: visual.isDark ? 0.18 : 0.10),
                            borderRadius: BorderRadius.circular(6),
                            border: Border.all(color: statusColor.withValues(alpha: 0.3)),
                          ),
                          child: Text(
                            _statusLabel(strings, action.status),
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.w800,
                              color: statusColor,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 5),
                    Text(
                      action.title,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w900,
                        letterSpacing: -0.2,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            action.description,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              height: 1.4,
              color: visual.foreground,
            ),
          ),
          const SizedBox(height: 14),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                strings.actionProgressLabel(action.progressPercentage),
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  color: visual.mutedForeground,
                ),
              ),
              if (action.targetCompletionDate != null)
                Text(
                  strings.actionTargetDate(
                    '${action.targetCompletionDate!.year}-${action.targetCompletionDate!.month.toString().padLeft(2, '0')}-${action.targetCompletionDate!.day.toString().padLeft(2, '0')}',
                  ),
                  style: TextStyle(fontSize: 11, color: visual.mutedForeground),
                ),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: SizedBox(
              height: 6,
              child: LinearProgressIndicator(
                value: (action.progressPercentage / 100).clamp(0.0, 1.0),
                backgroundColor: visual.surfaceSunken,
                valueColor: AlwaysStoppedAnimation<Color>(statusColor),
              ),
            ),
          ),
          if (action.evidenceSummary != null || action.evidenceUrl != null) ...[
            const SizedBox(height: 14),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: visual.surfaceSunken.withValues(alpha: 0.6),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: visual.border.withValues(alpha: 0.5)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (action.evidenceSummary != null)
                    Text(
                      action.evidenceSummary!,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: visual.foreground,
                      ),
                    ),
                  if (action.evidenceUrl != null) ...[
                    const SizedBox(height: 6),
                    InkWell(
                      onTap: onEvidenceTap,
                      borderRadius: BorderRadius.circular(6),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.link_rounded, size: 14, color: visual.goldSoft),
                          const SizedBox(width: 4),
                          Text(
                            strings.actionEvidenceButton,
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w800,
                              color: visual.goldSoft,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Color _statusColor(KefeVisualTheme visual, ActionFollowThroughStatus status) =>
      switch (status) {
        ActionFollowThroughStatus.proposed => visual.rules,
        ActionFollowThroughStatus.inProgress => visual.gold,
        ActionFollowThroughStatus.verifiedComplete => visual.success,
        ActionFollowThroughStatus.stalled => visual.empathy,
      };

  IconData _statusIcon(ActionFollowThroughStatus status) => switch (status) {
    ActionFollowThroughStatus.proposed => Icons.lightbulb_outline_rounded,
    ActionFollowThroughStatus.inProgress => Icons.trending_up_rounded,
    ActionFollowThroughStatus.verifiedComplete => Icons.check_circle_outline_rounded,
    ActionFollowThroughStatus.stalled => Icons.pause_circle_outline_rounded,
  };

  String _statusLabel(KefeStrings strings, ActionFollowThroughStatus status) =>
      switch (status) {
        ActionFollowThroughStatus.proposed => strings.actionStatusProposed,
        ActionFollowThroughStatus.inProgress => strings.actionStatusInProgress,
        ActionFollowThroughStatus.verifiedComplete =>
            strings.actionStatusVerifiedComplete,
        ActionFollowThroughStatus.stalled => strings.actionStatusStalled,
      };
}
