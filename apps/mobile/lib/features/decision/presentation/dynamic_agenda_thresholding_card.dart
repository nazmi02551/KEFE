import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/dynamic_agenda_thresholding_models.dart';

class DynamicAgendaThresholdingCard extends StatelessWidget {
  const DynamicAgendaThresholdingCard({
    required this.agenda,
    this.onTap,
    super.key,
  });

  final DynamicAgendaModel agenda;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _tierColor(visual, agenda.priorityTier);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('agenda-topic-${agenda.topicId}'),
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
                  child: Icon(Icons.trending_up_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.agendaThrEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _tierLabel(strings, agenda.priorityTier),
                        style: TextStyle(
                          fontSize: 12.5,
                          fontWeight: FontWeight.w800,
                          color: visual.foreground,
                        ),
                      ),
                    ],
                  ),
                ),
                if (agenda.isFeaturedOnNationalBallot)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
                    decoration: BoxDecoration(
                      color: visual.surfaceSunken,
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                    ),
                    child: Text(
                      strings.agendaThrFeaturedLabel,
                      style: TextStyle(
                        fontSize: 9,
                        fontWeight: FontWeight.w800,
                        color: visual.gold,
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              agenda.topicTitle,
              style: TextStyle(
                fontSize: 12.5,
                fontWeight: FontWeight.w800,
                color: visual.foreground,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: visual.border.withValues(alpha: 0.5)),
              ),
              child: Text(
                strings.agendaThrMetricsLabel(
                  (agenda.resonanceVelocityIndex * 100).toInt(),
                  (agenda.viewpointDiversityEntropy * 100).toInt(),
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

  Color _tierColor(KefeVisualSystem visual, AgendaPriorityTierModel tier) => switch (tier) {
    AgendaPriorityTierModel.nationalUrgencySpike => visual.empathy,
    AgendaPriorityTierModel.regionalEmergentTopic => visual.gold,
    AgendaPriorityTierModel.monitoredIncubation => visual.rules,
  };

  String _tierLabel(KefeStrings strings, AgendaPriorityTierModel tier) => switch (tier) {
    AgendaPriorityTierModel.nationalUrgencySpike => strings.agendaThrTierNational,
    AgendaPriorityTierModel.regionalEmergentTopic => strings.agendaThrTierRegional,
    AgendaPriorityTierModel.monitoredIncubation => strings.agendaThrTierIncubation,
  };
}
