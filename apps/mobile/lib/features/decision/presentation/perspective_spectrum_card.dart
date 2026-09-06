import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/perspective_spectrum_models.dart';

class PerspectiveSpectrumCard extends StatelessWidget {
  const PerspectiveSpectrumCard({
    required this.spectrum,
    this.onTap,
    super.key,
  });

  final PerspectiveSpectrumModel spectrum;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _hueColor(visual, spectrum.primaryValueHue);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('persp-spec-${spectrum.spectrumId}'),
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
                  child: Icon(Icons.palette_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.perspSpecEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _hueLabel(strings, spectrum.primaryValueHue),
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
                    strings.perspSpecBridgeLabel((spectrum.crossValueBridgeRatio * 100).toInt()),
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
                spectrum.coreMoralIntuition,
                style: TextStyle(
                  fontSize: 11.5,
                  color: visual.foreground,
                ),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              strings.perspSpecResonanceLabel(spectrum.argumentResonanceCount),
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

  Color _hueColor(KefeVisualSystem visual, PrimaryValueHueModel hue) => switch (hue) {
    PrimaryValueHueModel.securityAndOrder => visual.rules,
    PrimaryValueHueModel.autonomyAndLiberty => visual.gold,
    PrimaryValueHueModel.equalityAndCare => visual.empathy,
    PrimaryValueHueModel.innovationAndProgress => const Color(0xFF10B981),
    PrimaryValueHueModel.traditionAndHeritage => visual.burgundy,
  };

  String _hueLabel(KefeStrings strings, PrimaryValueHueModel hue) => switch (hue) {
    PrimaryValueHueModel.securityAndOrder => strings.perspSpecValSecurity,
    PrimaryValueHueModel.autonomyAndLiberty => strings.perspSpecValAutonomy,
    PrimaryValueHueModel.equalityAndCare => strings.perspSpecValEquality,
    PrimaryValueHueModel.innovationAndProgress => strings.perspSpecValInnovation,
    PrimaryValueHueModel.traditionAndHeritage => strings.perspSpecValTradition,
  };
}
