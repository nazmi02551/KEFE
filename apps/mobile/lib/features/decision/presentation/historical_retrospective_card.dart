import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/historical_retrospective_models.dart';

class HistoricalRetrospectiveCard extends StatelessWidget {
  const HistoricalRetrospectiveCard({
    required this.retrospective,
    this.onTap,
    super.key,
  });

  final HistoricalRetrospectiveModel retrospective;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = visual.gold;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('historical-retro-${retrospective.retrospectiveId}'),
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
                  child: Icon(Icons.history_edu_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.retroSimEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        retrospective.historicalEventName,
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
                    '${retrospective.historicalYear}',
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.w900,
                      color: accent,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              _eraLabel(strings, retrospective.historicalEra),
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
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    strings.retroSimDecisionLabel,
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.w800,
                      color: visual.gold,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    retrospective.actualHistoricalDecision,
                    style: TextStyle(
                      fontSize: 11.5,
                      fontWeight: FontWeight.w600,
                      color: visual.foreground,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    strings.retroSimConsequenceLabel,
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.w800,
                      color: visual.empathy,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    retrospective.historicalConsequenceSummary,
                    style: TextStyle(
                      fontSize: 11,
                      color: visual.foreground,
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

  String _eraLabel(KefeStrings strings, HistoricalEraModel era) => switch (era) {
    HistoricalEraModel.ancientClassical => strings.retroSimEraAncient,
    HistoricalEraModel.industrialEra => strings.retroSimEraIndustrial,
    HistoricalEraModel.twentiethCentury => strings.retroSimEraCentury20,
    HistoricalEraModel.contemporaryCrisis => strings.retroSimEraContemporary,
  };
}
