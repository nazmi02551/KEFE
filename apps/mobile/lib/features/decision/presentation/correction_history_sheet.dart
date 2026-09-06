import 'package:flutter/material.dart';

import '../../../core/design/kefe_surface.dart';
import '../../../core/design/kefe_visual_system.dart';
import '../../../core/localization/internal_alpha_strings.dart';
import '../../../core/localization/kefe_strings.dart';
import '../domain/correction_history_models.dart';

class CorrectionHistorySheet extends StatelessWidget {
  const CorrectionHistorySheet({
    required this.history,
    super.key,
  });

  final CaseCorrectionHistoryModel history;

  static Future<void> show(
    BuildContext context,
    CaseCorrectionHistoryModel history,
  ) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => CorrectionHistorySheet(history: history),
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
              Icon(Icons.history_toggle_off_rounded, color: visual.rules, size: 22),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  strings.correctionSheetTitle,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w900,
                    letterSpacing: -0.2,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 18),
          if (history.corrections.isEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 24),
              child: Center(
                child: Text(
                  strings.correctionNoCorrections,
                  style: TextStyle(color: visual.mutedForeground, fontSize: 13),
                  textAlign: TextAlign.center,
                ),
              ),
            )
          else
            Flexible(
              child: SingleChildScrollView(
                child: Column(
                  children: history.corrections.map((item) {
                    final color = _severityColor(visual, item.severity);

                    return Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: KefeSurface(
                        tone: KefeSurfaceTone.raised,
                        padding: const EdgeInsets.all(14),
                        borderRadius: 16,
                        accent: color,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 6,
                                    vertical: 2,
                                  ),
                                  decoration: BoxDecoration(
                                    color: color.withValues(
                                      alpha: visual.isDark ? 0.16 : 0.08,
                                    ),
                                    borderRadius: BorderRadius.circular(6),
                                    border: Border.all(
                                      color: color.withValues(alpha: 0.3),
                                    ),
                                  ),
                                  child: Text(
                                    _typeLabel(strings, item.correctionType),
                                    style: TextStyle(
                                      fontSize: 10.5,
                                      fontWeight: FontWeight.w800,
                                      color: color,
                                    ),
                                  ),
                                ),
                                Text(
                                  '${item.timestamp.day}.${item.timestamp.month}.${item.timestamp.year}',
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w600,
                                    color: visual.mutedForeground,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text(
                              item.summary,
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w800,
                                color: visual.foreground,
                              ),
                            ),
                            const SizedBox(height: 6),
                            Text(
                              '${strings.correctionRationaleLabel} ${item.editorialRationale}',
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: visual.mutedForeground,
                                fontSize: 11.5,
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

  Color _severityColor(KefeVisualTheme visual, CorrectionSeverityModel severity) =>
      switch (severity) {
        CorrectionSeverityModel.minor => visual.mutedForeground,
        CorrectionSeverityModel.material => visual.gold,
        CorrectionSeverityModel.substantial => visual.attention,
      };

  String _typeLabel(KefeStrings strings, CorrectionTypeModel type) => switch (type) {
    CorrectionTypeModel.factualUpdate => strings.correctionTypeFactual,
    CorrectionTypeModel.clarification => strings.correctionTypeClarification,
    CorrectionTypeModel.sourceExpansion => strings.correctionTypeSource,
    CorrectionTypeModel.typoFix => strings.correctionTypeTypo,
    CorrectionTypeModel.legalStatusUpdate => strings.correctionTypeLegal,
  };
}
