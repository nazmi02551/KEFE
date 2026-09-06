import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/incentive_map_models.dart';

class IncentiveMapCard extends StatelessWidget {
  const IncentiveMapCard({
    required this.incentiveMap,
    this.onTap,
    super.key,
  });

  final IncentiveMapModel incentiveMap;
  final VoidCallback? onTap;

  Color _riskColor(KefeVisualSystem visual, String risk) => switch (risk) {
    'CRITICAL' || 'HIGH' => visual.attention,
    'MODERATE' => visual.gold,
    _ => visual.success,
  };

  Color _statusColor(KefeVisualSystem visual, String status) => switch (status) {
    'ALIGNED' => visual.success,
    'MISALIGNED' => visual.gold,
    'PERVERSE' => visual.attention,
    _ => visual.mutedForeground,
  };

  String _statusLabel(KefeStrings strings, String status) => switch (status) {
    'ALIGNED' => strings.incentiveMapStatusAligned,
    'MISALIGNED' => strings.incentiveMapStatusMisaligned,
    'PERVERSE' => strings.incentiveMapStatusPerverse,
    _ => status,
  };

  String _typeLabel(KefeStrings strings, String type) => switch (type) {
    'FINANCIAL_PROFIT' => strings.incentiveMapTypeProfit,
    'POLITICAL_ELECTORAL' => strings.incentiveMapTypeElectoral,
    'BUREAUCRATIC_RISK_AVERSION' => strings.incentiveMapTypeBureaucratic,
    'CIVIC_PUBLIC_WELFARE' => strings.incentiveMapTypeCivic,
    _ => type,
  };

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _riskColor(visual, incentiveMap.perverseIncentiveRisk);
    final alignmentPct = (incentiveMap.alignmentIndex * 100).toInt();

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('inc-map-${incentiveMap.mapId}'),
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
                  child: Icon(Icons.hub_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.incentiveMapEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        strings.incentiveMapAlignmentLabel(alignmentPct),
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w800,
                          color: visual.foreground,
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: visual.surfaceSunken,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                  ),
                  child: Text(
                    strings.incentiveMapRiskLabel(incentiveMap.perverseIncentiveRisk),
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.w700,
                      color: accent,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: incentiveMap.alignmentIndex.clamp(0.0, 1.0),
                backgroundColor: visual.surfaceSunken,
                valueColor: AlwaysStoppedAnimation<Color>(accent),
                minHeight: 6,
              ),
            ),
            if (incentiveMap.primaryDriver.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(
                strings.incentiveMapDriverLabel(incentiveMap.primaryDriver),
                style: TextStyle(
                  fontSize: 11.5,
                  fontWeight: FontWeight.w600,
                  color: visual.mutedForeground,
                ),
              ),
            ],
            const SizedBox(height: 12),
            ...incentiveMap.incentiveNodes.map((node) {
              final statusColor = _statusColor(visual, node.alignmentStatus);
              final intensityPct = (node.intensityScore * 100).toInt();

              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            node.stakeholderGroup,
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                              color: visual.foreground,
                            ),
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: statusColor.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(4),
                            border: Border.all(color: statusColor.withValues(alpha: 0.3)),
                          ),
                          child: Text(
                            _statusLabel(strings, node.alignmentStatus),
                            style: TextStyle(
                              fontSize: 9.5,
                              fontWeight: FontWeight.w700,
                              color: statusColor,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          '%$intensityPct',
                          style: TextStyle(
                            fontSize: 11.5,
                            fontWeight: FontWeight.w800,
                            color: visual.foreground,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${_typeLabel(strings, node.incentiveType)}: ${node.coreIncentive}',
                      style: TextStyle(
                        fontSize: 10.5,
                        color: visual.foreground.withValues(alpha: 0.85),
                      ),
                    ),
                    if (node.unintendedBehavior.isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.only(top: 2),
                        child: Text(
                          node.unintendedBehavior,
                          style: TextStyle(
                            fontSize: 10,
                            fontStyle: FontStyle.italic,
                            color: visual.mutedForeground,
                          ),
                        ),
                      ),
                  ],
                ),
              );
            }),
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: visual.border.withValues(alpha: 0.4)),
              ),
              child: Row(
                children: [
                  Icon(Icons.shield_outlined, size: 14, color: visual.mutedForeground),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      strings.incentiveMapMitigationLabel(incentiveMap.mitigationMechanism),
                      style: TextStyle(
                        fontSize: 10.5,
                        fontWeight: FontWeight.w600,
                        color: visual.mutedForeground,
                      ),
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
}
