import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/context_lens_models.dart';

class ContextLensSheet extends StatelessWidget {
  const ContextLensSheet({
    required this.lens,
    super.key,
  });

  final ContextLensModel lens;

  static Future<void> show(BuildContext context, ContextLensModel lens) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => ContextLensSheet(lens: lens),
    );
  }

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;

    return Container(
      decoration: BoxDecoration(
        color: visual.surface,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
        border: Border.all(color: visual.border.withValues(alpha: 0.6)),
      ),
      padding: EdgeInsets.only(
        top: 20,
        left: 20,
        right: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: visual.borderStrong,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Icon(Icons.auto_stories_outlined, color: visual.rules, size: 22),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  strings.lensSheetTitle,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w900,
                    letterSpacing: -0.2,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 18),
          Flexible(
            child: SingleChildScrollView(
              child: Column(
                children: lens.pillars.map((pillar) {
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: KefeSurface(
                      tone: KefeSurfaceTone.raised,
                      padding: const EdgeInsets.all(14),
                      borderRadius: 16,
                      accent: visual.rules,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(_pillarIcon(pillar.pillarType), size: 16, color: visual.rules),
                              const SizedBox(width: 6),
                              Text(
                                _pillarLabel(strings, pillar.pillarType),
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w800,
                                  color: visual.rules,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Text(
                            pillar.title,
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w800,
                              color: visual.foreground,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            pillar.content,
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              height: 1.4,
                              color: visual.foreground,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            '${strings.lensCitationLabel} ${pillar.sourceCitation}',
                            style: TextStyle(
                              fontSize: 10.5,
                              fontStyle: FontStyle.italic,
                              color: visual.mutedForeground,
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
          ),
          const SizedBox(height: 14),
          OutlinedButton(
            onPressed: () => Navigator.of(context).pop(),
            child: Text(strings.methodologyClose),
          ),
        ],
      ),
    );
  }

  IconData _pillarIcon(LensPillarTypeModel type) => switch (type) {
    LensPillarTypeModel.legalFramework => Icons.gavel_outlined,
    LensPillarTypeModel.historicalContext => Icons.history_edu_outlined,
    LensPillarTypeModel.scientificData => Icons.science_outlined,
    LensPillarTypeModel.comparativePractice => Icons.public_outlined,
  };

  String _pillarLabel(KefeStrings strings, LensPillarTypeModel type) => switch (type) {
    LensPillarTypeModel.legalFramework => strings.lensPillarLegal,
    LensPillarTypeModel.historicalContext => strings.lensPillarHistorical,
    LensPillarTypeModel.scientificData => strings.lensPillarScientific,
    LensPillarTypeModel.comparativePractice => strings.lensPillarComparative,
  };
}
