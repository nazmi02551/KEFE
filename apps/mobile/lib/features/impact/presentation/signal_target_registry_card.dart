import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/signal_target_models.dart';

class SignalTargetRegistryCard extends StatelessWidget {
  const SignalTargetRegistryCard({
    required this.report,
    this.onTap,
    super.key,
  });

  final SignalTargetRegistryReportModel report;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = visual.rules;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('signal-target-registry-${report.signalId}'),
        tone: KefeSurfaceTone.raised,
        padding: const EdgeInsets.all(18),
        borderRadius: 22,
        accent: accent,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header Row
            Row(
              children: [
                Container(
                  width: 38,
                  height: 38,
                  decoration: BoxDecoration(
                    color: accent.withValues(alpha: visual.isDark ? 0.18 : 0.10),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: accent.withValues(alpha: 0.3)),
                  ),
                  child: Icon(Icons.account_balance_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.sigTargetEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        strings.sigTargetTitle,
                        style: TextStyle(
                          fontSize: 14.5,
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

            // Summary Badges
            Wrap(
              spacing: 8,
              runSpacing: 6,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: visual.surfaceSunken,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                  ),
                  child: Text(
                    '${report.targets.length} Targets Registered',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: visual.foreground,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: accent.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: accent.withValues(alpha: 0.4)),
                  ),
                  child: Text(
                    strings.sigTargetPrimaryBadge,
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      color: accent,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Notice
            Text(
              strings.sigTargetNotice,
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w500,
                color: visual.mutedForeground,
                height: 1.35,
              ),
            ),
            const SizedBox(height: 12),

            // Targets List
            ...report.targets.map((target) {
              final isPrimary = target.targetId == report.primaryTargetId;
              final statusColor = _statusColor(visual, target.dispatchStatus);

              return Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: visual.surfaceSunken,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: isPrimary ? accent.withValues(alpha: 0.6) : visual.border.withValues(alpha: 0.4),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: (isPrimary ? accent : visual.mutedForeground).withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            isPrimary ? strings.sigTargetPrimaryBadge : strings.sigTargetSecondaryBadge,
                            style: TextStyle(
                              fontSize: 9.5,
                              fontWeight: FontWeight.w800,
                              color: isPrimary ? accent : visual.mutedForeground,
                            ),
                          ),
                        ),
                        const Spacer(),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: statusColor.withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            _statusLabel(strings, target.dispatchStatus),
                            style: TextStyle(
                              fontSize: 9.5,
                              fontWeight: FontWeight.w800,
                              color: statusColor,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(
                      target.targetName,
                      style: TextStyle(
                        fontSize: 12.5,
                        fontWeight: FontWeight.w700,
                        color: visual.foreground,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${target.targetType.toJsonValue()} · ${target.jurisdictionLevel}',
                      style: TextStyle(
                        fontSize: 10.5,
                        color: visual.mutedForeground,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Text(
                          strings.sigTargetChannelLabel(target.officialContactChannel),
                          style: TextStyle(
                            fontSize: 10,
                            color: visual.mutedForeground,
                          ),
                        ),
                        const Spacer(),
                        Text(
                          strings.sigTargetResponseDue(target.responseDueDays),
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                            color: visual.gold,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              );
            }),
            const SizedBox(height: 4),

            // Seal proof hash
            Text(
              strings.sigTargetProofVerified(
                report.registryProofHash.length > 16
                    ? '${report.registryProofHash.substring(0, 16)}...'
                    : report.registryProofHash,
              ),
              style: TextStyle(
                fontSize: 9.5,
                fontFamily: 'monospace',
                color: visual.mutedForeground.withValues(alpha: 0.6),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _statusColor(KefeVisualSystem visual, DispatchStatusModel status) {
    return switch (status) {
      DispatchStatusModel.proposedTarget => visual.mutedForeground,
      DispatchStatusModel.verifiedTarget => visual.rules,
      DispatchStatusModel.dispatched => visual.gold,
      DispatchStatusModel.acknowledged => visual.rules,
      DispatchStatusModel.actionPledged => visual.empathy,
      DispatchStatusModel.declinedJurisdiction => visual.burgundy,
    };
  }

  String _statusLabel(KefeStrings strings, DispatchStatusModel status) {
    return switch (status) {
      DispatchStatusModel.proposedTarget => strings.sigTargetStProposed,
      DispatchStatusModel.verifiedTarget => strings.sigTargetStVerified,
      DispatchStatusModel.dispatched => strings.sigTargetStDispatched,
      DispatchStatusModel.acknowledged => strings.sigTargetStAcknowledged,
      DispatchStatusModel.actionPledged => strings.sigTargetStPledged,
      DispatchStatusModel.declinedJurisdiction => strings.sigTargetStDeclined,
    };
  }
}
