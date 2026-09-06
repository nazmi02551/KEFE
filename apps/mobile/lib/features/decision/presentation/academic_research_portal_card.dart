import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/academic_research_portal_models.dart';

class AcademicResearchPortalCard extends StatelessWidget {
  const AcademicResearchPortalCard({
    required this.dataset,
    this.onTap,
    super.key,
  });

  final AcademicResearchDatasetModel dataset;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final strings = KefeStrings.of(context);
    final visual = context.kefeVisual;
    final accent = _corpusColor(visual, dataset.corpusType);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: KefeSurface(
        key: ValueKey('acad-dataset-${dataset.datasetId}'),
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
                  child: Icon(Icons.dataset_rounded, color: accent, size: 22),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      KefeEyebrow(strings.acadPortEyebrow, color: accent),
                      const SizedBox(height: 2),
                      Text(
                        _corpusLabel(strings, dataset.corpusType),
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
                    strings.acadPortPrivacyLabel(dataset.differentialPrivacyEpsilon),
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
              dataset.datasetTitle,
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
                strings.acadPortRecordsLabel(dataset.recordCount, dataset.doiIdentifier),
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

  Color _corpusColor(KefeVisualSystem visual, ResearchCorpusTypeModel corpus) => switch (corpus) {
    ResearchCorpusTypeModel.deliberativePolarizationDataset => visual.rules,
    ResearchCorpusTypeModel.ethicalTradeOffCorpus => visual.empathy,
    ResearchCorpusTypeModel.argumentGraphTopology => visual.gold,
    ResearchCorpusTypeModel.policyOutcomeBenchmark => visual.burgundy,
  };

  String _corpusLabel(KefeStrings strings, ResearchCorpusTypeModel corpus) => switch (corpus) {
    ResearchCorpusTypeModel.deliberativePolarizationDataset => strings.acadPortCorpPolar,
    ResearchCorpusTypeModel.ethicalTradeOffCorpus => strings.acadPortCorpEthics,
    ResearchCorpusTypeModel.argumentGraphTopology => strings.acadPortCorpGraph,
    ResearchCorpusTypeModel.policyOutcomeBenchmark => strings.acadPortCorpPolicy,
  };
}
