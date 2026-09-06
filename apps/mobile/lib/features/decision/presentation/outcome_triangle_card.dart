import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/outcome_triangle_models.dart';

class OutcomeTriangleCard extends StatelessWidget {
  const OutcomeTriangleCard({
    required this.triangle,
    super.key,
  });

  final OutcomeTriangleModel triangle;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _archetypeColor(visual, triangle.dominantArchetype);

    return KefeSurface(
      key: ValueKey('outcome-triangle-${triangle.caseVersionId}-${triangle.optionCode}'),
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
                  color: accent.withValues(alpha: visual.isDark ? 0.16 : 0.08),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: accent.withValues(alpha: 0.25)),
                ),
                child: Icon(Icons.change_history_rounded, color: accent, size: 20),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    KefeEyebrow(strings.triangleEyebrow, color: accent),
                    const SizedBox(height: 2),
                    Text(
                      _archetypeLabel(strings, triangle.dominantArchetype),
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w800,
                        letterSpacing: -0.2,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          // 3 Axial Bars
          _buildAxisRow(
            context,
            label: strings.triangleAxisRules((triangle.rulesWeight * 100).round()),
            weight: triangle.rulesWeight,
            color: visual.rules,
            visual: visual,
          ),
          const SizedBox(height: 10),
          _buildAxisRow(
            context,
            label: strings.triangleAxisEmpathy((triangle.empathyWeight * 100).round()),
            weight: triangle.empathyWeight,
            color: visual.empathy,
            visual: visual,
          ),
          const SizedBox(height: 10),
          _buildAxisRow(
            context,
            label: strings.triangleAxisUtility((triangle.utilityWeight * 100).round()),
            weight: triangle.utilityWeight,
            color: visual.goldSoft,
            visual: visual,
          ),
        ],
      ),
    );
  }

  Widget _buildAxisRow(
    BuildContext context, {
    required String label,
    required double weight,
    required Color color,
    required KefeVisualTheme visual,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w700,
                color: visual.foreground,
              ),
            ),
            Text(
              '%${(weight * 100).toStringAsFixed(0)}',
              style: TextStyle(
                fontSize: 11.5,
                fontWeight: FontWeight.w800,
                color: color,
              ),
            ),
          ],
        ),
        const SizedBox(height: 4),
        ClipRRect(
          borderRadius: BorderRadius.circular(3),
          child: SizedBox(
            height: 5,
            child: LinearProgressIndicator(
              value: weight.clamp(0.0, 1.0),
              backgroundColor: visual.surfaceSunken,
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
        ),
      ],
    );
  }

  Color _archetypeColor(
    KefeVisualTheme visual,
    TriangleArchetypeModel archetype,
  ) =>
      switch (archetype) {
        TriangleArchetypeModel.rightsCentric => visual.rules,
        TriangleArchetypeModel.empathyCentric => visual.empathy,
        TriangleArchetypeModel.utilityCentric => visual.goldSoft,
        TriangleArchetypeModel.triBalancedHarmony => visual.gold,
      };

  String _archetypeLabel(
    KefeStrings strings,
    TriangleArchetypeModel archetype,
  ) =>
      switch (archetype) {
        TriangleArchetypeModel.rightsCentric => strings.triangleArchetypeRights,
        TriangleArchetypeModel.empathyCentric => strings.triangleArchetypeEmpathy,
        TriangleArchetypeModel.utilityCentric => strings.triangleArchetypeUtility,
        TriangleArchetypeModel.triBalancedHarmony =>
            strings.triangleArchetypeHarmony,
      };
}
