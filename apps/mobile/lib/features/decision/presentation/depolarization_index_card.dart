import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/depolarization_index_models.dart';

class DepolarizationIndexCard extends StatelessWidget {
  const DepolarizationIndexCard({
    required this.index,
    this.onTap,
    super.key,
  });

  final DepolarizationIndexModel index;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _stateColor(visual, index.bridgeEfficacyState);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('depolar-index-${index.caseVersionId}'),
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
                  child: Icon(Icons.compare_arrows_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.depolarEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _stateLabel(strings, index.bridgeEfficacyState),
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
                    strings.depolarScoreLabel((index.depolarizationScore * 100).toInt()),
                    style: TextStyle(
                      fontSize: 10.5,
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
                strings.depolarDistanceLabel(
                  (index.preDeliberationDistance * 100).toInt(),
                  (index.postDeliberationDistance * 100).toInt(),
                ),
                style: TextStyle(
                  fontSize: 11.5,
                  fontWeight: FontWeight.w700,
                  color: visual.foreground,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _stateColor(KefeVisualSystem visual, BridgeEfficacyStateModel state) => switch (state) {
    BridgeEfficacyStateModel.highDepolarization => visual.rules,
    BridgeEfficacyStateModel.moderateBridgeResonance => visual.gold,
    BridgeEfficacyStateModel.persistentPolarization => visual.burgundy,
  };

  String _stateLabel(KefeStrings strings, BridgeEfficacyStateModel state) => switch (state) {
    BridgeEfficacyStateModel.highDepolarization => strings.depolarStateHigh,
    BridgeEfficacyStateModel.moderateBridgeResonance => strings.depolarStateModerate,
    BridgeEfficacyStateModel.persistentPolarization => strings.depolarStatePersistent,
  };
}
