import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/ethical_vector_space_models.dart';

class EthicalVectorSpaceCard extends StatelessWidget {
  const EthicalVectorSpaceCard({
    required this.vector,
    this.onTap,
    super.key,
  });

  final EthicalVectorSpaceModel vector;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _attractorColor(visual, vector.dominantAttractor);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('eth-vector-${vector.caseVersionId}'),
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
                  child: Icon(Icons.hub_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.ethVecEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        strings.ethVecDominantLabel(_attractorLabel(strings, vector.dominantAttractor)),
                        style: TextStyle(
                          fontSize: 12.5,
                          fontWeight: FontWeight.w800,
                          color: visual.foreground,
                        ),
                      ),
                    ],
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
                strings.ethVecVectorLabel(
                  (vector.utilitarianWeight * 100).toInt(),
                  (vector.deontologicalWeight * 100).toInt(),
                  (vector.communitarianWeight * 100).toInt(),
                  (vector.intergenerationalWeight * 100).toInt(),
                ),
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

  Color _attractorColor(KefeVisualSystem visual, DominantMoralAttractorModel attractor) => switch (attractor) {
    DominantMoralAttractorModel.utilitarianWelfare => visual.empathy,
    DominantMoralAttractorModel.deontologicalRights => visual.rules,
    DominantMoralAttractorModel.communitarianSolidarity => visual.gold,
    DominantMoralAttractorModel.intergenerationalCare => visual.burgundy,
  };

  String _attractorLabel(KefeStrings strings, DominantMoralAttractorModel attractor) => switch (attractor) {
    DominantMoralAttractorModel.utilitarianWelfare => strings.ethVecDomUtilitarian,
    DominantMoralAttractorModel.deontologicalRights => strings.ethVecDomDeontological,
    DominantMoralAttractorModel.communitarianSolidarity => strings.ethVecDomCommunitarian,
    DominantMoralAttractorModel.intergenerationalCare => strings.ethVecDomIntergen,
  };
}
