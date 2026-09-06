import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/municipal_participatory_budgeting_models.dart';

class MunicipalParticipatoryBudgetingCard extends StatelessWidget {
  const MunicipalParticipatoryBudgetingCard({
    required this.project,
    this.onTap,
    super.key,
  });

  final MunicipalBudgetProjectModel project;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _domainColor(visual, project.projectDomain);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('mun-project-${project.projectId}'),
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
                  child: Icon(Icons.location_city_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.munBudEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _domainLabel(strings, project.projectDomain),
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
                    strings.munBudApprovalLabel((project.civicApprovalRate * 100).toInt()),
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                      color: accent,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              project.municipalityName,
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
                strings.munBudBudgetLabel(project.requestedBudgetTry, project.citizenVotesCount),
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

  Color _domainColor(KefeVisualSystem visual, MunicipalProjectDomainModel domain) => switch (domain) {
    MunicipalProjectDomainModel.parksAndGreenSpaces => const Color(0xFF10B981),
    MunicipalProjectDomainModel.publicTransitAndMobility => visual.rules,
    MunicipalProjectDomainModel.educationAndYouthCenters => visual.gold,
    MunicipalProjectDomainModel.disasterResilienceAndSafety => visual.empathy,
  };

  String _domainLabel(KefeStrings strings, MunicipalProjectDomainModel domain) => switch (domain) {
    MunicipalProjectDomainModel.parksAndGreenSpaces => strings.munBudDomParks,
    MunicipalProjectDomainModel.publicTransitAndMobility => strings.munBudDomTransit,
    MunicipalProjectDomainModel.educationAndYouthCenters => strings.munBudDomEducation,
    MunicipalProjectDomainModel.disasterResilienceAndSafety => strings.munBudDomDisaster,
  };
}
