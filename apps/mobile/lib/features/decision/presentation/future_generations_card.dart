import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/future_generations_models.dart';

class FutureGenerationsCard extends StatelessWidget {
  const FutureGenerationsCard({
    required this.projection,
    this.onTap,
    super.key,
  });

  final FutureGenerationsModel projection;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = projection.netIntergenerationalScore >= 0.0
        ? visual.rules
        : visual.attention;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('future-gen-${projection.optionCode}'),
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
                  child: Icon(Icons.nest_cam_wired_stand_rounded, color: accent, size: 20),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.futureGenEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        '${strings.futureGenNetScoreLabel} ${projection.netIntergenerationalScore >= 0 ? "+" : ""}${projection.netIntergenerationalScore}',
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
              children: projection.projections.map((p) {
                final isPos = p.impactScore >= 0.0;
                final pColor = isPos ? visual.rules : visual.attention;

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
                              _horizonLabel(strings, p.horizon),
                              style: TextStyle(
                                fontSize: 11.5,
                                fontWeight: FontWeight.w800,
                                color: pColor,
                              ),
                            ),
                            Text(
                              '${isPos ? "+" : ""}${(p.impactScore * 100).toInt()}%',
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w700,
                                color: pColor,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          p.summary,
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

  String _horizonLabel(KefeStrings strings, TimeHorizonModel h) => switch (h) {
    TimeHorizonModel.horizon5Years => strings.futureGenH5Yr,
    TimeHorizonModel.horizon20Years => strings.futureGenH20Yr,
    TimeHorizonModel.horizon50Years => strings.futureGenH50Yr,
    TimeHorizonModel.horizon100Years => strings.futureGenH100Yr,
  };
}
