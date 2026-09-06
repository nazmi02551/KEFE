import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/moderator_audit_log_models.dart';

class ModeratorAuditLogCard extends StatelessWidget {
  const ModeratorAuditLogCard({
    required this.audit,
    this.onTap,
    super.key,
  });

  final ModeratorAuditLogModel audit;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _actionColor(visual, audit.actionType);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('mod-audit-${audit.auditId}'),
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
                  child: Icon(Icons.admin_panel_settings_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.modAuditEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _actionLabel(strings, audit.actionType),
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
                    '${strings.modAuditModeratorLabel} ${audit.moderatorId}',
                    style: TextStyle(
                      fontSize: 9.5,
                      fontWeight: FontWeight.w800,
                      color: visual.gold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              '${strings.modAuditRuleLabel} ${audit.policyRuleReference}',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w700,
                color: visual.rules,
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
                audit.justificationText,
                style: TextStyle(
                  fontSize: 11.5,
                  color: visual.foreground,
                ),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Hash: ${audit.actionHash.substring(0, 16)}...',
              style: TextStyle(
                fontSize: 10,
                fontFamily: 'monospace',
                color: visual.mutedForeground,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _actionColor(KefeVisualSystem visual, ModerationActionTypeModel action) => switch (action) {
    ModerationActionTypeModel.reasonRemovedPolicyBreach => visual.burgundy,
    ModerationActionTypeModel.flagDismissedValid => visual.rules,
    ModerationActionTypeModel.caseVersionFreeze => visual.gold,
    ModerationActionTypeModel.userWarningIssued => visual.empathy,
  };

  String _actionLabel(KefeStrings strings, ModerationActionTypeModel action) => switch (action) {
    ModerationActionTypeModel.reasonRemovedPolicyBreach => strings.modAuditActionRemove,
    ModerationActionTypeModel.flagDismissedValid => strings.modAuditActionDismiss,
    ModerationActionTypeModel.caseVersionFreeze => strings.modAuditActionFreeze,
    ModerationActionTypeModel.userWarningIssued => strings.modAuditActionWarning,
  };
}
