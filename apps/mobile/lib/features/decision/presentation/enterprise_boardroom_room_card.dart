import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/enterprise_boardroom_room_models.dart';

class EnterpriseBoardroomRoomCard extends StatelessWidget {
  const EnterpriseBoardroomRoomCard({
    required this.room,
    this.onTap,
    super.key,
  });

  final EnterpriseBoardroomModel room;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _scopeColor(visual, room.dilemmaScope);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('boardroom-room-${room.roomId}'),
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
                  child: Icon(Icons.business_center_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.entBoardEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _scopeLabel(strings, room.dilemmaScope),
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
                    strings.entBoardConsensusLabel((room.fiduciaryConsensusRatio * 100).toInt()),
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
              room.organizationName,
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
                strings.entBoardEsgLabel(
                  (room.esgAlignmentScore * 100).toInt(),
                  room.boardMemberCount,
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

  Color _scopeColor(KefeVisualSystem visual, BoardroomDilemmaScopeModel scope) => switch (scope) {
    BoardroomDilemmaScopeModel.esgAndSustainability => visual.empathy,
    BoardroomDilemmaScopeModel.capitalAllocationAndMa => visual.rules,
    BoardroomDilemmaScopeModel.executiveCompensation => visual.gold,
    BoardroomDilemmaScopeModel.crisisManagement => visual.burgundy,
  };

  String _scopeLabel(KefeStrings strings, BoardroomDilemmaScopeModel scope) => switch (scope) {
    BoardroomDilemmaScopeModel.esgAndSustainability => strings.entBoardScopeEsg,
    BoardroomDilemmaScopeModel.capitalAllocationAndMa => strings.entBoardScopeCapital,
    BoardroomDilemmaScopeModel.executiveCompensation => strings.entBoardScopeCompensation,
    BoardroomDilemmaScopeModel.crisisManagement => strings.entBoardScopeCrisis,
  };
}
