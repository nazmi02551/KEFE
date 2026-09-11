import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../domain/consensus_divergence_models.dart';

class ConsensusDivergenceCard extends StatelessWidget {
  const ConsensusDivergenceCard({
    required this.model,
    this.onTap,
    super.key,
  });

  final ConsensusDivergenceModel model;
  final VoidCallback? onTap;

  Color _categoryColor(BuildContext context, DivergenceCategory category) {
    final visual = context.kefeVisual;
    switch (category) {
      case DivergenceCategory.broadConsensus:
        return visual.success;
      case DivergenceCategory.bipolarDivergence:
        return visual.empathy;
      case DivergenceCategory.fragmentedPlurality:
        return visual.attention;
      case DivergenceCategory.leaningMajority:
        return visual.rules;
    }
  }

  IconData _categoryIcon(DivergenceCategory category) {
    switch (category) {
      case DivergenceCategory.broadConsensus:
        return Icons.handshake_outlined;
      case DivergenceCategory.bipolarDivergence:
        return Icons.compare_arrows_outlined;
      case DivergenceCategory.fragmentedPlurality:
        return Icons.pie_chart_outline;
      case DivergenceCategory.leaningMajority:
        return Icons.trending_up;
    }
  }

  @override
  Widget build(BuildContext context) {
    final visual = context.kefeVisual;
    final lang = Localizations.localeOf(context).languageCode;
    final badgeColor = _categoryColor(context, model.classification);
    final label = lang == 'tr' ? model.labelTr : model.labelEn;
    final description = lang == 'tr' ? model.descriptionTr : model.descriptionEn;

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
                Icons.analytics_outlined,
                size: 18,
                color: visual.gold,
              ),
              const SizedBox(width: 8),
              Text(
                lang == 'tr' ? 'UZLAŞI VE AYRIŞMA ANALİZİ' : 'CONSENSUS & DIVERGENCE ANALYSIS',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.1,
                  color: visual.gold,
                ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: badgeColor.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: badgeColor.withValues(alpha: 0.4)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      _categoryIcon(model.classification),
                      size: 14,
                      color: badgeColor,
                    ),
                    const SizedBox(width: 5),
                    Text(
                      label.toUpperCase(),
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: badgeColor,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            label,
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
              color: visual.foreground,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            description,
            style: TextStyle(
              fontSize: 13,
              height: 1.45,
              color: visual.mutedForeground,
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: visual.surfaceSunken,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        lang == 'tr' ? 'ÖNCÜ PAY' : 'LEADING SHARE',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w600,
                          letterSpacing: 0.8,
                          color: visual.mutedForeground,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '%${(model.leadingShare * 100).toStringAsFixed(1)}',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w700,
                          color: visual.foreground,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: visual.surfaceSunken,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: visual.border.withValues(alpha: 0.5)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        lang == 'tr' ? 'AYRIŞMA MARJI' : 'DIVERGENCE MARGIN',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w600,
                          letterSpacing: 0.8,
                          color: visual.mutedForeground,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '%${(model.marginOfDivergence * 100).toStringAsFixed(1)}',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w700,
                          color: visual.foreground,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            lang == 'tr'
                ? 'Bu sınıflandırma matematiksel dağılıma dayanır ve normatif bir değer yargısı içermez.'
                : 'This classification is based on mathematical distribution and carries no normative judgment.',
            style: TextStyle(
              fontSize: 11,
              fontStyle: FontStyle.italic,
              color: visual.mutedForeground.withValues(alpha: 0.8),
            ),
          ),
        ],
      ),
    ),
  );
}
}
