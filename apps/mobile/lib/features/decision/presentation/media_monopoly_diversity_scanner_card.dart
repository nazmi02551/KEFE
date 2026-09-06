import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/media_monopoly_diversity_scanner_models.dart';

class MediaMonopolyDiversityScannerCard extends StatelessWidget {
  const MediaMonopolyDiversityScannerCard({
    required this.scan,
    this.onTap,
    super.key,
  });

  final MediaDiversityModel scan;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _levelColor(visual, scan.pluralismLevel);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('media-scanner-${scan.scannerId}'),
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
                  child: Icon(Icons.newspaper_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.mediaScanEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _levelLabel(strings, scan.pluralismLevel),
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
                    strings.mediaScanOutletsLabel(scan.independentOutletsCount),
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
                'Haber Kümesi: ${scan.topicCluster}',
                style: TextStyle(
                  fontSize: 11.5,
                  color: visual.foreground,
                ),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              strings.mediaScanDiversityLabel((scan.sourceDiversityIndex * 100).toInt()),
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

  Color _levelColor(KefeVisualSystem visual, MediaPluralismLevelModel level) => switch (level) {
    MediaPluralismLevelModel.pluralisticIndependentDiverse => const Color(0xFF10B981),
    MediaPluralismLevelModel.corporateConglomerateConcentration => visual.gold,
    MediaPluralismLevelModel.stateControlledMonopolyAlert => visual.empathy,
  };

  String _levelLabel(KefeStrings strings, MediaPluralismLevelModel level) => switch (level) {
    MediaPluralismLevelModel.pluralisticIndependentDiverse => strings.mediaScanLvlPluralistic,
    MediaPluralismLevelModel.corporateConglomerateConcentration => strings.mediaScanLvlConglomerate,
    MediaPluralismLevelModel.stateControlledMonopolyAlert => strings.mediaScanLvlMonopoly,
  };
}
