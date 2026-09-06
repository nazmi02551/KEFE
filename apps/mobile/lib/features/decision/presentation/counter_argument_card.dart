import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/counter_argument_models.dart';

class CounterArgumentCard extends StatelessWidget {
  const CounterArgumentCard({
    required this.link,
    this.onTap,
    super.key,
  });

  final ArgumentRefutationLinkModel link;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = visual.empathy;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('counter-arg-${link.refutationId}'),
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
                  child: Icon(Icons.compare_arrows_rounded, color: accent, size: 20),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.rebuttalEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _typeLabel(strings, link.refutationType),
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
                    strings.rebuttalStrengthLabel((link.refutationStrength * 100).toInt()),
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.w800,
                      color: accent,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: visual.border.withValues(alpha: 0.5)),
              ),
              child: Text(
                link.rebuttalThesis,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: visual.foreground,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _typeLabel(KefeStrings strings, RefutationTypeModel type) => switch (type) {
    RefutationTypeModel.directEmpiricalRebuttal => strings.rebuttalTypeEmpirical,
    RefutationTypeModel.logicalInvalidation => strings.rebuttalTypeLogical,
    RefutationTypeModel.valueHierarchyChallenge => strings.rebuttalTypeValue,
    RefutationTypeModel.boundaryQualification => strings.rebuttalTypeBoundary,
  };
}
