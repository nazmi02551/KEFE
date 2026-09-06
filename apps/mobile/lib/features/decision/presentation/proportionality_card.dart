import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/proportionality_models.dart';

class ProportionalityCard extends StatelessWidget {
  const ProportionalityCard({
    required this.test,
    this.onTap,
    super.key,
  });

  final ProportionalityTestModel test;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _outcomeColor(visual, test.outcome);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('proportionality-${test.optionCode}'),
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
                  child: Icon(Icons.balance_rounded, color: accent, size: 20),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.proportionalEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _outcomeLabel(strings, test.outcome),
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
                    '%${(test.compositeProportionalityScore * 100).toInt()}',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      color: accent,
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
              child: Column(
                children: [
                  _ProngRow(
                    label: strings.proportionalProngSuitability((test.suitabilityScore * 100).toInt()),
                    color: visual.rules,
                  ),
                  const SizedBox(height: 4),
                  _ProngRow(
                    label: strings.proportionalProngNecessity((test.necessityLeastIntrusiveScore * 100).toInt()),
                    color: visual.gold,
                  ),
                  const SizedBox(height: 4),
                  _ProngRow(
                    label: strings.proportionalProngStrict((test.strictProportionalityScore * 100).toInt()),
                    color: accent,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 10),
            Text(
              test.summary,
              style: TextStyle(
                fontSize: 12,
                color: visual.foreground,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _outcomeColor(KefeVisualTheme visual, ProportionalityOutcomeModel outcome) =>
      switch (outcome) {
        ProportionalityOutcomeModel.proportionalValid => visual.rules,
        ProportionalityOutcomeModel.excessivelyBurdensome => visual.gold,
        ProportionalityOutcomeModel.disproportionateInvalid => visual.attention,
      };

  String _outcomeLabel(KefeStrings strings, ProportionalityOutcomeModel outcome) =>
      switch (outcome) {
        ProportionalityOutcomeModel.proportionalValid =>
            strings.proportionalOutcomeValid,
        ProportionalityOutcomeModel.excessivelyBurdensome =>
            strings.proportionalOutcomeBurdensome,
        ProportionalityOutcomeModel.disproportionateInvalid =>
            strings.proportionalOutcomeInvalid,
      };
}

class _ProngRow extends StatelessWidget {
  const _ProngRow({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 6,
          height: 6,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 6),
        Expanded(
          child: Text(
            label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: color,
            ),
          ),
        ),
      ],
    );
  }
}
