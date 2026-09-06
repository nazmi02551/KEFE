import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/digital_sovereignty_vault_models.dart';

class DigitalSovereigntyVaultCard extends StatelessWidget {
  const DigitalSovereigntyVaultCard({
    required this.vault,
    this.onTap,
    super.key,
  });

  final DigitalSovereigntyModel vault;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _tierColor(visual, vault.sovereigntyTier);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('sovereignty-vault-${vault.vaultId}'),
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
                  child: Icon(Icons.shield_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.sovereigntyEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _tierLabel(strings, vault.sovereigntyTier),
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
                    strings.sovereigntyResidencyLabel((vault.localResidencyPct * 100).toInt()),
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
                'Egemenlik Bölgesi: ${vault.jurisdictionRegion}',
                style: TextStyle(
                  fontSize: 11.5,
                  color: visual.foreground,
                ),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              strings.sovereigntyThreatLabel((vault.exfiltrationThreatScore * 100).toInt()),
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

  Color _tierColor(KefeVisualSystem visual, DigitalSovereigntyTierModel tier) => switch (tier) {
    DigitalSovereigntyTierModel.sovereignResidencyEnforced => const Color(0xFF10B981),
    DigitalSovereigntyTierModel.controlledEphemeralCompute => visual.gold,
    DigitalSovereigntyTierModel.dataExfiltrationBreachAlert => visual.empathy,
  };

  String _tierLabel(KefeStrings strings, DigitalSovereigntyTierModel tier) => switch (tier) {
    DigitalSovereigntyTierModel.sovereignResidencyEnforced => strings.sovereigntyStEnforced,
    DigitalSovereigntyTierModel.controlledEphemeralCompute => strings.sovereigntyStEphemeral,
    DigitalSovereigntyTierModel.dataExfiltrationBreachAlert => strings.sovereigntyStBreach,
  };
}
