import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/rights_conflict_models.dart';

class RightsConflictCard extends StatelessWidget {
  const RightsConflictCard({
    required this.conflict,
    this.onTap,
    super.key,
  });

  final RightsConflictModel conflict;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _severityColor(visual, conflict.severity);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('rights-conflict-${conflict.optionCode}'),
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
                  child: Icon(Icons.gavel_rounded, color: accent, size: 20),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.rightsEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _collisionLabel(strings, conflict.collisionType),
                        style: TextStyle(
                          fontSize: 12.5,
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
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: visual.border.withValues(alpha: 0.5)),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    _severityLabel(strings, conflict.severity),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: accent,
                    ),
                  ),
                  Text(
                    strings.rightsCoreScoreLabel(
                      (conflict.inalienableCoreScore * 100).toInt(),
                    ),
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.w600,
                      color: visual.mutedForeground,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 10),
            Text(
              conflict.constitutionalRationale,
              style: TextStyle(
                fontSize: 12,
                color: visual.foreground,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _severityColor(KefeVisualTheme visual, RestrictionSeverityModel sev) =>
      switch (sev) {
        RestrictionSeverityModel.permissibleRestriction => visual.rules,
        RestrictionSeverityModel.coreRightErosion => visual.gold,
        RestrictionSeverityModel.unconstitutionalBreach => visual.attention,
      };

  String _severityLabel(KefeStrings strings, RestrictionSeverityModel sev) =>
      switch (sev) {
        RestrictionSeverityModel.permissibleRestriction =>
            strings.rightsSevPermissible,
        RestrictionSeverityModel.coreRightErosion => strings.rightsSevErosion,
        RestrictionSeverityModel.unconstitutionalBreach =>
            strings.rightsSevBreach,
      };

  String _collisionLabel(KefeStrings strings, RightsCollisionTypeModel type) =>
      switch (type) {
        RightsCollisionTypeModel.privacyVsSecurity =>
            strings.rightsTypePrivacySec,
        RightsCollisionTypeModel.expressionVsDignity =>
            strings.rightsTypeExprDignity,
        RightsCollisionTypeModel.propertyVsEnvironment =>
            strings.rightsTypePropEnv,
        RightsCollisionTypeModel.individualLibertyVsPublicHealth =>
            strings.rightsTypeLibertyHealth,
      };
}
