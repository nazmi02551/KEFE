import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/argument_strength_models.dart';

class ArgumentStrengthCard extends StatelessWidget {
  const ArgumentStrengthCard({
    required this.strength,
    this.onTap,
    super.key,
  });

  final ArgumentStrengthModel strength;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _tierColor(visual, strength.strengthTier);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('arg-strength-${strength.argumentId}'),
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
                  child: Icon(Icons.fitness_center_rounded, color: accent, size: 20),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.argStrengthEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _tierLabel(strings, strength.strengthTier),
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
                    '%${(strength.compositeStrengthScore * 100).toInt()}',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      color: accent,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: visual.border.withValues(alpha: 0.5)),
              ),
              child: Column(
                children: [
                  _dim(
                    strings.argStrengthDimEmpirical((strength.empiricalFoundationScore * 100).toInt()),
                    strength.empiricalFoundationScore,
                    visual.rules,
                  ),
                  const SizedBox(height: 6),
                  _dim(
                    strings.argStrengthDimLogic((strength.logicalConsistencyScore * 100).toInt()),
                    strength.logicalConsistencyScore,
                    visual.gold,
                  ),
                  const SizedBox(height: 6),
                  _dim(
                    strings.argStrengthDimBalance((strength.representativeBalanceScore * 100).toInt()),
                    strength.representativeBalanceScore,
                    visual.empathy,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _dim(String label, double val, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(label, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600)),
        const SizedBox(height: 3),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: val,
            minHeight: 4,
            backgroundColor: color.withValues(alpha: 0.15),
            valueColor: AlwaysStoppedAnimation(color),
          ),
        ),
      ],
    );
  }

  Color _tierColor(KefeVisualTheme visual, ArgumentStrengthTierModel tier) =>
      switch (tier) {
        ArgumentStrengthTierModel.tierARobust => visual.rules,
        ArgumentStrengthTierModel.tierBPlausible => visual.gold,
        ArgumentStrengthTierModel.tierCWeakRhetorical => visual.attention,
      };

  String _tierLabel(KefeStrings strings, ArgumentStrengthTierModel tier) =>
      switch (tier) {
        ArgumentStrengthTierModel.tierARobust => strings.argStrengthTierRobust,
        ArgumentStrengthTierModel.tierBPlausible => strings.argStrengthTierPlausible,
        ArgumentStrengthTierModel.tierCWeakRhetorical => strings.argStrengthTierWeak,
      };
}
