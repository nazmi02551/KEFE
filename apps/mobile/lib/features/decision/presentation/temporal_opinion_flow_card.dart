import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/temporal_opinion_flow_models.dart';

class TemporalOpinionFlowCard extends StatelessWidget {
  const TemporalOpinionFlowCard({
    required this.flow,
    this.onTap,
    super.key,
  });

  final TemporalOpinionFlowModel flow;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _epochColor(visual, flow.epochType);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('opinion-flow-${flow.flowId}'),
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
                  child: Icon(Icons.timeline_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.tempFlowEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _epochLabel(strings, flow.epochType),
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
                    strings.tempFlowRateLabel((flow.migrationRate * 100).toInt()),
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                      color: accent,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: visual.border.withValues(alpha: 0.5)),
              ),
              child: Text(
                strings.tempFlowSharesLabel(
                  (flow.optionAShare * 100).toInt(),
                  (flow.optionBShare * 100).toInt(),
                  (flow.undecidedBridgeShare * 100).toInt(),
                ),
                style: TextStyle(
                  fontSize: 11.5,
                  fontWeight: FontWeight.w700,
                  color: visual.gold,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _epochColor(KefeVisualSystem visual, MigrationEpochTypeModel epoch) => switch (epoch) {
    MigrationEpochTypeModel.initialBlindResonance => visual.rules,
    MigrationEpochTypeModel.midDeliberationShift => visual.gold,
    MigrationEpochTypeModel.maturedConsensusState => visual.empathy,
  };

  String _epochLabel(KefeStrings strings, MigrationEpochTypeModel epoch) => switch (epoch) {
    MigrationEpochTypeModel.initialBlindResonance => strings.tempFlowEpochInitial,
    MigrationEpochTypeModel.midDeliberationShift => strings.tempFlowEpochMid,
    MigrationEpochTypeModel.maturedConsensusState => strings.tempFlowEpochMatured,
  };
}
