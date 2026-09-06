import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/public_procurement_oversight_models.dart';

class PublicProcurementOversightCard extends StatelessWidget {
  const PublicProcurementOversightCard({
    required this.procurement,
    this.onTap,
    super.key,
  });

  final ProcurementOversightModel procurement;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _integrityColor(visual, procurement.integrityLevel);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('procure-hive-${procurement.tenderId}'),
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
                  child: Icon(Icons.account_balance_wallet_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.procureEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _integrityLabel(strings, procurement.integrityLevel),
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
                    strings.procureAuditorsLabel(procurement.activeCivicAuditorsCount),
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
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: visual.border.withValues(alpha: 0.5)),
              ),
              child: Text(
                procurement.contractingAuthority,
                style: TextStyle(
                  fontSize: 11.5,
                  color: visual.foreground,
                ),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              strings.procureAmountLabel(procurement.awardedAmountTry.toStringAsFixed(0)),
              style: TextStyle(
                fontSize: 10.5,
                fontWeight: FontWeight.w700,
                color: visual.gold,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _integrityColor(KefeVisualSystem visual, ProcurementIntegrityLevelModel level) => switch (level) {
    ProcurementIntegrityLevelModel.openCompetitiveVerified => const Color(0xFF10B981),
    ProcurementIntegrityLevelModel.anomalousSoleSourceReview => visual.gold,
    ProcurementIntegrityLevelModel.criticalOverrunAlert => visual.empathy,
  };

  String _integrityLabel(KefeStrings strings, ProcurementIntegrityLevelModel level) => switch (level) {
    ProcurementIntegrityLevelModel.openCompetitiveVerified => strings.procureLvlOpen,
    ProcurementIntegrityLevelModel.anomalousSoleSourceReview => strings.procureLvlSole,
    ProcurementIntegrityLevelModel.criticalOverrunAlert => strings.procureLvlOverrun,
  };
}
