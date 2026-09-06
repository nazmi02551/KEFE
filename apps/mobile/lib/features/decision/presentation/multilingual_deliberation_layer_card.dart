import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/multilingual_deliberation_layer_models.dart';

class MultilingualDeliberationLayerCard extends StatelessWidget {
  const MultilingualDeliberationLayerCard({
    required this.translation,
    this.onTap,
    super.key,
  });

  final MultilingualTranslationModel translation;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _fidelityColor(visual, translation.fidelityTier);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('translation-${translation.translationId}'),
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
                  child: Icon(Icons.translate_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.multiLocEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _fidelityLabel(strings, translation.fidelityTier),
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
                    strings.multiLocLocalesLabel(
                      translation.sourceLocale.toUpperCase(),
                      translation.targetLocale.toUpperCase(),
                    ),
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
            Text(
              translation.translatedText,
              style: TextStyle(
                fontSize: 12.5,
                fontWeight: FontWeight.w800,
                color: visual.foreground,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: visual.surfaceSunken,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: visual.border.withValues(alpha: 0.5)),
              ),
              child: Text(
                strings.multiLocFidelityLabel((translation.semanticSimilarityScore * 100).toInt()),
                style: TextStyle(
                  fontSize: 11.5,
                  fontWeight: FontWeight.w700,
                  color: visual.gold,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _fidelityColor(KefeVisualSystem visual, TranslationFidelityTierModel tier) => switch (tier) {
    TranslationFidelityTierModel.highFidelityCertified => const Color(0xFF10B981),
    TranslationFidelityTierModel.communityVerified => visual.gold,
    TranslationFidelityTierModel.machineRawPreview => visual.rules,
  };

  String _fidelityLabel(KefeStrings strings, TranslationFidelityTierModel tier) => switch (tier) {
    TranslationFidelityTierModel.highFidelityCertified => strings.multiLocTierCertified,
    TranslationFidelityTierModel.communityVerified => strings.multiLocTierCommunity,
    TranslationFidelityTierModel.machineRawPreview => strings.multiLocTierMachine,
  };
}
