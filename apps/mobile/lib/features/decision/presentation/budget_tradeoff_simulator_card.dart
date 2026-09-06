import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/budget_tradeoff_simulator_models.dart';

class BudgetTradeoffSimulatorCard extends StatelessWidget {
  const BudgetTradeoffSimulatorCard({
    required this.tradeoff,
    this.onTap,
    super.key,
  });

  final BudgetTradeoffModel tradeoff;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _profileColor(visual, tradeoff.tradeoffProfile);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('budget-tradeoff-${tradeoff.tradeoffId}'),
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
                  child: Icon(Icons.pie_chart_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.budgetSimEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _profileLabel(strings, tradeoff.tradeoffProfile),
                        style: TextStyle(
                          fontSize: 12.5,
                          fontWeight: FontWeight.w800,
                          color: visual.foreground,
                        ),
                      ),
                    ],
                  ),
                ),
                if (tradeoff.unallocatedPct > 0)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
                    decoration: BoxDecoration(
                      color: visual.surfaceSunken,
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                    ),
                    child: Text(
                      strings.budgetSimUnallocatedLabel(tradeoff.unallocatedPct),
                      style: TextStyle(
                        fontSize: 9.5,
                        fontWeight: FontWeight.w800,
                        color: visual.gold,
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
                strings.budgetSimBreakdownLabel(
                  tradeoff.healthcarePct,
                  tradeoff.educationPct,
                  tradeoff.infrastructurePct,
                  tradeoff.greenTransitionPct,
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

  Color _profileColor(KefeVisualSystem visual, TradeoffProfileModel profile) => switch (profile) {
    TradeoffProfileModel.healthEducationPriority => visual.rules,
    TradeoffProfileModel.infrastructureGrowth => visual.gold,
    TradeoffProfileModel.ecologicalTransition => visual.empathy,
    TradeoffProfileModel.balancedAllocation => visual.gold,
  };

  String _profileLabel(KefeStrings strings, TradeoffProfileModel profile) => switch (profile) {
    TradeoffProfileModel.healthEducationPriority => strings.budgetSimProfileHuman,
    TradeoffProfileModel.infrastructureGrowth => strings.budgetSimProfileInfra,
    TradeoffProfileModel.ecologicalTransition => strings.budgetSimProfileEco,
    TradeoffProfileModel.balancedAllocation => strings.budgetSimProfileBalanced,
  };
}
