import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/unintended_consequences_models.dart';

class UnintendedConsequencesCard extends StatelessWidget {
  const UnintendedConsequencesCard({
    required this.unintended,
    this.onTap,
    super.key,
  });

  final UnintendedConsequencesModel unintended;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _severityColor(visual, unintended.overallSystemicRisk);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('unintended-consequences-${unintended.optionCode}'),
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
                  child: Icon(Icons.waves_rounded, color: accent, size: 20),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.unintendedEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _severityLabel(strings, unintended.overallSystemicRisk),
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
            const SizedBox(height: 14),
            Column(
              children: unintended.consequences.map((item) {
                final itemColor = _severityColor(visual, item.severity);

                return Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: visual.surfaceSunken,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              _typeLabel(strings, item.consequenceType),
                              style: TextStyle(
                                fontSize: 11.5,
                                fontWeight: FontWeight.w800,
                                color: itemColor,
                              ),
                            ),
                            Text(
                              strings.unintendedMitigationLabel(
                                (item.mitigationFeasibility * 100).toInt(),
                              ),
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.w600,
                                color: visual.mutedForeground,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          item.description,
                          style: TextStyle(
                            fontSize: 11,
                            color: visual.foreground,
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Color _severityColor(KefeVisualTheme visual, ConsequenceSeverityModel sev) =>
      switch (sev) {
        ConsequenceSeverityModel.lowDrift => visual.rules,
        ConsequenceSeverityModel.moderateImpact => visual.gold,
        ConsequenceSeverityModel.severeParadox => visual.attention,
      };

  String _severityLabel(KefeStrings strings, ConsequenceSeverityModel sev) =>
      switch (sev) {
        ConsequenceSeverityModel.lowDrift => strings.unintendedRiskLow,
        ConsequenceSeverityModel.moderateImpact => strings.unintendedRiskModerate,
        ConsequenceSeverityModel.severeParadox => strings.unintendedRiskSevere,
      };

  String _typeLabel(KefeStrings strings, ConsequenceTypeModel type) =>
      switch (type) {
        ConsequenceTypeModel.perverseIncentive => strings.unintendedTypePerverse,
        ConsequenceTypeModel.marketDistortion => strings.unintendedTypeDistortion,
        ConsequenceTypeModel.behavioralRebound => strings.unintendedTypeRebound,
        ConsequenceTypeModel.systemicDisplacement =>
            strings.unintendedTypeDisplacement,
      };
}
