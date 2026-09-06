import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/fallacy_detector_models.dart';

class FallacyDetectorCard extends StatelessWidget {
  const FallacyDetectorCard({
    required this.result,
    this.onTap,
    super.key,
  });

  final FallacyDetectionResultModel result;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = result.hasFallacy ? visual.attention : visual.rules;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('fallacy-detector-${result.argumentId}'),
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
                  child: Icon(
                    result.hasFallacy
                        ? Icons.warning_amber_rounded
                        : Icons.check_circle_outline_rounded,
                    color: accent,
                    size: 20,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.fallacyEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        result.hasFallacy
                            ? strings.fallacyDetectedHeading
                            : strings.fallacyCleanHeading,
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
                    'Doğruluk: %${(result.overallIntegrityScore * 100).toInt()}',
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
            Column(
              children: result.detectedFallacies.map((item) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: visual.surfaceSunken,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              _fallacyLabel(strings, item.fallacyType),
                              style: TextStyle(
                                fontSize: 11.5,
                                fontWeight: FontWeight.w800,
                                color: accent,
                              ),
                            ),
                            Text(
                              '%${(item.confidence * 100).toInt()}',
                              style: TextStyle(
                                fontSize: 10.5,
                                fontWeight: FontWeight.w600,
                                color: visual.mutedForeground,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          item.explanation,
                          style: TextStyle(
                            fontSize: 11,
                            color: visual.foreground,
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  String _fallacyLabel(KefeStrings strings, FallacyTypeModel type) => switch (type) {
    FallacyTypeModel.adHominem => strings.fallacyTypeAdHominem,
    FallacyTypeModel.strawMan => strings.fallacyTypeStrawMan,
    FallacyTypeModel.falseDilemma => strings.fallacyTypeFalseDilemma,
    FallacyTypeModel.slipperySlope => strings.fallacyTypeSlipperySlope,
    FallacyTypeModel.appealToEmotionFear => strings.fallacyTypeFear,
    FallacyTypeModel.noFallacyDetected => strings.fallacyTypeNone,
  };
}
