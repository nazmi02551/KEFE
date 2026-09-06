import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/divergence_anatomy_models.dart';

class DivergenceAnatomyCard extends StatelessWidget {
  const DivergenceAnatomyCard({
    required this.anatomy,
    super.key,
  });

  final DivergenceAnatomyModel anatomy;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = visual.rules;

    return KefeSurface(
      key: ValueKey('divergence-anatomy-${anatomy.caseVersionId}'),
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
                child: Icon(Icons.analytics_outlined, color: accent, size: 18),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    KefeEyebrow(strings.anatomyEyebrow, color: accent),
                    const SizedBox(height: 2),
                    Text(
                      _driverLabel(strings, anatomy.primaryDriver),
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
          ...anatomy.drivers.map((driver) {
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          _driverLabel(strings, driver.driverType),
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                            color: visual.foreground,
                          ),
                        ),
                      ),
                      Text(
                        '%${driver.sharePercentage.toStringAsFixed(1)}',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w800,
                          color: visual.goldSoft,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 5),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(3),
                    child: SizedBox(
                      height: 5,
                      child: LinearProgressIndicator(
                        value: (driver.sharePercentage / 100).clamp(0.0, 1.0),
                        backgroundColor: visual.surfaceSunken,
                        valueColor: AlwaysStoppedAnimation<Color>(visual.rules),
                      ),
                    ),
                  ),
                  if (driver.explanation.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Text(
                      driver.explanation,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: visual.mutedForeground,
                        fontSize: 11,
                      ),
                    ),
                  ],
                ],
              ),
            );
          }),
        ],
      ),
    );
  }

  String _driverLabel(KefeStrings strings, DivergenceDriverTypeModel type) =>
      switch (type) {
        DivergenceDriverTypeModel.normativeValueWeight =>
            strings.anatomyDriverNormative,
        DivergenceDriverTypeModel.factualProbabilityAssessment =>
            strings.anatomyDriverFactual,
        DivergenceDriverTypeModel.proceduralGovernance =>
            strings.anatomyDriverProcedural,
        DivergenceDriverTypeModel.timeHorizon => strings.anatomyDriverTimeHorizon,
      };
}
