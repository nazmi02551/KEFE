import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/youth_deliberation_space_models.dart';

class YouthDeliberationSpaceCard extends StatelessWidget {
  const YouthDeliberationSpaceCard({
    required this.space,
    this.onTap,
    super.key,
  });

  final YouthDeliberationSpaceModel space;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _focusColor(visual, space.focusArea);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('youth-space-${space.spaceId}'),
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
                  child: Icon(Icons.groups_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.youthSpaceEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _focusLabel(strings, space.focusArea),
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
                    strings.youthSpaceActionsLabel(space.consensusActionCount),
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
              space.spaceName,
              style: TextStyle(
                fontSize: 12.5,
                fontWeight: FontWeight.w800,
                color: visual.foreground,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              space.institutionOrCommunity,
              style: TextStyle(
                fontSize: 11,
                color: visual.mutedForeground,
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
                strings.youthSpaceStudentsLabel(space.activeStudentCount),
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

  Color _focusColor(KefeVisualSystem visual, YouthSpaceFocusAreaModel focus) => switch (focus) {
    YouthSpaceFocusAreaModel.campusAndEducationPolicy => visual.rules,
    YouthSpaceFocusAreaModel.climateAndIntergenerational => visual.empathy,
    YouthSpaceFocusAreaModel.digitalRightsAndAi => visual.gold,
    YouthSpaceFocusAreaModel.civicEntrepreneurship => visual.burgundy,
  };

  String _focusLabel(KefeStrings strings, YouthSpaceFocusAreaModel focus) => switch (focus) {
    YouthSpaceFocusAreaModel.campusAndEducationPolicy => strings.youthSpaceFocusCampus,
    YouthSpaceFocusAreaModel.climateAndIntergenerational => strings.youthSpaceFocusClimate,
    YouthSpaceFocusAreaModel.digitalRightsAndAi => strings.youthSpaceFocusDigital,
    YouthSpaceFocusAreaModel.civicEntrepreneurship => strings.youthSpaceFocusCivic,
  };
}
