import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../domain/normative_models.dart';

class NormativeModelsCard extends StatelessWidget {
  const NormativeModelsCard({
    required this.model,
    super.key,
  });

  final CaseNormativeModelsModel model;

  Color _philosophyColor(BuildContext context, NormativePhilosophyType type) {
    final visual = context.kefeVisual;
    switch (type) {
      case NormativePhilosophyType.utilitarianMaxWelfare:
        return visual.rules;
      case NormativePhilosophyType.deontologicalCategoricalRights:
        return visual.empathy;
      case NormativePhilosophyType.rawlsianMaximinEquity:
        return visual.gold;
      case NormativePhilosophyType.virtueEthicsCharacter:
        return visual.success;
    }
  }

  String _philosophyTitle(NormativePhilosophyType type, bool isTr) {
    switch (type) {
      case NormativePhilosophyType.utilitarianMaxWelfare:
        return isTr ? 'Faydacılık' : 'Utilitarianism';
      case NormativePhilosophyType.deontologicalCategoricalRights:
        return isTr ? 'Ödev Etiği (Haklar)' : 'Deontological Rights';
      case NormativePhilosophyType.rawlsianMaximinEquity:
        return isTr ? 'Rawlsgil Hakkaniyet' : 'Rawlsian Equity';
      case NormativePhilosophyType.virtueEthicsCharacter:
        return isTr ? 'Erdem Etiği' : 'Virtue Ethics';
    }
  }

  Widget _buildScoreBar({
    required BuildContext context,
    required String label,
    required double score,
    required Color color,
  }) {
    final visual = context.kefeVisual;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                label,
                style: TextStyle(
                  fontSize: 12,
                  color: visual.foreground,
                ),
              ),
              Text(
                '%${(score * 100).toStringAsFixed(0)}',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: color,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: score.clamp(0.0, 1.0),
              minHeight: 6,
              backgroundColor: visual.surfaceSunken,
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final isTr = Localizations.localeOf(context).languageCode == 'tr';

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: KefeSurface(
        tone: KefeSurfaceTone.raised,
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.balance_outlined,
                  size: 18,
                  color: visual.gold,
                ),
                const SizedBox(width: 8),
                Text(
                  isTr ? 'NORMATİF ETİK MODELLERİ' : 'NORMATIVE ETHICAL MODELS',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.1,
                    color: visual.gold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              isTr
                  ? 'Seçeneklerin felsefi etik geleneklerindeki karşılıkları ve değer dağılımları.'
                  : 'Philosophical ethical traditions and value distribution across options.',
              style: TextStyle(
                fontSize: 13,
                height: 1.4,
                color: visual.mutedForeground,
              ),
            ),
            const SizedBox(height: 16),
            ...model.evaluations.map((evaluation) {
              final domColor = _philosophyColor(context, evaluation.dominantPhilosophy);
              final domTitle = _philosophyTitle(evaluation.dominantPhilosophy, isTr);
              final explanation = isTr
                  ? model.philosophiesExplainedTr[evaluation.dominantPhilosophy.wireValue] ?? ''
                  : model.philosophiesExplainedEn[evaluation.dominantPhilosophy.wireValue] ?? '';

              return Container(
                margin: const EdgeInsets.only(bottom: 16),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: visual.surfaceSunken,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          evaluation.optionCode,
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w700,
                            color: visual.foreground,
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: domColor.withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: domColor.withValues(alpha: 0.4)),
                          ),
                          child: Text(
                            domTitle.toUpperCase(),
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.w700,
                              color: domColor,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    _buildScoreBar(
                      context: context,
                      label: isTr ? 'Faydacılık' : 'Utilitarianism',
                      score: evaluation.utilitarianScore,
                      color: visual.rules,
                    ),
                    _buildScoreBar(
                      context: context,
                      label: isTr ? 'Ödev Etiği (Haklar)' : 'Deontological Rights',
                      score: evaluation.deontologicalScore,
                      color: visual.empathy,
                    ),
                    _buildScoreBar(
                      context: context,
                      label: isTr ? 'Rawlsgil Hakkaniyet' : 'Rawlsian Equity',
                      score: evaluation.rawlsianScore,
                      color: visual.gold,
                    ),
                    _buildScoreBar(
                      context: context,
                      label: isTr ? 'Erdem Etiği' : 'Virtue Ethics',
                      score: evaluation.virtueScore,
                      color: visual.success,
                    ),
                    if (explanation.isNotEmpty) ...[
                      const SizedBox(height: 10),
                      Text(
                        explanation,
                        style: TextStyle(
                          fontSize: 11,
                          fontStyle: FontStyle.italic,
                          height: 1.35,
                          color: visual.mutedForeground,
                        ),
                      ),
                    ],
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}
